"""Monta e executa o DAG do batch noturno."""

import logging

from dag import SUCESSO, Orquestrador, Tarefa
from tarefas import (
    agregar_por_categoria,
    enriquecer,
    extrair_pedidos,
    publicar_resultado,
    validar_volumes,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S")


def main() -> int:
    contexto: dict = {}

    orquestrador = Orquestrador()
    orquestrador.adicionar(Tarefa("extrair", lambda: extrair_pedidos(contexto)))
    orquestrador.adicionar(Tarefa("validar", lambda: validar_volumes(contexto), ["extrair"], max_tentativas=4))
    orquestrador.adicionar(Tarefa("enriquecer", lambda: enriquecer(contexto), ["validar"]))
    orquestrador.adicionar(Tarefa("agregar", lambda: agregar_por_categoria(contexto), ["validar"]))
    orquestrador.adicionar(Tarefa("publicar", lambda: publicar_resultado(contexto), ["agregar"]))

    status = orquestrador.executar()

    print("\n=== RESUMO DO BATCH ===")
    print(orquestrador.resumo())
    return 0 if all(s == SUCESSO for s in status.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
