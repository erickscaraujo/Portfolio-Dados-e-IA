"""Analise de vendas do varejo: gera a base, calcula indicadores e publica o relatorio."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from analise import (
    desempenho_lojas,
    faturamento_mensal,
    preparar,
    ranking_categoria,
    resumo_executivo,
    top_produtos,
)
from dados import gerar_vendas

SAIDA = "outputs"


def grafico_faturamento_mensal(mensal: pd.DataFrame) -> None:
    ax = mensal["receita"].plot(figsize=(10, 4), marker="o", title="Faturamento mensal")
    ax.set_ylabel("Receita (R$)")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{SAIDA}/faturamento_mensal.png", dpi=120)
    plt.close()


def grafico_categorias(rank: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    rank["receita"].sort_values().plot.barh(ax=ax, color="#2a7f62")
    ax.set_title("Receita por categoria")
    ax.set_xlabel("R$")
    plt.tight_layout()
    plt.savefig(f"{SAIDA}/receita_categoria.png", dpi=120)
    plt.close()


def grafico_lojas(lojas: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(lojas["pedidos"], lojas["ticket_medio"], s=lojas["receita"] / 3000, color="#b5451b")
    for loja, linha in lojas.iterrows():
        ax.annotate(loja, (linha["pedidos"], linha["ticket_medio"]), fontsize=9)
    ax.set_title("Lojas: volume x ticket medio (bolha = receita)")
    ax.set_xlabel("Pedidos")
    ax.set_ylabel("Ticket medio (R$)")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{SAIDA}/lojas.png", dpi=120)
    plt.close()


def salvar_resumo(resumo: dict, melhor_loja: str, produto_top: str) -> None:
    with open(f"{SAIDA}/resumo.md", "w", encoding="utf-8") as arq:
        arq.write("# Resumo executivo - vendas\n\n")
        arq.write(f"- Faturamento total: R$ {resumo['faturamento_total']:,.2f}\n")
        arq.write(f"- Pedidos unicos: {resumo['pedidos']:,}\n")
        arq.write(f"- Ticket medio: R$ {resumo['ticket_medio']:,.2f}\n")
        arq.write(f"- Margem: {resumo['margem_pct']:.1%}\n")
        arq.write(f"- Crescimento ultimo trimestre: {resumo['crescimento_trimestral']:+.1%}\n")
        arq.write(f"- Loja lider: {melhor_loja} | Produto campeao: {produto_top}\n")


if __name__ == "__main__":
    import pathlib

    pathlib.Path(SAIDA).mkdir(exist_ok=True)

    base = preparar(gerar_vendas())

    resumo = resumo_executivo(base)
    print("=== RESUMO EXECUTIVO ===")
    print(f"Faturamento total : R$ {resumo['faturamento_total']:>14,.2f}")
    print(f"Pedidos           : {resumo['pedidos']:>14,}")
    print(f"Ticket medio      : R$ {resumo['ticket_medio']:>14,.2f}")
    print(f"Margem            : {resumo['margem_pct']:>14.1%}")
    print(f"Cresc. trimestral : {resumo['crescimento_trimestral']:>14.1%}")

    mensal = faturamento_mensal(base)
    print("\n=== FATURAMENTO MENSAL (ultimos 6 meses) ===")
    print(mensal.tail(6).to_string(float_format=lambda x: f"{x:,.2f}"))

    rank = ranking_categoria(base)
    print("\n=== CATEGORIAS ===")
    print(rank.to_string(float_format=lambda x: f"{x:,.2f}"))

    lojas = desempenho_lojas(base)
    print("\n=== LOJAS ===")
    print(lojas.to_string(float_format=lambda x: f"{x:,.2f}"))

    produtos = top_produtos(base)
    print("\n=== TOP 5 PRODUTOS ===")
    print(produtos.head().to_string(float_format=lambda x: f"{x:,.2f}"))

    grafico_faturamento_mensal(mensal)
    grafico_categorias(rank)
    grafico_lojas(lojas)
    salvar_resumo(resumo, lojas.index[0], produtos.index[0])
    print("\nRelatorios salvos em outputs/ (resumo.md + 3 graficos PNG)")
