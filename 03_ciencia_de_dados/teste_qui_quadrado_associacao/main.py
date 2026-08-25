"""Qui-quadrado de independencia: plano x churn (associado) e regiao x canal (independente)."""

import numpy as np
import pandas as pd
from scipy import stats

SEED = 150


def cramers_v(tabela: pd.DataFrame, qui2: float) -> float:
    n = tabela.to_numpy().sum()
    min_dim = min(tabela.shape[0] - 1, tabela.shape[1] - 1)
    return float(np.sqrt(qui2 / (n * min_dim)))


def analisar(nome: str, tabela: pd.DataFrame) -> None:
    qui2, p_valor, gl, esperada = stats.chi2_contingency(tabela)
    v = cramers_v(tabela, qui2)

    print(f"\n=== {nome} ===")
    print("Observado:")
    print(tabela.to_string())
    print("\nEsperado sob independencia:")
    print(pd.DataFrame(esperada.round(1), index=tabela.index, columns=tabela.columns).to_string())

    frequencias_baixas = (esperada < 5).sum()
    if frequencias_baixas:
        print(f"Atencao: {frequencias_baixas} celulas com esperado < 5 (qui-quadrado perde validade).")

    forca = "desprezivel" if v < 0.1 else "pequena" if v < 0.3 else "moderada" if v < 0.5 else "forte"
    conclusao = "REJEITA H0: ha associacao" if p_valor < 0.05 else "sem evidencia de associacao"
    print(f"\nchi2={qui2:.2f} | gl={gl} | p-valor={p_valor:.4g} | Cramer's V={v:.3f} ({forca})")
    print(f"Conclusao: {conclusao}")


def gerar_plano_churn(n: int = 5_000) -> pd.DataFrame:
    """Churn depende do plano: Pre 18%, Medio 11%, Pos 6%."""
    rng = np.random.default_rng(SEED)
    plano = rng.choice(["Pre", "Medio", "Pos"], n, p=[0.45, 0.35, 0.20])
    taxa_churn = pd.Series(plano).map({"Pre": 0.18, "Medio": 0.11, "Pos": 0.06})
    churn = rng.random(n) < taxa_churn
    return pd.crosstab(plano, churn).rename(columns={False: "fica", True: "sai"})


def gerar_regiao_canal(n: int = 4_000) -> pd.DataFrame:
    """Regiao e canal de entrada sao realmente independentes aqui."""
    rng = np.random.default_rng(SEED + 1)
    regiao = rng.choice(["Norte", "Sul"], n)
    canal = rng.choice(["site", "app", "loja"], n)
    return pd.crosstab(regiao, canal)


if __name__ == "__main__":
    analisar("PLANO x CHURN (associacao plantada)", gerar_plano_churn())
    analisar("REGIAO x CANAL (independentes)", gerar_regiao_canal())

    print(
        "\nNota metodologica: p-valor so diz SE existe associacao; "
        "o tamanho do efeito (Cramer's V) diz QUAO relevante ela e para o negocio."
    )
