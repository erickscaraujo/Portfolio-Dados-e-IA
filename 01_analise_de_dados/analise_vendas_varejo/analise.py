"""Transformacoes e agregacoes sobre a base de vendas."""

import pandas as pd


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza tipos e cria colunas derivadas usadas em toda a analise."""
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])
    df["ano_mes"] = df["data"].dt.to_period("M").astype(str)
    df["receita"] = df["quantidade"] * df["preco_unitario"]
    df["custo_total"] = df["quantidade"] * df["custo_unitario"]
    df["margem_valor"] = df["receita"] - df["custo_total"]
    return df


def resumo_executivo(df: pd.DataFrame) -> dict:
    total_receita = df["receita"].sum()
    pedidos = df["id_pedido"].nunique()

    meses = sorted(df["ano_mes"].unique())
    receita_mes = df.groupby("ano_mes")["receita"].sum()
    trimestre_atual = receita_mes[meses[-3:]].sum()
    trimestre_anterior = receita_mes[meses[-6:-3]].sum()
    crescimento_tri = trimestre_atual / trimestre_anterior - 1

    return {
        "faturamento_total": total_receita,
        "pedidos": pedidos,
        "ticket_medio": total_receita / pedidos,
        "margem_pct": df["margem_valor"].sum() / total_receita,
        "crescimento_trimestral": crescimento_tri,
    }


def faturamento_mensal(df: pd.DataFrame) -> pd.DataFrame:
    mensal = df.groupby("ano_mes").agg(receita=("receita", "sum"), pedidos=("id_pedido", "nunique"))
    mensal["crescimento_moM"] = mensal["receita"].pct_change()
    return mensal


def ranking_categoria(df: pd.DataFrame) -> pd.DataFrame:
    rank = df.groupby("categoria").agg(
        receita=("receita", "sum"),
        margem_pct=("margem_valor", lambda s: s.sum() / df.loc[s.index, "receita"].sum()),
    )
    return rank.sort_values("receita", ascending=False)


def desempenho_lojas(df: pd.DataFrame) -> pd.DataFrame:
    lojas = df.groupby("loja").agg(
        receita=("receita", "sum"),
        pedidos=("id_pedido", "nunique"),
        ticket_medio=("receita", lambda s: s.sum() / df.loc[s.index, "id_pedido"].nunique()),
    )
    return lojas.sort_values("receita", ascending=False)


def top_produtos(df: pd.DataFrame, n: int = 10) -> pd.Series:
    return df.groupby("produto")["receita"].sum().nlargest(n)
