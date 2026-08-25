"""NL2SQL sem LLM: parser de perguntas -> SQL -> resultado no SQLite."""

import sqlite3
from pathlib import Path

import consultas as cq
import numpy as np
import pandas as pd

BANCO = "outputs/vendas.db"
PERGUNTAS_DEMO = [
    "faturamento total por categoria",
    "media dos pedidos de eletronicos",
    "quantidade de pedidos por cidade em 2024",
    "total de vendas em curitiba por mes",
    "quem venceu a copa de 1998",  # fora do escopo de proposito
]


def preparar_banco(seed: int = 6) -> None:
    rng = np.random.default_rng(seed)
    n_clientes, n_pedidos = 200, 3_000

    clientes = pd.DataFrame(
        {
            "cliente_id": range(1, n_clientes + 1),
            "cidade": rng.choice(["Sao Paulo", "Rio de Janeiro", "Curitiba", "Recife"], n_clientes),
        }
    )
    pedidos = pd.DataFrame(
        {
            "pedido_id": [f"P{i}" for i in range(1, n_pedidos + 1)],
            "cliente_id": rng.integers(1, n_clientes + 1, n_pedidos),
            "categoria": rng.choice(list(cq.CATEGORIAS), n_pedidos),
            "valor": np.round(rng.uniform(20, 1_800, n_pedidos), 2),
            "data": (pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 700, n_pedidos), unit="D")).astype(
                str
            ),
        }
    )

    Path(BANCO).parent.mkdir(exist_ok=True)
    with sqlite3.connect(BANCO) as con:
        clientes.to_sql("clientes", con, if_exists="replace", index=False)
        pedidos.to_sql("pedidos", con, if_exists="replace", index=False)


def main() -> None:
    preparar_banco()

    print("Perguntas que entendo:\n" + cq.capacidades() + "\n")
    with sqlite3.connect(BANCO) as con:
        for pergunta in PERGUNTAS_DEMO:
            sql = cq.traduzir(pergunta)
            print(f"\n[pergunta] {pergunta}")
            if sql is None:
                print("  Nao entendi. Tente reformular usando o vocabulario acima.")
                continue

            print(f"  [sql] {' '.join(sql.split())[:110]}...")
            resultado = pd.read_sql_query(sql, con)
            print(resultado.head(5).to_string(index=False, float_format=lambda x: f"{x:,.2f}"))


if __name__ == "__main__":
    main()
