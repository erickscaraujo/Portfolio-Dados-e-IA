"""Previsao de demanda diaria com features temporais e comparacao contra baselines."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression


def gerar_serie(inicio: str = "2022-01-01", dias: int = 1095, seed: int = 13) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    datas = pd.date_range(inicio, periods=dias, freq="D")
    tendencia = np.linspace(0, 70, dias)
    sazonal_anual = 45 * np.sin(2 * np.pi * datas.dayofyear / 365 - 1.4)
    # fins de semana vendem menos na operacao B2B simulada
    efeito_semana = np.where(datas.dayofweek >= 5, -35, np.where(datas.dayofweek == 4, 20, 10))
    demanda = 240 + tendencia + sazonal_anual + efeito_semana + rng.normal(0, 22, dias)
    return pd.DataFrame({"data": datas, "demanda": np.clip(demanda, 40, None).round()})


def criar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["dia_semana"] = df["data"].dt.dayofweek
    # lags capturam autocorrelacao; media movel suaviza ruido de curto prazo
    for lag in (1, 7, 14):
        df[f"lag_{lag}"] = df["demanda"].shift(lag)
    df["media_movel_7"] = df["demanda"].shift(1).rolling(7).mean()
    df = pd.get_dummies(df, columns=["dia_semana"], drop_first=True)
    return df.dropna().reset_index(drop=True)


def metricas(y_real: pd.Series, y_previsto: np.ndarray) -> dict:
    mae = np.mean(np.abs(y_real - y_previsto))
    rmse = np.sqrt(np.mean((y_real - y_previsto) ** 2))
    mape = np.mean(np.abs((y_real - y_previsto) / y_real))
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = criar_features(gerar_serie())

    # split temporal estrito: nunca treinar com o futuro
    corte = pd.Timestamp("2024-10-01")
    treino = base[base["data"] < corte]
    validacao = base[base["data"] >= corte]
    colunas = [c for c in base.columns if c not in ("data", "demanda")]

    modelos = {
        "Naive (lag 7)": None,
        "Regressao Linear": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=300, max_depth=12, random_state=13, n_jobs=-1),
    }

    resultados = {}
    previsoes = {}
    for nome, modelo in modelos.items():
        if nome.startswith("Naive"):
            pred = validacao["lag_7"].to_numpy()
        else:
            modelo.fit(treino[colunas], treino["demanda"])
            pred = modelo.predict(validacao[colunas])
        resultados[nome] = metricas(validacao["demanda"], pred)
        previsoes[nome] = pred

    print("=== VALIDACAO OUT-OF-TIME (out/2024 em diante) ===")
    tabela = pd.DataFrame(resultados).T
    print(tabela.to_string(float_format=lambda x: f"{x:,.1f}"))

    melhor = min(resultados, key=lambda k: resultados[k]["RMSE"])
    print(f"\nMelhor modelo por RMSE: {melhor}")

    rf = modelos["Random Forest"]
    importancias = pd.Series(rf.feature_importances_, index=colunas).sort_values(ascending=False)
    print("\nImportancia das features (top 6):")
    print(importancias.head(6).to_string(float_format=lambda x: f"{x:.3f}"))

    janela = slice(-60, None)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(validacao["data"].iloc[janela], validacao["demanda"].iloc[janela], label="Real", lw=1.6)
    ax.plot(
        validacao["data"].iloc[janela],
        previsoes[melhor][janela],
        label=f"Previsto ({melhor})",
        ls="--",
    )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.set_title(f"Demanda real vs prevista — ultimos 60 dias ({melhor})")
    ax.set_ylabel("Unidades")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/previsao_demanda.png", dpi=120)
    print("\nGrafico salvo em outputs/previsao_demanda.png")
