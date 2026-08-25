"""Decomposicao aditiva: tendencia + indice sazonal mensal + residuo."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MESES = 48
SEED = 350


def gerar_serie() -> pd.Series:
    rng = np.random.default_rng(SEED)
    periodo = pd.period_range("2022-01", periods=MESES, freq="M")
    tendencia = 420_000 + 6_500 * np.arange(MESES)

    # sazonalidade fixa por mes (vendas caem em janeiro, explodem em dezembro)
    indice_sazonal = {
        1: -0.14,
        2: -0.08,
        3: 0.02,
        4: 0.0,
        5: 0.03,
        6: 0.05,
        7: -0.04,
        8: 0.01,
        9: 0.06,
        10: 0.09,
        11: 0.16,
        12: 0.28,
    }
    sazonal = np.array([indice_sazonal[p.month] for p in periodo]) * tendencia

    ruido = rng.normal(0, 18_000, MESES)
    return pd.Series((tendencia + sazonal + ruido).round(2), index=periodo.to_timestamp(), name="receita")


def decompor(serie: pd.Series) -> dict[str, pd.Series]:
    # media movel centralizada de 12 meses estima a tendencia sem defasar meio ciclo
    tendencia = serie.rolling(12, center=True).mean()

    detrended = serie - tendencia
    indice = detrended.groupby(detrended.index.month).mean()
    sazonal = serie.index.map(lambda d: indice[d.month]).to_series(index=serie.index)

    residuo = serie - tendencia - sazonal
    return {"tendencia": tendencia, "sazonal": sazonal, "residuo": residuo, "indice_mensal": indice}


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    serie = gerar_serie()
    partes = decompor(serie)
    indice = partes["indice_mensal"]

    print("=== INDICE SAZONAL POR MES (R$) ===")
    rotulos = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    for numero_mes, valor in indice.items():
        barra = "#" * max(int(abs(valor) / 2000), 1 if valor > 0 else 0)
        sinal = "+" if valor >= 0 else ""
        print(f"- {rotulos[numero_mes - 1]}: {sinal}{valor:>9,.0f} {barra}")

    melhor_mes = int(indice.idxmax())
    pior_mes = int(indice.idxmin())
    print(
        f"\nMes mais forte: {rotulos[melhor_mes - 1]} ({indice.max():+,.0f}) | "
        f"mais fraco: {rotulos[pior_mes - 1]} ({indice.min():+,.0f})"
    )

    ajustada = serie - partes["sazonal"]
    crescimento_ajustado = ajustada.iloc[-3:].mean() / ajustada.iloc[:3].mean() - 1
    print(f"Crescimento da tendência (ajustado sazonalmente): {crescimento_ajustado:+.1%}")

    fig, eixos = plt.subplots(4, 1, figsize=(11, 9), sharex=True)
    eixos[0].plot(serie, color="#334155")
    eixos[0].set_ylabel("original")
    eixos[1].plot(partes["tendencia"], color="#2563eb")
    eixos[1].set_ylabel("tendencia")
    eixos[2].bar(partes["sazonal"].index, partes["sazonal"], width=22, color="#7c3aed")
    eixos[2].set_ylabel("sazonal")
    eixos[3].plot(partes["residuo"], color="#94a3b8", lw=0.9)
    eixos[3].set_ylabel("residuo")
    eixos[0].set_title("Decomposição aditiva da receita mensal")
    for eixo in eixos:
        eixo.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig("outputs/decomposicao_sazonal.png", dpi=120)

    print("\nPainel salvo em outputs/decomposicao_sazonal.png")
