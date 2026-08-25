"""Backfill que cai no meio e retoma exatamente onde parou."""

import logging

import backfill

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S")


def main() -> int:
    print("=== EXECUCAO 1: fonte historica instavel ===")
    codigo = backfill.executar_backfill()

    if codigo != 0:
        print("\n... time de infra estabilizou a fonte ...\n")
        backfill.marcar_fonte_recuperada()
        print("=== EXECUCAO 2: retomada pelo checkpoint ===")
        codigo = backfill.executar_backfill()

    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
