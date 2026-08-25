"""API de inferencia de risco de credito (FastAPI) consumindo o modelo treinado."""

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field

logger = logging.getLogger("uvicorn.error")

CAMINHO_MODELO = Path("outputs/modelo_credito.joblib")
CAMINHO_METADATA = Path("outputs/metadata_modelo.json")

modelo: Any = None
metadata: dict = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    global modelo, metadata
    if not CAMINHO_MODELO.exists():
        raise RuntimeError("modelo ausente: rode 'python treinar.py' antes de subir a API")
    modelo = joblib.load(CAMINHO_MODELO)
    metadata = json.loads(CAMINHO_METADATA.read_text(encoding="utf-8"))
    logger.info("modelo versao %s carregado (AUC %.3f)", metadata["versao"], metadata["metrica_auc"])
    yield


app = FastAPI(title="API Risco de Credito", version="1.0.0", lifespan=lifespan)


class SolicitacaoEmprestimo(BaseModel):
    renda: float = Field(gt=0, description="renda mensal declarada em R$")
    idade: int = Field(ge=18, le=100)
    tempo_emprego_anos: float = Field(ge=0)
    divida_sobre_renda: float = Field(ge=0, le=1)
    score_serasa: int = Field(ge=0, le=1000)
    atrasos_12m: int = Field(ge=0)


class RespostaRisco(BaseModel):
    probabilidade_inadimplencia: float
    faixa_risco: str
    aprovado_pre_aprovacao: bool


@app.get("/saude")
def saude() -> dict:
    return {"status": "ok", "modelo_carregado": modelo is not None}


@app.get("/informacoes")
def informacoes() -> dict:
    return metadata


@app.post("/predizer", response_model=RespostaRisco)
def predizer(solicitacao: SolicitacaoEmprestimo) -> RespostaRisco:
    entrada = [[getattr(solicitacao, f) for f in metadata["features"]]]
    probabilidade = float(modelo.predict_proba(entrada)[0, 1])

    if probabilidade < 0.30:
        faixa = "baixo"
    elif probabilidade < 0.60:
        faixa = "medio"
    else:
        faixa = "alto"

    return RespostaRisco(
        probabilidade_inadimplencia=round(probabilidade, 4),
        faixa_risco=faixa,
        aprovado_pre_aprovacao=probabilidade < 0.40,
    )
