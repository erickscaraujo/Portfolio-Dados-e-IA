"""Transformacao: limpeza, deduplicacao e conformidade antes da carga."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

UFS_VALIDAS = {"SP", "RJ", "MG", "RS", "BA"}


def limpar_clientes(clientes: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    total_antes = len(clientes)

    clientes["nome"] = clientes["nome"].str.strip().str.title()
    clientes["email"] = clientes["email"].str.lower()
    clientes["uf"] = clientes["uf"].str.strip().str.upper()

    sem_email_valido = ~clientes["email"].str.contains(r"^[\w.+-]+@[\w-]+\.[\w.]+$", regex=True)
    fora_do_pais_sigla = ~clientes["uf"].isin(UFS_VALIDAS)
    rejeitados = clientes[sem_email_valido | fora_do_pais_sigla]
    clientes_limpos = clientes.drop(rejeitados.index).drop_duplicates(subset="id")

    logger.info(
        "clientes: %d entradas -> %d validas (%d rejeitadas)",
        total_antes,
        len(clientes_limpos),
        len(rejeitados),
    )
    return clientes_limpos.reset_index(drop=True), len(rejeitados)


def limpar_pedidos(pedidos: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    total_antes = len(pedidos)

    pedidos["data"] = pd.to_datetime(pedidos["data"], errors="coerce")
    pedidos["quantidade"] = pd.to_numeric(pedidos["quantidade"], errors="coerce")

    invalidos = pedidos["data"].isna() | (pedidos["quantidade"] <= 0) | (pedidos["valor"] <= 0)
    pedidos_limpos = pedidos[~invalidos].drop_duplicates(subset="pedido_id")

    logger.info(
        "pedidos: %d entradas -> %d validas (%d descartadas/duplicadas)",
        total_antes,
        len(pedidos_limpos),
        total_antes - len(pedidos_limpos),
    )
    return pedidos_limpos.reset_index(drop=True), int(invalidos.sum())


def construir_fato(pedidos: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    """Inner join garante integridade referencial no destino."""
    fato = pedidos.merge(clientes[["id", "uf"]], left_on="cliente_id", right_on="id", how="inner")
    fato["receita"] = fato["valor"] * fato["quantidade"]
    fato["ano_mes"] = fato["data"].dt.to_period("M").astype(str)
    logger.info("fato_vendas construida com %d registros apos o join", len(fato))
    return fato[["pedido_id", "cliente_id", "uf", "categoria", "receita", "ano_mes"]]
