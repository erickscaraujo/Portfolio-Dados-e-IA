"""Inferencia em batch: pontua lotes grandes em chunks com memoria previsivel."""

import json
import math
from pathlib import Path

import numpy as np

TAMANHO_CHUNK = 5_000


def psi(esperado: np.ndarray, atual: np.ndarray, cortes: list[float]) -> float:
    """PSI entre o score de treino (baseline) e o score de hoje."""
    bordas = np.array(cortes).copy()
    bordas[0], bordas[-1] = -np.inf, np.inf

    dist_esperada = np.histogram(esperado, bins=bordas)[0] / len(esperado)
    dist_atual = np.histogram(atual, bins=bordas)[0] / len(atual)
    dist_esperada, dist_atual = np.clip(dist_esperada, 1e-6, None), np.clip(dist_atual, 1e-6, None)

    return float(np.sum((dist_atual - dist_esperada) * np.log(dist_atual / dist_esperada)))


def _lotes_sinteticos(total: int, drift_renda: float = 1.0, chunk: int = TAMANHO_CHUNK):
    """Simula a chegada de novos clientes; drift_renda > 1 piora a carteira gradualmente."""
    rng = np.random.default_rng(88)
    for _ in range(math.ceil(total / chunk)):
        n = min(chunk, total)
        total -= n
        renda = rng.lognormal(8.2, 0.5, n) / drift_renda
        divida = rng.beta(2, 6, n)
        atrasos = rng.poisson(0.9, n)
        yield np.column_stack([renda / 10_000, divida, atrasos])


def pontuar_lote(modelo, total: int, caminho_saida: str, baseline: dict, drift_renda: float = 1.0) -> dict:
    scores_acumulados: list[np.ndarray] = []
    aprovados = 0
    pontuados = 0

    with open(caminho_saida, "w", encoding="utf-8") as saida:
        saida.write("probabilidade_inadimplencia,faixa_risco\n")
        for lote in _lotes_sinteticos(total, drift_renda):
            probabilidades = modelo.predict_proba(lote)[:, 1]
            for probabilidade in probabilidades:
                faixa = "baixo" if probabilidade < 0.30 else ("medio" if probabilidade < 0.60 else "alto")
                saida.write(f"{probabilidade:.4f},{faixa}\n")

            scores_acumulados.append(probabilidades)
            aprovados += int((probabilidades < 0.40).sum())
            pontuados += len(probabilidades)

    scores_hoje = np.concatenate(scores_acumulados)
    valor_psi = psi(np.array(baseline["quantis"]), scores_hoje, baseline["quantis"])

    resumo = {
        "pontuados": pontuados,
        "taxa_aprovacao": round(aprovados / pontuados, 4),
        "score_medio": round(float(scores_hoje.mean()), 4),
        "psi_vs_treino": round(valor_psi, 3),
        "status_drift": "estavel" if valor_psi < 0.10 else ("alerta" if valor_psi < 0.25 else "critico"),
    }
    Path(caminho_saida).with_suffix(".json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return resumo
