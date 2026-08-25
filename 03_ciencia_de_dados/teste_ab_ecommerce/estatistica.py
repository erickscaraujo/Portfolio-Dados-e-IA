"""Funcoes estatisticas para teste A/B de proporcoes (duas amostras independentes)."""

import numpy as np
from scipy import stats


def taxa_conversao(conversoes: int, n: int) -> float:
    return conversoes / n


def z_estatistica(conv_a: int, n_a: int, conv_b: int, n_b: int) -> float:
    """Z-teste agrupado para diferenca de duas proporcoes."""
    p_pool = (conv_a + conv_b) / (n_a + n_b)
    erro_padrao = np.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
    p_a = conv_a / n_a
    p_b = conv_b / n_b
    return (p_b - p_a) / erro_padrao


def p_valor_bilateral(z: float) -> float:
    return 2 * (1 - stats.norm.cdf(abs(z)))


def intervalo_confianca(conv: int, n: int, confianca: float = 0.95) -> tuple[float, float]:
    z = stats.norm.ppf(1 - (1 - confianca) / 2)
    p = conv / n
    margem = z * np.sqrt(p * (1 - p) / n)
    return p - margem, p + margem


def tamanho_amostral(p_base: float, mde: float, alpha: float = 0.05, poder: float = 0.80) -> int:
    """N minimo por grupo para detectar um lift absoluto de `mde` sobre `p_base`."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(poder)
    variancia_total = p_base * (1 - p_base) + (p_base + mde) * (1 - p_base - mde)
    return int(np.ceil((z_alpha + z_beta) ** 2 * variancia_total / mde**2))


def poder_estatistico(p_base: float, p_alternativa: float, n: int, alpha: float = 0.05) -> float:
    """Poder aproximado dado o efeito real entre os grupos."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    erro_padrao = np.sqrt(p_base * (1 - p_base) * 2 / n)
    delta = abs(p_alternativa - p_base)
    return 1 - stats.norm.cdf(z_alpha - delta / erro_padrao)
