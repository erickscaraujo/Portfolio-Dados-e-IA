"""Orquestrador do pipeline ETL: extracao -> transformacao -> carga com logs e CLI."""

import argparse
import logging
import time

import carregamento
import extracao
import transformacao

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def rodar(caminho_dw: str) -> dict[str, int]:
    inicio = time.perf_counter()

    logger.info("ETAPA 1/3 — extracao")
    clientes_brutos, pedidos_brutos = extracao.extrair()

    logger.info("ETAPA 2/3 — transformacao")
    clientes, rejeitados_cli = transformacao.limpar_clientes(clientes_brutos)
    pedidos, descartados_ped = transformacao.limpar_pedidos(pedidos_brutos)
    fato = transformacao.construir_fato(pedidos, clientes)

    logger.info("ETAPA 3/3 — carga no data warehouse")
    contagens = carregamento.carregar(clientes, fato, caminho_dw)

    logger.info("pipeline finalizado em %.2fs", time.perf_counter() - inicio)
    logger.info(
        "resumo: %d clientes validos | %d pedidos rejeitados | fato=%s",
        len(clientes),
        rejeitados_cli + descartados_ped,
        contagens["fato_pedido"],
    )
    return contagens


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline ETL de vendas para SQLite")
    parser.add_argument("--dw", default="outputs/dw_vendas.sqlite", help="caminho do data warehouse de saida")
    argumentos = parser.parse_args()

    resultado = rodar(argumentos.dw)
    print("\n=== AMOSTRA DO DW (ultimos meses carregados) ===")
    print(carregamento.consulta_resumo(argumentos.dw).to_string(index=False))
