"""Deteccao de anomalias em transacoes financeiras: regras estatisticas vs Isolation Forest."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_recall_fscore_support

SEED = 64
TAXA_FRAUDE = 0.02


def gerar_transacoes(n: int = 8_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    n_fraudes = int(n * TAXA_FRAUDE)

    horas = rng.integers(0, 24, n)
    valores = rng.lognormal(4.6, 0.9, n).round(2)
    distancia_do_padrao = np.abs(rng.normal(0, 25, n)).round(1)

    # fraudes: madrugada, valores altos e fora do raio habitual do cliente
    horas_fraude = rng.choice(range(0, 6), n_fraudes)
    valores_fraude = rng.uniform(3_000, 18_000, n_fraudes)
    distancia_fraude = np.abs(rng.normal(180, 60, n_fraudes))

    horas[:n_fraudes] = horas_fraude
    valores[:n_fraudes] = valores_fraude
    distancia_do_padrao[:n_fraudes] = distancia_fraude

    return pd.DataFrame(
        {
            "hora": horas,
            "valor": valores,
            "distancia_km": distancia_do_padrao,
            "fraude": np.arange(n) < n_fraudes,
        }
    )


def preparar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Hora ciclica evita que 23h pareca distante de 0h para o modelo."""
    return pd.DataFrame(
        {
            "log_valor": np.log1p(df["valor"]),
            "hora_sin": np.sin(2 * np.pi * df["hora"] / 24),
            "hora_cos": np.cos(2 * np.pi * df["hora"] / 24),
            "distancia": df["distancia_km"],
        }
    )


def avaliar(nome: str, alerta: pd.Series, real: pd.Series) -> dict:
    precisao, recall, f1, _ = precision_recall_fscore_support(real, alerta, average="binary", zero_division=0)
    print(f"- {nome:<16} alertas={int(alerta.sum()):>4} | precisao={precisao:.2f} recall={recall:.2f} F1={f1:.2f}")
    return {"metodo": nome, "precisao": precisao, "recall": recall, "f1": f1}


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    transacoes = gerar_transacoes()
    features = preparar_features(transacoes)

    print(f"Transacoes: {len(transacoes)} | fraudes reais: {transacoes['fraude'].sum()}")
    resultados = []

    # metodo 1: IQR sobre o valor (baseline simples de negocio)
    q1, q3 = transacoes["valor"].quantile([0.25, 0.75])
    limite_iqr = q3 + 1.5 * (q3 - q1)
    alerta_iqr = transacoes["valor"] > limite_iqr
    resultados.append(avaliar("IQR valor", alerta_iqr, transacoes["fraude"]))

    # metodo 2: z-score da hora ponderada (compras fora do horario comum)
    z_hora = (transacoes["hora"] - transacoes["hora"].mean()) / transacoes["hora"].std()
    alerta_hora = (z_hora > 2) & (transacoes["valor"] > transacoes["valor"].median())
    resultados.append(avaliar("Z hora+valor", alerta_hora, transacoes["fraude"]))

    # metodo 3: isolation forest multivariado
    iso = IsolationForest(contamination=TAXA_FRAUDE, random_state=SEED)
    rotulo_iso = iso.fit_predict(features) == -1
    resultados.append(avaliar("IsolationForest", pd.Series(rotulo_iso), transacoes["fraude"]))

    melhor = max(resultados, key=lambda r: r["f1"])
    print(f"\nMelhor F1: {melhor['metodo']}")

    if melhor["metodo"] == "IsolationForest":
        top_alertas = transacoes[rotulo_iso].nlargest(5, "valor")
        print("\nTop 5 alertas para investigacao manual:")
        print(top_alertas[["hora", "valor", "distancia_km", "fraude"]].to_string(index=False))

    plt.figure(figsize=(7.5, 5))
    normais = ~rotulo_iso
    plt.scatter(
        transacoes.loc[normais, "hora"],
        transacoes.loc[normais, "valor"],
        s=6,
        alpha=0.35,
        label="normal",
    )
    plt.scatter(
        transacoes.loc[rotulo_iso, "hora"],
        transacoes.loc[rotulo_iso, "valor"],
        s=14,
        color="#dc2626",
        label="alerta",
    )
    plt.yscale("log")
    plt.xlabel("Hora do dia")
    plt.ylabel("Valor (R$, log)")
    plt.title(f"Alertas do {melhor['metodo']}")
    plt.legend()
    plt.tight_layout()
    plt.savefig("outputs/anomalias.png", dpi=120)
    print("\nGrafico salvo em outputs/anomalias.png")
