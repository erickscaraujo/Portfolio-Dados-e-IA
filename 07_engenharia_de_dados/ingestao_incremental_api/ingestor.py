"""Ingestor incremental: watermark persistido, dedup e escrita em JSONL."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CAMINHO_EVENTOS = Path("outputs/eventos.jsonl")
CAMINHO_STATE = Path("outputs/state.json")


def carregar_watermark() -> int:
    if CAMINHO_STATE.exists():
        return json.loads(CAMINHO_STATE.read_text(encoding="utf-8"))["ultimo_id"]
    return 0


def _salvar_watermark(ultimo_id: int) -> None:
    CAMINHO_STATE.write_text(json.dumps({"ultimo_id": ultimo_id}), encoding="utf-8")


def sincronizar(api) -> dict[str, int]:
    """Puxa apenas o que mudou desde a ultima execucao; seguro rodar quantas vezes quiser."""
    watermark = carregar_watermark()
    logger.info("watermark atual: id %d", watermark)

    CAMINHO_EVENTOS.parent.mkdir(exist_ok=True)
    ids_vistos: set[int] = set()
    novos = 0

    with open(CAMINHO_EVENTOS, "a", encoding="utf-8") as destino:
        while True:
            pagina = api.listar_apos(watermark)
            if not pagina:
                break

            for evento in pagina:
                if evento["id"] in ids_vistos:
                    continue  # protecao contra duplicidade dentro da mesma execucao
                ids_vistos.add(evento["id"])
                destino.write(json.dumps(evento, ensure_ascii=False) + "\n")
                novos += 1
                watermark = max(watermark, evento["id"])

    _salvar_watermark(watermark)
    logger.info("sincronizacao concluida: %d novos eventos | chamadas a API: %d", novos, api.chamadas)
    return {"novos": novos, "total_acumulado": watermark}
