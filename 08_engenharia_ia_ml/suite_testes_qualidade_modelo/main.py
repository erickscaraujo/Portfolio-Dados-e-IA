"""Suíte de portoes de qualidade para o modelo antes de qualquer deploy."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

SEED = 33
AUC_MINIMO_GLOBAL = 0.75
AUC_MINIMO_POR_REGIAO = 0.70


def gerar_base(n: int = 10_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    regiao = rng.choice(["norte", "sul", "centro"], n, p=[0.3, 0.5, 0.2])
    divida_renda = rng.beta(2, 6, n)
    renda = rng.lognormal(8.3, 0.45, n)
    atrasos = rng.poisson(0.9, n)

    logit = (
        -2.0
        + 6.2 * divida_renda
        + 0.48 * atrasos
        - 0.00038 * renda
        # sinal mais fraco no norte: simula viés de representatividade nos dados
        + np.where(regiao == "norte", rng.normal(-0.55, 0.95, n), rng.normal(0.25, 0.55, n))
    )
    inadimpliu = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)

    return pd.DataFrame(
        {
            "regiao": regiao,
            "divida_renda": divida_renda,
            "renda": renda,
            "atrasos_12m": atrasos,
            "inadimpliu": inadimpliu,
        }
    )


def treinar(base: pd.DataFrame):
    features = ["divida_renda", "renda", "atrasos_12m"]
    treino, teste = train_test_split(base, test_size=0.3, random_state=SEED)

    modelo = RandomForestClassifier(250, max_depth=9, random_state=SEED, n_jobs=-1)
    modelo.fit(treino[features], treino["inadimpliu"])
    return modelo, teste.assign(probabilidade=modelo.predict_proba(teste[features])[:, 1])


# ---------- checks (cada um devolve nome, ok, detalhe) ----------


def check_auc_global(teste: pd.DataFrame):
    auc = roc_auc_score(teste["inadimpliu"], teste["probabilidade"])
    return ("AUC global >= 0.75", auc >= AUC_MINIMO_GLOBAL, f"AUC={auc:.3f}")


def check_auc_por_regiao(teste: pd.DataFrame):
    aucs = {
        regiao: roc_auc_score(grupo["inadimpliu"], grupo["probabilidade"]) for regiao, grupo in teste.groupby("regiao")
    }
    piores = {r: round(a, 3) for r, a in aucs.items() if a < AUC_MINIMO_POR_REGIAO}
    detalhe = f"por regiao: { ({r: round(a, 3) for r, a in aucs.items()}) }"
    ok = not piores
    if not ok:
        detalhe += f" | abaixo do minimo: {piores}"
    return ("AUC por regiao >= 0.70", ok, detalhe)


def check_faixa_probabilidades(teste: pd.DataFrame):
    probs = teste["probabilidade"]
    valido = probs.between(0, 1).all() and not probs.isna().any()
    return ("Probabilidades em [0,1] sem NaN", bool(valido), f"min={probs.min():.3f} max={probs.max():.3f}")


def check_monotonicidade_divida(teste: pd.DataFrame):
    """Score medio deve crescer com o endividamento; quebra denuncia vazamento/bug."""
    faixas = pd.qcut(teste["divida_renda"], 5, duplicates="drop")
    medias = teste.groupby(faixas, observed=True)["probabilidade"].mean().to_numpy()
    monotona = bool(np.all(np.diff(medias) > -0.01))
    return ("Score monotono na divida", monotona, f"medias por quintil: {[round(float(m), 3) for m in medias]}")


def check_taxa_aprovacao_estavel(teste: pd.DataFrame, tolerancia_pp: float = 12.0):
    taxa = teste.groupby("regiao").apply(lambda g: (g["probabilidade"] < 0.40).mean(), include_groups=False)
    amplitude = float(taxa.max() - taxa.min()) * 100
    return (
        f"Aprovacao entre regioes difere < {tolerancia_pp:.0f}pp",
        amplitude <= tolerancia_pp,
        f"amplitude={amplitude:.1f}pp ({taxa.round(2).to_dict()})",
    )


CHECKS = [
    check_auc_global,
    check_auc_por_regiao,
    check_faixa_probabilidades,
    check_monotonicidade_divida,
    check_taxa_aprovacao_estavel,
]


def main() -> int:
    base = gerar_base()
    _, teste = treinar(base)

    print("=== SUITE DE QUALIDADE DO MODELO ===")
    falhas = 0
    for check in CHECKS:
        nome, ok, detalhe = check(teste)
        marca = "[OK]  " if ok else "[FALHA]"
        falhas += not ok
        print(f"{marca} {nome}\n       {detalhe}")

    veredito = "APROVADO PARA DEPLOY" if falhas == 0 else f"BLOQUEADO ({falhas} check(s) falharam)"
    print(f"\nGATE DE DEPLOY: {veredito}")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
