"""Estatisticas nao-parametricas para comparar distribuicoes salariais."""

import numpy as np
import pandas as pd
from scipy import stats


def rank_biserial(grupo_a: np.ndarray, grupo_b: np.ndarray, u_estatistica: float) -> float:
    """Tamanho de efeito do Mann-Whitney; +1 = A sempre maior, -1 = sempre menor."""
    n_a, n_b = len(grupo_a), len(grupo_b)
    return 1 - (2 * u_estatistica) / (n_a * n_b)


def bootstrap_diferenca_medianas(
    grupo_a: np.ndarray,
    grupo_b: np.ndarray,
    n_repeticoes: int = 10_000,
    seed: int = 7,
) -> tuple[float, float]:
    """IC 95% da diferenca de medianas por bootstrap — sem assumir forma de distribuicao."""
    rng = np.random.default_rng(seed)
    diferencas = np.empty(n_repeticoes)
    for i in range(n_repeticoes):
        amostra_a = rng.choice(grupo_a, size=len(grupo_a), replace=True)
        amostra_b = rng.choice(grupo_b, size=len(grupo_b), replace=True)
        diferencas[i] = np.median(amostra_a) - np.median(amostra_b)

    return tuple(np.quantile(diferencas, [0.025, 0.975]))


def mann_whitney(grupo_a: np.ndarray, grupo_b: np.ndarray) -> tuple[float, float]:
    resultado = stats.mannwhitneyu(grupo_a, grupo_b, alternative="two-sided")
    return float(resultado.statistic), float(resultado.pvalue)


def resumo_salarios(df: "pd.DataFrame") -> None:
    for grupo, sub in df.groupby("area"):
        print(
            f"- {grupo}: mediana R$ {sub['salario'].median():,.2f} | "
            f"n={len(sub)} | media R$ {sub['salario'].mean():,.2f}"
        )
