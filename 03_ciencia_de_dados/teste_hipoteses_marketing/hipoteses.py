"""Ferramentas estatisticas para comparar campanhas: ANOVA, Tukey HSD e tamanho de efeito."""

import numpy as np
import pandas as pd
from scipy import stats


def cohen_d(grupo_a: np.ndarray, grupo_b: np.ndarray) -> float:
    """Tamanho de efeito padronizado; 0.2 pequeno, 0.5 medio, 0.8 grande."""
    n_a, n_b = len(grupo_a), len(grupo_b)
    var_combinada = ((n_a - 1) * grupo_a.var(ddof=1) + (n_b - 1) * grupo_b.var(ddof=1)) / (n_a + n_b - 2)
    return float((grupo_a.mean() - grupo_b.mean()) / np.sqrt(var_combinada))


def resumo_descritivo(grupos: dict[str, np.ndarray]) -> "pd.DataFrame":

    linhas = []
    for nome, valores in grupos.items():
        stat_shapiro, p_normalidade = stats.shapiro(valores)
        linhas.append(
            {
                "campanha": nome,
                "n": len(valores),
                "media": round(float(valores.mean()), 2),
                "desvio": round(float(valores.std(ddof=1)), 2),
                "normal_p": round(p_normalidade, 4),
            }
        )
    return pd.DataFrame(linhas)


def anova_um_fator(grupos: dict[str, np.ndarray]) -> tuple[float, float]:
    estatistica, p_valor = stats.f_oneway(*grupos.values())
    return float(estatistica), float(p_valor)


def tukey_hsd(grupos: dict[str, np.ndarray], alpha: float = 0.05) -> list[dict]:
    """Retorna o resultado do Tukey HSD para todos os pares."""
    resultado = stats.tukey_hsd(*grupos.values())
    nomes = list(grupos)
    pares = []
    for i, a in enumerate(nomes):
        for j, b in enumerate(nomes):
            if j > i:
                pares.append(
                    {
                        "par": f"{a} vs {b}",
                        "diferenca_media": round(float(resultado.statistic[i, j]), 2),
                        "p_valor": round(float(resultado.pvalue[i, j]), 4),
                        "significativo": bool(resultado.pvalue[i, j] < alpha),
                    }
                )
    return pares
