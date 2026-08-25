"""Ingestao incremental de uma API paginada: roda duas vezes para provar a idempotencia."""

import logging

from cliente_api import ClienteApiEventos
from ingestor import sincronizar

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S")


def main() -> None:
    api = ClienteApiEventos(total_eventos=500, page_size=120)

    print("=== EXECUCAO 1 (primeira carga) ===")
    resultado1 = sincronizar(api)

    print("\n=== EXECUCAO 2 (nada novo na fonte) ===")
    resultado2 = sincronizar(api)

    if resultado1["novos"] == 500 and resultado2["novos"] == 0:
        print("\nIdempotencia confirmada: segunda execucao nao duplicou nem refetchou nada.")
    else:
        print(f"\nAtencao: padrao inesperado {resultado1} / {resultado2}")


if __name__ == "__main__":
    main()
