"""Metricas de drift para features numericas e scores do modelo."""

import numpy as np
from scipy import stats

EPS = 1e-6


def psi(esperado: np.ndarray, atual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index usando quantis da distribuicao esperada.

    Referencias praticas: <0.10 estavel, 0.10-0.25 alerta, >0.25 drift critico.
    """
    cortes = np.quantile(esperado, np.linspace(0, 1, bins + 1))
    cortes[0], cortes[-1] = -np.inf, np.inf

    dist_esperada = np.histogram(esperado, bins=cortes)[0] / len(esperado)
    dist_atual = np.histogram(atual, bins=cortes)[0] / len(atual)

    dist_esperada = np.clip(dist_esperada, EPS, None)
    dist_atual = np.clip(dist_atual, EPS, None)

    return float(np.sum((dist_atual - dist_esperada) * np.log(dist_atual / dist_esperada)))


def teste_ks(esperado: np.ndarray, atual: np.ndarray) -> tuple[float, float]:
    estatistica, p_valor = stats.ks_2samp(esperado, atual)
    return float(estatistica), float(p_valor)


def status_do_drift(valor_psi: float) -> str:
    if valor_psi < 0.10:
        return "estavel"
    if valor_psi < 0.25:
        return "alerta"
    return "critico"


def score_modelo(renda: np.ndarray, drift: float = 0.0) -> np.ndarray:
    """Probabilidade simulada de inadimplencia; drift alto reduz renda observada e sobe o risco."""
    renda_efetiva = renda / (1 + drift)
    return 1 / (1 + np.exp((renda_efetiva - 3_500) / 700))
