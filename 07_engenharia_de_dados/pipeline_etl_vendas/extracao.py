"""Extracao das fontes brutas (CSV e JSON); gera dados com sujeira na primeira execucao."""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
PASTA_BRUTOS = Path("dados_brutos")


def _gerar_brutos(seed: int = 77) -> None:
    """Cria arquivos de origem com problemas tipicos: duplicatas, maiusculas irregulares e nulos."""
    rng = np.random.default_rng(seed)
    PASTA_BRUTOS.mkdir(exist_ok=True)

    clientes = pd.DataFrame(
        {
            "id": list(range(1, 401)) + [55, 120],
            "nome": [f"  cliente {i} ".upper() if i % 9 == 0 else f"Cliente {i}" for i in range(1, 403)],
            "email": [f"cliente{i}@mail.com" if i % 13 else f"invalido_{i}" for i in range(1, 403)],
            "uf": rng.choice(["SP", "sp ", "RJ", "MG", "XX"], 402),
            "idade": rng.integers(18, 75, 402),
        }
    )
    clientes.to_csv(PASTA_BRUTOS / "clientes.csv", index=False)

    pedidos = [
        {
            "pedido_id": f"P{i}",
            "cliente_id": int(rng.integers(1, 420)),
            "categoria": str(rng.choice(["eletronicos", "casa", "livros"])),
            "valor": round(float(rng.uniform(20, 900)), 2),
            "quantidade": int(rng.integers(0, 4)) or 1,
            "data": (pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(rng.integers(0, 200)))).strftime("%Y-%m-%d"),
        }
        for i in range(1, 1_501)
    ]
    pedidos += [pedidos[10].copy()]  # duplicata proposital para testar o dedup
    with open(PASTA_BRUTOS / "pedidos.json", "w", encoding="utf-8") as arq:
        json.dump(pedidos, arq)

    logger.info("arquivos brutos gerados em %s", PASTA_BRUTOS)


def extrair(regenerar: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    csv_clientes = PASTA_BRUTOS / "clientes.csv"
    json_pedidos = PASTA_BRUTOS / "pedidos.json"

    if regenerar or not (csv_clientes.exists() and json_pedidos.exists()):
        _gerar_brutos()

    clientes = pd.read_csv(csv_clientes)
    with open(json_pedidos, encoding="utf-8") as arq:
        pedidos = pd.DataFrame(json.load(arq))

    logger.info("extraidos %d clientes (CSV) e %d pedidos (JSON)", len(clientes), len(pedidos))
    return clientes, pedidos
