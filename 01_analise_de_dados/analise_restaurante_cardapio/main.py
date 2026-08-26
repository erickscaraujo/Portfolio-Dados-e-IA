"""Engenharia de cardapio: popularidade x rentabilidade de cada item."""

import matplotlib

matplotlib.use("Agg")

# (nome, categoria, vendas no mes, preco, custo do insumo)
import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ITENS = [
    ("Picanha na chapa", "prato", 210, 78.0, 34.0),
    ("Risoto de funghi", "prato", 95, 62.0, 21.0),
    ("Lasanha da casa", "prato", 240, 48.0, 17.5),
    ("Peixe do dia", "prato", 60, 89.0, 52.0),
    ("Hamburguer artesanal", "prato", 320, 44.0, 18.0),
    ("Burrata com tomate", "entrada", 150, 38.0, 14.0),
    ("Bruschetta classica", "entrada", 260, 26.0, 6.5),
    ("Carpaccio", "entrada", 55, 42.0, 24.0),
    ("Petit gateau", "sobremesa", 280, 28.0, 7.0),
    ("Cheesecake", "sobremesa", 90, 30.0, 9.5),
    ("Mousse de maracuja", "sobremesa", 200, 22.0, 4.8),
    ("Chopp artesanal 500ml", "bebida", 520, 24.0, 6.2),
    ("Vinho da casa (taça)", "bebida", 310, 26.0, 7.8),
    ("Suco natural", "bebida", 180, 16.0, 3.4),
]
SEED = 300


def montar_cardapio() -> pd.DataFrame:
    df = pd.DataFrame(ITENS, columns=["item", "categoria", "vendas", "preco", "custo"])
    df["margem_contribuicao"] = df["preco"] - df["custo"]
    df["margem_pct"] = (df["margem_contribuicao"] / df["preco"] * 100).round(1)
    df["receita"] = df["preco"] * df["vendas"]

    # cortes classicos de Kasavana-Smith: popularidade vs margem de contribuicao em R$
    media_vendas = df["vendas"].mean()
    media_margem_rs = df["margem_contribuicao"].mean()

    condicoes = [
        (df["vendas"] >= media_vendas) & (df["margem_contribuicao"] >= media_margem_rs),
        (df["vendas"] >= media_vendas) & (df["margem_contribuicao"] < media_margem_rs),
        (df["vendas"] < media_vendas) & (df["margem_contribuicao"] >= media_margem_rs),
    ]
    escolhas = ["Estrela", "Cavalo de batalha", "Puzzle"]
    df["classe"] = np.select(condicoes, escolhas, default="Cao")
    return df


ACOES = {
    "Estrela": "manter posicao de destaque no menu",
    "Cavalo de batalha": "reprecificar ou baratear o insumo",
    "Puzzle": "promover: sugestao do garcom e foto no menu",
    "Cao": "testar remocao ou reformular receita",
}


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    cardapio = montar_cardapio()

    print("=== CLASSIFICACAO DO CARDÁPIO ===")
    colunas = ["item", "categoria", "vendas", "preco", "margem_pct", "classe"]
    print(cardapio[colunas].sort_values(["classe", "vendas"], ascending=[True, False]).to_string(index=False))

    resumo = (
        cardapio.groupby("classe")
        .agg(
            itens=("item", "count"),
            vendas=("vendas", "sum"),
            receita=("receita", "sum"),
        )
        .round(1)
    )
    resumo["mix_receita_pct"] = (resumo["receita"] / resumo["receita"].sum() * 100).round(1)
    ordem = ["Estrela", "Cavalo de batalha", "Puzzle", "Cao"]
    print("\n=== MIX POR QUADRANTE ===")
    print(resumo.reindex(ordem).to_string())

    print("\nAcoes sugeridas:")
    for quadrante in ordem:
        itens_quadrante = cardapio.loc[cardapio["classe"] == quadrante, "item"].tolist()
        if itens_quadrante:
            print(f"- {quadrante} ({', '.join(itens_quadrante)}): {ACOES[quadrante]}")

    cores = {"Estrela": "#16a34a", "Cavalo de batalha": "#2563eb", "Puzzle": "#f59e0b", "Cao": "#dc2626"}
    plt.figure(figsize=(10, 6.5))
    for classe, grupo in cardapio.groupby("classe"):
        plt.scatter(
            grupo["vendas"],
            grupo["margem_pct"],
            s=grupo["receita"] / 40,
            alpha=0.7,
            color=cores[classe],
            label=classe,
            edgecolor="white",
        )
    plt.axvline(cardapio["vendas"].mean(), ls="--", color="gray", lw=1)
    plt.axhline(cardapio["margem_pct"].mean(), ls="--", color="gray", lw=1)
    for _, linha in cardapio.iterrows():
        plt.annotate(
            linha["item"], (linha["vendas"], linha["margem_pct"]), fontsize=7, xytext=(3, 3), textcoords="offset points"
        )
    plt.xlabel("Vendas no mes")
    plt.ylabel("Margem de contribuicao (%)")
    plt.title("Engenharia de cardapio — bolha = receita")
    plt.legend(title="Classe")
    plt.tight_layout()
    plt.savefig("outputs/cardapio_engenharia.png", dpi=120)

    print("\nMatriz salva em outputs/cardapio_engenharia.png")
