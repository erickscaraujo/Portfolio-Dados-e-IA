"""Benchmark antes/depois de indices: full scan vs busca indexada com EXPLAIN."""

import sqlite3
import time
from pathlib import Path

BANCO = "outputs/benchmark_indices.sqlite"
N_LINHAS = 500_000

CONSULTAS = {
    "filtro por cliente": "SELECT COUNT(*) FROM pedidos WHERE cliente_id = 1234",
    "faixa de data": "SELECT SUM(valor) FROM pedidos WHERE data BETWEEN '2025-03-01' AND '2025-03-03'",
    "status + valor": "SELECT AVG(valor) FROM pedidos WHERE status = 'pago' AND valor > 500",
}


def popular(con: sqlite3.Connection) -> None:
    con.execute("CREATE TABLE pedidos (id INTEGER, cliente_id INTEGER, data TEXT, status TEXT, valor REAL)")

    def gerar_linhas():
        for i in range(N_LINHAS):
            dia = (i * 13) % 365
            yield (
                i,
                (i * 7919) % 50_000,  # primo espalha bem os clientes
                f"2025-{1 + dia // 30:02d}-{1 + dia % 30:02d}",
                "pago" if i % 4 else "pendente",
                round(10 + (i * 37) % 2000 + i % 100 / 100, 2),
            )

    # executemany consome o gerador sem carregar tudo em memoria
    con.executemany("INSERT INTO pedidos VALUES (?, ?, ?, ?, ?)", gerar_linhas())
    con.commit()


def medir(con: sqlite3.Connection, sql: str, repeticoes: int = 3) -> float:
    melhor = min(_cronometrar(con, sql) for _ in range(repeticoes))
    return melhor


def _cronometrar(con: sqlite3.Connection, sql: str) -> float:
    inicio = time.perf_counter()
    con.execute(sql).fetchone()
    return time.perf_counter() - inicio


def plano(con: sqlite3.Connection, sql: str) -> str:
    linhas = con.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    return "; ".join(linha[3] for linha in linhas)


def main() -> None:
    Path(BANCO).parent.mkdir(exist_ok=True)
    Path(BANCO).unlink(missing_ok=True)

    with sqlite3.connect(BANCO) as con:
        print(f"Carga de {N_LINHAS:,} linhas...")
        inicio_carga = time.perf_counter()
        popular(con)
        print(f"carga concluida em {time.perf_counter() - inicio_carga:.1f}s\n")

        print("=== SEM INDICES ===")
        tempos_sem = {}
        for nome, sql in CONSULTAS.items():
            tempos_sem[nome] = medir(con, sql)
            print(f"- {nome:<20} {tempos_sem[nome] * 1000:>8.2f} ms | {plano(con, sql)}")

        print("\nCriando indices...")
        inicio_indices = time.perf_counter()
        con.executescript("""
            CREATE INDEX idx_pedidos_cliente ON pedidos(cliente_id);
            CREATE INDEX idx_pedidos_data ON pedidos(data);
            CREATE INDEX idx_pedidos_status_valor ON pedidos(status, valor);
        """)
        custo_indices = time.perf_counter() - inicio_indices
        print(f"indices criados em {custo_indices:.2f}s\n")

        print("=== COM INDICES ===")
        ganhos = []
        for nome, sql in CONSULTAS.items():
            tempo_com = medir(con, sql)
            speedup = tempos_sem[nome] / max(tempo_com, 1e-6)
            ganhos.append(speedup)
            print(f"- {nome:<20} {tempo_com * 1000:>8.2f} ms | {speedup:>6.1f}x mais rapido")
            print(f"{'':<23}{plano(con, sql)}")

        print(
            f"\nSpeedup medio: {sum(ganhos) / len(ganhos):.1f}x | custo pago na escrita: {custo_indices:.2f}s (uma vez)"
        )


if __name__ == "__main__":
    main()
