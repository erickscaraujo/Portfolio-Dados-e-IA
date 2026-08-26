"""Importancia de features: nativa x permutacao x drop-column no mesmo modelo."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

SEED = 370
FEATURES = [
    "renda",
    "divida_renda",
    "atrasos_12m",
    "tempo_casa",
    "score_interno",
    "score_duplicado",
]  # duplicado = score com ruido (correlacao ~0.95)


def gerar_base(n: int = 10_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    renda = rng.lognormal(8.3, 0.45, n)
    divida_renda = rng.beta(2, 6, n)
    atrasos_12m = rng.poisson(0.8, n)
    tempo_casa = rng.integers(1, 120, n)
    score_interno = (500 + 0.00002 * renda - 300 * divida_renda + rng.normal(0, 60, n)).round()

    logit = (
        -1.8
        + 0.00022 * renda
        + 4.6 * divida_renda
        + 0.38 * atrasos_12m
        - 0.004 * (score_interno - 500)
        - 0.004 * tempo_casa * 0.1
        + rng.normal(0, 0.9, n)
    )
    return pd.DataFrame(
        {
            "renda": renda.round(2),
            "divida_renda": divida_renda,
            "atrasos_12m": atrasos_12m,
            "tempo_casa": tempo_casa,
            "score_interno": score_interno.astype(int),
            "score_duplicado": (score_interno + rng.normal(0, 25, n)).astype(int),
            "inadimpliu": (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int),
        }
    )


def drop_column_auc(X_tr, y_tr, X_te, y_te, coluna_removida: str | None) -> float:
    colunas = [c for c in X_tr.columns if c != coluna_removida]
    modelo = GradientBoostingClassifier(random_state=SEED).fit(X_tr[colunas], y_tr)
    return float(roc_auc_score(y_te, modelo.predict_proba(X_te[colunas])[:, 1]))


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_base()
    alvo = base.pop("inadimpliu")
    X_tr, X_te, y_tr, y_te = train_test_split(base, alvo, test_size=0.3, random_state=SEED)

    modelo = GradientBoostingClassifier(random_state=SEED).fit(X_tr, y_tr)

    nativa = pd.Series(modelo.feature_importances_, index=base.columns, name="nativa")
    permutada = permutation_importance(modelo, X_te, y_te, random_state=SEED, n_repeats=8)
    permutacao = pd.Series(permutada.importances_mean, index=base.columns, name="permutacao")

    auc_referencia = drop_column_auc(X_tr, y_tr, X_te, y_te, None)
    queda_drop = {coluna: auc_referencia - drop_column_auc(X_tr, y_tr, X_te, y_te, coluna) for coluna in base.columns}
    drop_column = pd.Series(queda_drop, name="drop_column")

    comparativo = pd.concat([nativa, permutacao, drop_column], axis=1).round(4)

    print("=== RANKING POR METODO ===")
    for metodo in comparativo.columns:
        ranking = comparativo[metodo].sort_values(ascending=False)
        print(f"\n[{metodo}]")
        print(ranking.to_string(float_format=lambda x: f"{x:.4f}"))

    divergencia_score = comparativo.loc["score_duplicado"]
    print("\n=== LEITURA SOBRE A FEATURE DUPLICADA ===")
    print(
        f"score_duplicado -> nativa {divergencia_score['nativa']:.3f} | "
        f"permutacao {divergencia_score['permutacao']:.4f} | "
        f"drop_column {divergencia_score['drop_column']:+.4f}"
    )
    print("A importancia nativa divide o credito entre as duas versoes do score;")
    print("drop-column quase nao cai (a outra copia cobre o trabalho);")
    print("permutacao tambem se confunde. Conclusao: remover redundantes ANTES de interpretar.")

    plot_df = comparativo.div(comparativo.abs().max())
    eixo = plot_df.sort_values("nativa").plot.barh(figsize=(9.5, 5), width=0.75)
    eixo.set_title("Importancia normalizada por metodo")
    eixo.set_xlabel("importancia relativa")
    plt.tight_layout()
    plt.savefig("outputs/importancia_metodos.png", dpi=120)

    print("\nGrafico salvo em outputs/importancia_metodos.png")
