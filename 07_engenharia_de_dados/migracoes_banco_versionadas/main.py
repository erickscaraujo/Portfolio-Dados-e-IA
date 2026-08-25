"""Runner de migracoes: aplica versoes pendentes, registra e permite rollback."""

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

BANCO = "outputs/app_migracoes.sqlite"

MIGRACOES = [
    {
        "versao": 1,
        "descricao": "cria tabela clientes",
        "up": """
            CREATE TABLE clientes (
                cliente_id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT UNIQUE
            )""",
        "down": "DROP TABLE clientes",
    },
    {
        "versao": 2,
        "descricao": "cria tabela pedidos com FK",
        "up": """
            CREATE TABLE pedidos (
                pedido_id INTEGER PRIMARY KEY,
                cliente_id INTEGER REFERENCES clientes(cliente_id),
                valor REAL NOT NULL CHECK (valor >= 0),
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
        "down": "DROP TABLE pedidos",
    },
    {
        "versao": 3,
        "descricao": "indice para consultas por cliente + coluna canal",
        "up": """
            ALTER TABLE pedidos ADD COLUMN canal TEXT DEFAULT 'site';
            CREATE INDEX idx_pedidos_cliente ON pedidos(cliente_id);
        """,
        # down parcial: SQLite antigo nao tem DROP COLUMN; em producao recriaria-se a tabela
        "down": """
            DROP INDEX IF EXISTS idx_pedidos_cliente;
            UPDATE pedidos SET canal = canal WHERE 0;
            SELECT 1;
        """,
    },
]


def inicializar(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
               versao INTEGER PRIMARY KEY,
               descricao TEXT,
               aplicada_em TEXT)"""
    )
    con.commit()


def versao_aplicadas(con: sqlite3.Connection) -> set[int]:
    return {linha[0] for linha in con.execute("SELECT versao FROM schema_migrations")}


def _rodar_statements(con: sqlite3.Connection, sql_multiplo: str) -> None:
    # split por ; cobre nossos scripts simples de DDL/DML
    for statement in filter(None, (s.strip() for s in sql_multiplo.split(";"))):
        con.execute(statement)


def aplicar_pendentes(con: sqlite3.Connection) -> list[int]:
    aplicadas = versao_aplicadas(con)
    executadas = []
    for migracao in sorted(MIGRACOES, key=lambda m: m["versao"]):
        if migracao["versao"] in aplicadas:
            continue

        try:
            # cada migracao roda atomica: ou tudo, ou nada fica registrado
            con.execute("BEGIN")
            _rodar_statements(con, migracao["up"])
            con.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?)",
                (migracao["versao"], migracao["descricao"], datetime.now().isoformat(timespec="seconds")),
            )
            con.commit()
        except sqlite3.Error:
            con.rollback()
            raise

        executadas.append(migracao["versao"])
        print(f"  + v{migracao['versao']} aplicada: {migracao['descricao']}")
    return executadas


def rollback_ultimo(con: sqlite3.Connection) -> None:
    aplicadas = versao_aplicadas(con)
    if not aplicadas:
        print("  nada para desfazer")
        return

    ultima = max(aplicadas)
    migracao = next(m for m in MIGRACOES if m["versao"] == ultima)
    try:
        con.execute("BEGIN")
        _rodar_statements(con, migracao["down"])
        con.execute("DELETE FROM schema_migrations WHERE versao = ?", (ultima,))
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise
    print(f"  - v{ultima} desfeita: {migracao['descricao']}")


if __name__ == "__main__":
    Path(BANCO).parent.mkdir(exist_ok=True)
    with closing(sqlite3.connect(BANCO)) as con:
        inicializar(con)

        print("=== EXECUCAO 1 ===")
        aplicar_pendentes(con)

        print("\n=== EXECUCAO 2 (deve ser no-op) ===")
        if not aplicar_pendentes(con):
            print("  nenhuma pendencia: runner e idempotente")

        print("\n=== ROLLBACK DA ULTIMA ===")
        rollback_ultimo(con)

        estado = con.execute("""SELECT p.name FROM sqlite_master p WHERE p.type='table' ORDER BY p.name""").fetchall()
        esperado = {"clientes", "pedidos", "schema_migrations"}
        encontrados = {nome for (nome,) in estado}
        print(f"\nTabelas finais: {sorted(encontrados)}")
        print("Integridade:", "OK" if esperado <= encontrados else f"FALHOU (faltou {esperado - encontrados})")
