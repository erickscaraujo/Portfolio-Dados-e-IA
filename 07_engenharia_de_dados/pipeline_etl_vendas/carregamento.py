"""Carga dos dados tratados em um mini data warehouse SQLite."""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DDL = [
    """
    CREATE TABLE IF NOT EXISTS dim_cliente (
        cliente_id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        uf TEXT NOT NULL,
        idade INTEGER
    )""",
    """
    CREATE TABLE IF NOT EXISTS fato_pedido (
        pedido_id TEXT PRIMARY KEY,
        cliente_id INTEGER REFERENCES dim_cliente(cliente_id),
        uf TEXT,
        categoria TEXT,
        receita REAL,
        ano_mes TEXT
    )""",
]


def carregar(
    clientes: pd.DataFrame, fato: pd.DataFrame, caminho_dw: str = "outputs/dw_vendas.sqlite"
) -> dict[str, int]:
    Path(caminho_dw).parent.mkdir(exist_ok=True)

    with sqlite3.connect(caminho_dw) as con:
        for ddl in DDL:
            con.execute(ddl)
        # carga full refresh simples: limpa e reinsere
        con.execute("DELETE FROM fato_pedido")
        con.execute("DELETE FROM dim_cliente")

        con.executemany(
            "INSERT INTO dim_cliente VALUES (?, ?, ?, ?, ?)",
            clientes.itertuples(index=False, name=None),
        )
        con.executemany(
            "INSERT INTO fato_pedido VALUES (?, ?, ?, ?, ?, ?)",
            fato.itertuples(index=False, name=None),
        )

        qtd_clientes = con.execute("SELECT COUNT(*) FROM dim_cliente").fetchone()[0]
        qtd_fatos = con.execute("SELECT COUNT(*) FROM fato_pedido").fetchone()[0]

    logger.info("carga concluida: %d clientes e %d fatos em %s", qtd_clientes, qtd_fatos, caminho_dw)
    return {"dim_cliente": qtd_clientes, "fato_pedido": qtd_fatos}


def consulta_resumo(caminho_dw: str = "outputs/dw_vendas.sqlite") -> pd.DataFrame:
    with sqlite3.connect(caminho_dw) as con:
        return pd.read_sql_query(
            """
            SELECT ano_mes, SUM(receita) AS receita_total, COUNT(*) AS pedidos
            FROM fato_pedido GROUP BY ano_mes ORDER BY ano_mes DESC LIMIT 5
            """,
            con,
        )
