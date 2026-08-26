"""Matriz BCG da carteira: quadrantes estrategicos com bolhas de receita."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CORTE_CRESCIMENTO = 10.0  # % ao ano
CORTE_SHARE = 1.0  # participacao relativa vs maior concorrente
N_PRODUTOS = 28
SEED = 141


def gerar_carteira() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    return pd.DataFrame(
        {
            "produto": [f"Prod-{i:02d}" for i in range(1, N_PRODUTOS + 1)],
            "crescimento_yoy_pct": rng.normal(6, 14, N_PRODUTOS).round(1),
            "share_relativo": np.clip(rng.lognormal(-0.2, 0.8, N_PRODUTOS), 0.05, None).round(2),
            "receita_mi": np.clip(rng.lognormal(0.4, 0.9, N_PRODUTOS), 0.3, None).round(2),
        }
    )


def classificar(df: pd.DataFrame) -> pd.DataFrame:
    quadrante = np.select(
        [
            (df["crescimento_yoy_pct"] >= CORTE_CRESCIMENTO) & (df["share_relativo"] >= CORTE_SHARE),
            (df["crescimento_yoy_pct"] >= CORTE_CRESCIMENTO) & (df["share_relativo"] < CORTE_SHARE),
            (df["crescimento_yoy_pct"] < CORTE_CRESCIMENTO) & (df["share_relativo"] >= CORTE_SHARE),
        ],
        ["Estrela", "Interrogacao", "Vaca leiteira"],
        default="Abacaxi",
    )
    return df.assign(quadrante=quadrante)


RECOMENDACOES = {
    "Estrela": "investir para sustentar crescimento",
    "Vaca leiteira": "colher caixa e financiar as estrelas",
    "Interrogacao": "decidir: investir pesado ou descontinuar",
    "Abacaxi": "descontinuar ou reposicionar",
}


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    carteira = classificar(gerar_carteira())
    receita_total = carteira["receita_mi"].sum()

    print(f"=== CARTEIRA BCG (receita total R$ {receita_total:,.1f} mi) ===")
    resumo = (
        carteira.groupby("quadrante")
        .agg(
            produtos=("produto", "count"),
            receita_mi=("receita_mi", "sum"),
            crescimento_medio=("crescimento_yoy_pct", "mean"),
        )
        .round(1)
    )
    resumo["participacao_receita"] = (resumo["receita_mi"] / receita_total * 100).round(1)
    ordem = ["Estrela", "Vaca leiteira", "Interrogacao", "Abacaxi"]
    print(resumo.reindex(ordem).to_string())

    print("\nRecomendacoes:")
    for quadrante in ordem:
        if quadrante in resumo.index:
            print(f"- {quadrante}: {RECOMENDACOES[quadrante]}")

    abacaxis = carteira.query("quadrante == 'Abacaxi'").nlargest(3, "receita_mi")["produto"].tolist()
    estrelas_top = carteira.query("quadrante == 'Estrela'").nlargest(3, "receita_mi")["produto"].tolist()
    print(f"\nMaiores estrelas: {', '.join(estrelas_top)}")
    print(f"Abacaxis com maior receita em risco: {', '.join(abacaxis)}")

    cores = {"Estrela": "#16a34a", "Vaca leiteira": "#2563eb", "Interrogacao": "#f59e0b", "Abacaxi": "#dc2626"}

    plt.figure(figsize=(9.5, 7))
    for quadrante, grupo in carteira.groupby("quadrante"):
        plt.scatter(
            grupo["share_relativo"],
            grupo["crescimento_yoy_pct"],
            s=grupo["receita_mi"] * 260,
            alpha=0.65,
            color=cores[quadrante],
            label=quadrante,
            edgecolor="white",
        )
    plt.axvline(CORTE_SHARE, color="gray", ls="--", lw=1)
    plt.axhline(CORTE_CRESCIMENTO, color="gray", ls="--", lw=1)
    plt.xscale("log")
    plt.xlabel("Participacao relativa de mercado (log)")
    plt.ylabel("Crescimento YoY (%)")
    plt.title("Matriz BCG — tamanho da bolha = receita")
    plt.legend(title="Quadrante", loc="upper right")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig("outputs/carteira_bcg.png", dpi=120)

    print("\nMatriz salva em outputs/carteira_bcg.png")
