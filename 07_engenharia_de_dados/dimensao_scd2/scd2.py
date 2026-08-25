"""Dimensao SCD Tipo 2 em SQLite: historico versionado com valido_de/valido_ate."""

import sqlite3

DDL = """
CREATE TABLE IF NOT EXISTS dim_cliente (
    sk INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_nk INTEGER NOT NULL,
    nome TEXT NOT NULL,
    cidade TEXT NOT NULL,
    faixa_renda TEXT NOT NULL,
    valido_de TEXT NOT NULL,
    valido_ate TEXT,
    is_current INTEGER NOT NULL DEFAULT 1
)
"""


def aplicar_mudancas(con: sqlite3.Connection, mudancas: list[dict], data_carga: str) -> dict[str, int]:
    """Cada mudanca fecha a versao vigente e abre uma nova linha (padrao SCD2)."""
    estatisticas = {"inseridos": 0, "atualizados": 0}

    for mudanca in mudancas:
        existente = con.execute(
            "SELECT sk FROM dim_cliente WHERE cliente_nk = ? AND is_current = 1",
            (mudanca["cliente_nk"],),
        ).fetchone()

        if existente is None:
            con.execute(
                """INSERT INTO dim_cliente (cliente_nk, nome, cidade, faixa_renda, valido_de, is_current)
                   VALUES (?, ?, ?, ?, ?, 1)""",
                (mudanca["cliente_nk"], mudanca["nome"], mudanca["cidade"], mudanca["faixa_renda"], data_carga),
            )
            estatisticas["inseridos"] += 1
        else:
            # so versiona quando algum atributo monitorado realmente mudou
            atual = con.execute(
                "SELECT nome, cidade, faixa_renda FROM dim_cliente WHERE sk = ?",
                (existente[0],),
            ).fetchone()
            novo = (mudanca["nome"], mudanca["cidade"], mudanca["faixa_renda"])
            if atual == novo:
                continue

            con.execute(
                "UPDATE dim_cliente SET valido_ate = ?, is_current = 0 WHERE sk = ?",
                (data_carga, existente[0]),
            )
            con.execute(
                """INSERT INTO dim_cliente (cliente_nk, nome, cidade, faixa_renda, valido_de, is_current)
                   VALUES (?, ?, ?, ?, ?, 1)""",
                (mudanca["cliente_nk"], mudanca["nome"], mudanca["cidade"], mudanca["faixa_renda"], data_carga),
            )
            estatisticas["atualizados"] += 1

    con.commit()
    return estatisticas


def consulta_pontual(con: sqlite3.Connection, cliente_nk: int, data: str) -> tuple | None:
    """Como o cliente estava naquele dia — a razao de ser do SCD2."""
    return con.execute(
        """SELECT nome, cidade, faixa_renda FROM dim_cliente
           WHERE cliente_nk = ? AND valido_de <= ? AND (valido_ate IS NULL OR valido_ate > ?)""",
        (cliente_nk, data, data),
    ).fetchone()


def conectar(caminho: str = "outputs/dw_dimensoes.sqlite") -> sqlite3.Connection:
    con = sqlite3.connect(caminho)
    con.execute(DDL)
    con.commit()
    return con
