"""Tarefas de um batch noturno de consolidacao de vendas (operam sobre um contexto compartilhado)."""

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


def extrair_pedidos(contexto: dict) -> list[dict]:
    rng = np.random.default_rng(2025)
    pedidos = [
        {
            "id": i,
            "categoria": str(rng.choice(["digital", "fisico", "assinatura"])),
            "valor": round(float(rng.uniform(30, 700)), 2),
        }
        for i in range(1, 301)
    ]
    contexto["pedidos"] = pedidos
    logger.info("extraidos %d pedidos da fonte", len(pedidos))
    return pedidos


_CONTADORES_VALIDACAO = 0


def validar_volumes(contexto: dict) -> None:
    """Falha nas duas primeiras chamadas para demonstrar o mecanismo de retry."""
    global _CONTADORES_VALIDACAO

    contador = _CONTADORES_VALIDACAO
    _CONTADORES_VALIDACAO += 1
    if contador < 2:
        raise ConnectionError(f"fonte instavel simulada (tentativa {contador + 1})")

    if not contexto.get("pedidos"):
        raise ValueError("nenhum pedido extraido")
    logger.info("volume ok: %d registros", len(contexto["pedidos"]))


def enriquecer(contexto: dict) -> list[dict]:
    pedidos = contexto["pedidos"]
    for pedido in pedidos:
        pedido["faixa"] = "alto" if pedido["valor"] > 400 else ("medio" if pedido["valor"] > 150 else "baixo")
    contexto["enriquecido"] = True
    logger.info("faixa de valor calculada para todos os pedidos")
    return pedidos


def agregar_por_categoria(contexto: dict) -> dict[str, float]:
    totais: dict[str, float] = {}
    for pedido in contexto["pedidos"]:
        totais[pedido["categoria"]] = totais.get(pedido["categoria"], 0.0) + pedido["valor"]
    contexto["agregacao"] = totais
    logger.info("agregado por categoria: %s", {k: round(v, 2) for k, v in totais.items()})
    return totais


def publicar_resultado(contexto: dict) -> Path:
    destino = Path("outputs/carga_batch.json")
    destino.parent.mkdir(exist_ok=True)
    with open(destino, "w", encoding="utf-8") as arq:
        json.dump(
            {"total_por_categoria": contexto["agregacao"], "registros": len(contexto["pedidos"])},
            arq,
            ensure_ascii=False,
            indent=2,
        )
    logger.info("resultado publicado em %s", destino)
    return destino
