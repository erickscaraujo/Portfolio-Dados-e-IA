"""Deploy canary: desafiador recebe 10% do trafego e precisa provar valor antes da promocao."""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 50
FRACAO_CANARY = 0.10
TAMANHO_LOTE = 2_000
MIN_AMOSTRA_DESAFIADOR = 400
MARGEM_AUC = 0.01
MAX_LOTES = 8


def gerar_base(n: int = 20_000, seed: int = SEED) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 5))
    logit = 1.8 * X[:, 0] - 1.2 * X[:, 1] + 0.9 * X[:, 4] + rng.normal(0, 1.1, n)
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    return X, y


def treinar_candidatos(seed: int = SEED) -> tuple[dict, dict]:
    X, y = gerar_base(seed=seed)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=seed)

    campeao = {
        "nome": "champion-logreg-v3",
        "modelo": make_pipeline(StandardScaler(), LogisticRegression(max_iter=800)),
    }
    desafiador = {
        "nome": "challenger-rf-v1",
        "modelo": RandomForestClassifier(180, max_depth=7, random_state=seed),
    }
    for candidato in (campeao, desafiador):
        candidato["modelo"].fit(X_tr, y_tr)

    # o desafiador e de fato melhor no mundo real (diferenca plantada nos dados novos)
    return campeao, desafiar_com_dados_novos(campeao, desafiador, seed + 99)


def desafiar_com_dados_novos(campeao: dict, desafiador: dict, seed_mundo: int) -> dict:
    """Avaliacao honesta em dados que nenhum dos dois viu."""
    X, y = gerar_base(n=10_000, seed=seed_mundo)
    auc_campeao = roc_auc_score(y, campeao["modelo"].predict_proba(X)[:, 1])
    auc_desafiador = roc_auc_score(y, desafiador["modelo"].predict_proba(X)[:, 1])
    desafiador["auc_verdadeiro"] = round(auc_desafiador, 4)
    campeao["auc_verdadeiro"] = round(auc_campeao, 4)
    return desafiador


def simular_trafego(campeao: dict, desafiador: dict) -> str:
    rng = np.random.default_rng(SEED + 1)
    X, y = gerar_base(n=TAMANHO_LOTE * MAX_LOTES, seed=SEED + 77)

    rotulos_campeao: list[int] = []
    rotulos_desafiador: list[int] = []
    probas_campeao: list[float] = []
    probas_desafiador: list[float] = []

    for lote in range(MAX_LOTES):
        fatia = slice(lote * TAMANHO_LOTE, (lote + 1) * TAMANHO_LOTE)
        X_lote, y_lote = X[fatia], y[fatia]

        vai_para_canary = rng.random(TAMANHO_LOTE) < FRACAO_CANARY
        rotulos_campeao.extend(y_lote[~vai_para_canary].tolist())
        rotulos_desafiador.extend(y_lote[vai_para_canary].tolist())
        probas_campeao.extend(campeao["modelo"].predict_proba(X_lote[~vai_para_canary])[:, 1])
        probas_desafiador.extend(desafiador["modelo"].predict_proba(X_lote[vai_para_canary])[:, 1])

        if len(rotulos_desafiador) >= MIN_AMOSTRA_DESAFIADOR:
            auc_canary = roc_auc_score(rotulos_desafiador, probas_desafiador)
            auc_controle = roc_auc_score(rotulos_campeao, probas_campeao)
            print(
                f"lote {lote + 1}: canary n={len(rotulos_desafiador)} "
                f"AUC {auc_canary:.4f} vs controle {auc_controle:.4f}"
            )

            if auc_canary > auc_controle + MARGEM_AUC:
                decisao = "PROMOVER"
                break
    else:
        decisao = "MANTER CHAMPION"

    print(
        f"\nVerdade de mercado -> campeao AUC {campeao['auc_verdadeiro']} | "
        f"desafiador AUC {desafiador['auc_verdadeiro']}"
    )
    return f"DECISAO FINAL: {decisao} ({desafiador['nome']})"


if __name__ == "__main__":
    print("Treinando champion e challenger...")
    campeao, desafiador = treinar_candidatos()
    print(f"- {campeao['nome']} | AUC verdadeiro {campeao['auc_verdadeiro']}")
    print(f"- {desafiador['nome']} | AUC verdadeiro {desafiador['auc_verdadeiro']}\n")

    print("=== CANARY EM PRODUCAO (10% do trafego para o desafiador) ===")
    print(simular_trafego(campeao, desafiador))
