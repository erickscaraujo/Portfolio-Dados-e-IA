"""Analise financeira pessoal: fluxo de receitas/despesas, taxa de poupanca e orcamento."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CATEGORIAS_DESPESA = {
    # categoria: (valor medio mensal, desvio, proporcao fixa do valor)
    "Moradia": (2_100, 40, 0.9),
    "Alimentacao": (1_250, 260, 0.2),
    "Transporte": (520, 140, 0.3),
    "Saude": (380, 160, 0.5),
    "Lazer": (450, 220, 0.1),
    "Educacao": (600, 0, 1.0),
    "Assinaturas": (180, 20, 0.95),
}

# orcamento mensal acordado com voce mesmo
ORCAMENTO = {
    "Moradia": 2_150,
    "Alimentacao": 1_200,
    "Transporte": 550,
    "Saude": 400,
    "Lazer": 350,
    "Educacao": 620,
    "Assinaturas": 190,
}

SEED = 2024


def gerar_lancamentos(meses: int = 18) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    periodo = pd.period_range("2024-01", periods=meses, freq="M")
    linhas = []

    for i, mes in enumerate(periodo):
        salario = 8_500 * (1 + 0.003 * i) + (rng.random() < 0.15) * rng.uniform(800, 2_500)
        linhas.append(
            {"mes": str(mes), "tipo": "receita", "categoria": "Salario", "valor": round(salario, 2), "dia": 5}
        )

        for categoria, (media, desvio, fixo) in CATEGORIAS_DESPESA.items():
            n_lancamentos = 1 if fixo > 0.8 else int(rng.integers(4, 12))
            parte_fixa = media * fixo
            parte_variavel = max(0, rng.normal(media - parte_fixa + desvio * 0.3, desvio))
            valor_por_lancamento = (parte_fixa + parte_variavel) / n_lancamentos
            for _ in range(n_lancamentos):
                linhas.append(
                    {
                        "mes": str(mes),
                        "tipo": "despesa",
                        "categoria": categoria,
                        "valor": round(max(valor_por_lancamento * rng.uniform(0.7, 1.3), 8), 2),
                        "dia": int(rng.integers(1, 29)),
                    }
                )

    return pd.DataFrame(linhas)


def resumo_mensal(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(index="mes", columns="tipo", values="valor", aggfunc="sum").fillna(0)
    pivot["saldo"] = pivot["receita"] - pivot["despesa"]
    pivot["taxa_poupanca"] = pivot["saldo"] / pivot["receita"]
    return pivot


def comparar_orcamento(df: pd.DataFrame) -> pd.DataFrame:
    despesas = df[df["tipo"] == "despesa"]
    realizado = despesas.groupby("categoria")["valor"].sum() / despesas["mes"].nunique()
    tabela = pd.DataFrame({"media_mensal": realizado.round(2)})
    tabela["orcamento"] = pd.Series(ORCAMENTO)
    tabela["variacao"] = (tabela["media_mensal"] / tabela["orcamento"] - 1).round(3)
    return tabela.sort_values("variacao", ascending=False)


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    lancamentos = gerar_lancamentos()
    resumo = resumo_mensal(lancamentos)

    print("=== RESUMO MENSAL (ultimos 6 meses) ===")
    print(resumo.tail(6).round(2).to_string())

    media_poupanca = resumo["taxa_poupanca"].mean()
    melhor_mes = resumo["taxa_poupanca"].idxmax()
    print(
        f"\nTaxa de poupanca media: {media_poupanca:.1%} | melhor mes: {melhor_mes} "
        f"({resumo['taxa_poupanca'].max():.1%})"
    )

    print("\n=== ORCAMENTO X REALIZADO (media mensal por categoria) ===")
    orcado = comparar_orcamento(lancamentos)
    for categoria, linha in orcado.iterrows():
        status = "ACIMA do orcamento" if linha["variacao"] > 0.05 else "ok"
        print(
            f"- {categoria:<13} R$ {linha['media_mensal']:>9,.2f} (orcado R$ {linha['orcamento']:>9,.2f}) -> {status}"
        )

    despesas_por_categoria = (
        lancamentos[lancamentos["tipo"] == "despesa"].groupby(["mes", "categoria"])["valor"].sum().unstack().fillna(0)
    )
    fig, eixos = plt.subplots(1, 2, figsize=(14, 4.5))
    despesas_por_categoria.plot.area(ax=eixos[0], alpha=0.85, legend=False)
    eixos[0].set_title("Composicao das despesas por mes")
    eixos[0].set_ylabel("R$")
    resumo["taxa_poupanca"].plot(ax=eixos[1], marker="o", color="#15803d")
    eixos[1].axhline(0.2, ls="--", color="gray", lw=1)
    eixos[1].set_title("Taxa de poupanca (meta 20%)")
    eixos[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    plt.tight_layout()
    plt.savefig("outputs/financas_pessoais.png", dpi=120)

    with open("outputs/resumo_financeiro.md", "w", encoding="utf-8") as arq:
        arq.write("# Resumo financeiro pessoal\n\n")
        arq.write(f"- Taxa de poupanca media: **{media_poupanca:.1%}**\n")
        arq.write(f"- Saldo acumulado no periodo: R$ {resumo['saldo'].sum():,.2f}\n")
        pior = orcado.index[0]
        arq.write(f"- Categoria mais fora do orcamento: **{pior}** ({orcado.loc[pior, 'variacao']:+.0%})\n")

    print("\nArtefatos salvos em outputs/ (PNG + resumo_financeiro.md)")
