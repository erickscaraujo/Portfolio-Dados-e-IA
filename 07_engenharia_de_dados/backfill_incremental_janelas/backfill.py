"""Backfill historico em janelas diarias com checkpoint de retomada."""

import json
import logging
from datetime import date, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

PASTA_AGREGADOS = Path("outputs/agregados")
CAMINHO_STATE = Path("outputs/backfill_state.json")
DATA_INICIO = date(2025, 1, 1)
DATA_FIM = date(2025, 1, 20)

# dia que a fonte historica "cai" na primeira execucao (para demonstrar a retomada)
DIA_INSTAVEL = date(2025, 1, 9)


def carregar_checkpoint() -> str | None:
    if CAMINHO_STATE.exists():
        return json.loads(CAMINHO_STATE.read_text(encoding="utf-8"))["ultima_janela_concluida"]
    return None


def salvar_checkpoint(dia: date) -> None:
    CAMINHO_STATE.write_text(json.dumps({"ultima_janela_concluida": dia.isoformat()}), encoding="utf-8")


def processar_janela(dia: date) -> dict:
    """Agregado de um dia; falha deterministicamente no dia instavel da 1a passada."""
    if dia == DIA_INSTAVEL and not _fonte_recuperada:
        raise ConnectionError(f"fonte historica indisponivel para {dia}")

    # agregacao simulada deterministica por dia
    seed = dia.toordinal()
    total_pedidos = 300 + (seed * 7) % 250
    receita = round(15_000 + (seed % 400) * 31.7, 2)
    return {"dia": dia.isoformat(), "pedidos": total_pedidos, "receita": receita}


_fonte_recuperada = False


def marcar_fonte_recuperada() -> None:
    global _fonte_recuperada
    _fonte_recuperada = True


def janelas_pendentes(checkpoint: str | None) -> list[date]:
    inicio = DATA_INICIO if checkpoint is None else date.fromisoformat(checkpoint) + timedelta(days=1)
    dias = []
    atual = inicio
    while atual <= DATA_FIM:
        dias.append(atual)
        atual += timedelta(days=1)
    return dias


def executar_backfill() -> int:
    PASTA_AGREGADOS.mkdir(parents=True, exist_ok=True)
    checkpoint = carregar_checkpoint()

    if checkpoint is None:
        logger.info("backfill do zero: %s ate %s", DATA_INICIO, DATA_FIM)
    else:
        logger.info("retomando a partir de %s (checkpoint)", date.fromisoformat(checkpoint) + timedelta(days=1))

    processadas = 0
    for dia in janelas_pendentes(checkpoint):
        try:
            resultado = processar_janela(dia)
        except ConnectionError as erro:
            logger.error("falhou em %s: %s", dia, erro)
            logger.error("checkpoint permanece em %s; rode novamente apos estabilizar a fonte", checkpoint or "inicio")
            return 1

        destino = PASTA_AGREGADOS / f"{dia.isoformat()}.json"
        destino.write_text(json.dumps(resultado), encoding="utf-8")
        salvar_checkpoint(dia)
        processadas += 1
        logger.info("janela %s concluida (%s)", dia, destino.name)

    logger.info("backfill finalizado com %d janelas processadas nesta execucao", processadas)
    return 0
