"""Drift multivariado: um classificador tenta separar treino de producao."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

N_AMOSTRAS = 6_000
SEED = 450


def amostra_treino(n: int, seed: int = SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    renda = rng.lognormal(8.3, 0.45, n)
    divida_renda = rng.beta(2, 6, n)
    idade_conta_dias = rng.integers(30, 3_000, n)
    return np.column_stack([renda / 10_000, divida_renda, idade_conta_dias / 1000])


def amostra_producao(n: int, magnitude: float, seed: int) -> np.ndarray:
    """Producao deriva: renda cai, endividamento sobe, contas mais novas."""
    rng = np.random.default_rng(seed)
    base = amostra_treino(n, seed + 1)
    deslocamento = np.array([[-0.35 * magnitude, 0.12 * magnitude, 0.25 * magnitude]])
    return base + deslocamento * rng.normal(1, 0.2, (n, 1))


def auc_dominio(treino: np.ndarray, producao: np.ndarray) -> float:
    """AUC do classificador treino-vs-producao em holdout; 0.5 = sem drift."""
    X = np.vstack([treino, producao])
    y = np.concatenate([np.zeros(len(treino)), np.ones(len(producao))])

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=SEED)
    detector = RandomForestClassifier(150, max_depth=8, random_state=SEED).fit(X_tr, y_tr)
    return float(roc_auc_score(y_te, detector.predict_proba(X_te)[:, 1]))


def atribuir_drift_por_feature(treino: np.ndarray, producao: np.ndarray) -> list[tuple[int, float]]:
    nomes = ["renda", "divida/renda", "idade_conta"]
    ks = [stats.ks_2samp(treino[:, i], producao[:, i]).statistic for i in range(treino.shape[1])]
    ordenado = sorted(zip(nomes, (float(k) for k in ks), strict=True), key=lambda par: -par[1])
    return ordenado


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    treino = amostra_treino(N_AMOSTRAS)

    print("=== AUC DO DETECTOR DE DOMINIO POR MAGNITUDE DE DRIFT ===")
    magnitudes = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5]
    aucs = []
    for magnitude in magnitudes:
        producao = amostra_producao(N_AMOSTRAS // 2, magnitude, seed=SEED + 50 + int(magnitude * 100))
        auc = auc_dominio(treino[: N_AMOSTRAS // 2], producao)
        aucs.append(auc)

        if magnitude == 0:
            status = "sem drift (controle)"
        elif auc > 0.9:
            status = "drift forte"
        elif auc > 0.7:
            status = "drift moderado"
        else:
            status = "drift leve"
        print(f"- shift {magnitude:>4}: AUC dominio = {auc:.3f} -> {status}")

    # atribuicao no pior caso
    producao_critica = amostra_producao(N_AMOSTRAS // 2, magnitude=1.5, seed=SEED + 250)
    ranking_ks = atribuir_drift_por_feature(treino[: N_AMOSTRAS // 2], producao_critica)
    print("\n=== CULPADOS (KS por feature, drift forte) ===")
    for nome, estatistica in ranking_ks:
        print(f"- {nome:<14} KS={estatistica:.3f}")

    plt.figure(figsize=(8, 4.4))
    plt.plot(magnitudes, aucs, marker="o", color="#b91c1c", lw=2)
    plt.axhline(0.5, ls="--", color="gray", label="sem drift")
    plt.axhline(0.7, ls=":", color="#f59e0b", label="limiar alerta")
    plt.xlabel("Magnitude do deslocamento na producao")
    plt.ylabel("AUC do classificador de dominio")
    plt.title("Drift multivariado detectado como tarefa de classificacao")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/drift_multivariado.png", dpi=120)

    print("\nCurva salva em outputs/drift_multivariado.png")
