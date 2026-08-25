"""Carga SCD2 em tres cargas mensais + consultas point-in-time no final."""

from contextlib import closing

import scd2

CARGAS = [
    (
        "2025-01-01",
        [
            {"cliente_nk": 1, "nome": "Ana", "cidade": "Sao Paulo", "faixa_renda": "B"},
            {"cliente_nk": 2, "nome": "Bruno", "cidade": "Curitiba", "faixa_renda": "A"},
            {"cliente_nk": 3, "nome": "Carla", "cidade": "Salvador", "faixa_renda": "C"},
        ],
    ),
    (
        "2025-02-01",
        [
            # Ana subiu de faixa; Bruno e Carla sem mudanca (nao devem gerar versao nova)
            {"cliente_nk": 1, "nome": "Ana", "cidade": "Sao Paulo", "faixa_renda": "A"},
            {"cliente_nk": 2, "nome": "Bruno", "cidade": "Curitiba", "faixa_renda": "A"},
            {"cliente_nk": 3, "nome": "Carla", "cidade": "Salvador", "faixa_renda": "C"},
        ],
    ),
    (
        "2025-03-01",
        [
            {"cliente_nk": 1, "nome": "Ana", "cidade": "Rio de Janeiro", "faixa_renda": "A"},
            {"cliente_nk": 4, "nome": "Diego", "cidade": "Recife", "faixa_renda": "B"},
        ],
    ),
]


def main() -> None:
    with closing(scd2.conectar()) as con:
        print("=== CARGAS MENSAIS ===")
        for data, mudancas in CARGAS:
            resultado = scd2.aplicar_mudancas(con, mudancas, data)
            total = con.execute("SELECT COUNT(*) FROM dim_cliente").fetchone()[0]
            vigentes = con.execute("SELECT COUNT(*) FROM dim_cliente WHERE is_current = 1").fetchone()[0]
            print(
                f"- {data}: {resultado['inseridos']} novos, {resultado['atualizados']} versionados "
                f"| linhas totais {total}, vigentes {vigentes}"
            )

        print("\n=== CONSULTAS POINT-IN-TIME (cliente 1) ===")
        for data in ("2025-01-15", "2025-02-15", "2025-03-15"):
            estado = scd2.consulta_pontual(con, cliente_nk=1, data=data)
            print(f"- em {data}: {estado}")

        print("\n=== HISTORICO COMPLETO ===")
        historico = con.execute(
            """SELECT cliente_nk, nome, cidade, faixa_renda, valido_de,
                      COALESCE(valido_ate, 'atual') AS valido_ate
               FROM dim_cliente ORDER BY cliente_nk, valido_de"""
        ).fetchall()
        for linha in historico:
            print(f" - nk={linha[0]} {linha[1]:<6} {linha[2]:<14} renda {linha[3]} [{linha[4]} ate {linha[5]}]")

        integridade = con.execute(
            """SELECT cliente_nk, COUNT(*) FROM dim_cliente GROUP BY cliente_nk
               HAVING SUM(is_current) <> 1"""
        ).fetchall()
        print("\nIntegridade SCD2:", "FALHOU" if integridade else "exatamente 1 versao vigente por cliente")


if __name__ == "__main__":
    main()
