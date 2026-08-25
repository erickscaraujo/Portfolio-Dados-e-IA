"""Registro de experimentos local: runs em JSONL, selecao do melhor e recarga do modelo."""

import json
import uuid
from datetime import datetime
from pathlib import Path

CAMINHO_REGISTRO = Path("outputs/runs.jsonl")


def registrar_run(experimento: str, params: dict, metricas: dict, artefato: Path | str) -> str:
    """Append-only: historico imutavel de tudo que ja foi treinado."""
    run_id = uuid.uuid4().hex[:8]
    registro = {
        "run_id": run_id,
        "experimento": experimento,
        "params": params,
        "metricas": metricas,
        "artefato": str(artefato),
        "criado_em": datetime.now().isoformat(timespec="seconds"),
    }
    CAMINHO_REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    with open(CAMINHO_REGISTRO, "a", encoding="utf-8") as arq:
        arq.write(json.dumps(registro) + "\n")
    return run_id


def listar_runs(experimento: str) -> list[dict]:
    if not CAMINHO_REGISTRO.exists():
        return []
    with open(CAMINHO_REGISTRO, encoding="utf-8") as arq:
        runs = [json.loads(linha) for linha in arq if linha.strip()]
    return [run for run in runs if run["experimento"] == experimento]


def melhor_run(experimento: str, metrica: str) -> dict:
    runs = listar_runs(experimento)
    if not runs:
        raise ValueError(f"nenhum run registrado para '{experimento}'")
    return max(runs, key=lambda run: run["metricas"][metrica])
