"""Como a escolha do CV muda o resultado: vazamento temporal em numeros."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold, TimeSeriesSplit


def gerar_serie_com_regime(n: int = 1_200, seed: int = 160) -> pd.DataFrame:
    """Demanda com tendencia crescente e quebra de nivel no meio (regime novo)."""
    rng = np.random.default_rng(seed)
    dias = np.arange(n)
    nivel = np.where(dias < n // 2, 100.0, 150.0)  # mudanca de regime
    demanda = nivel + dias * 0.05 + rng.normal(0, 8, n)

    df = pd.DataFrame({"demanda": demanda})
    # features com lags: o passado explica, mas o FUTURO nao pode entrar no treino
    for lag in (1, 2, 7):
        df[f"lag_{lag}"] = df["demanda"].shift(lag)
    return df.dropna().reset_index(drop=True)


def avaliar_estrategia(nome: str, splitter, X: pd.DataFrame, y: pd.Series, embaralhar: bool = False) -> float:
    maes = []
    for treino_idx, validacao_idx in splitter.split(X):
        modelo = RandomForestRegressor(120, max_depth=8, random_state=7, n_jobs=-1)
        modelo.fit(X.iloc[treino_idx], y.iloc[treino_idx])
        previsao = modelo.predict(X.iloc[validacao_idx])
        maes.append(mean_absolute_error(y.iloc[validacao_idx], previsao))

    media = float(np.mean(maes))
    print(f"- {nome:<26} MAE medio: {media:6.2f} (folds: {[round(m, 1) for m in maes]})")
    return media


if __name__ == "__main__":
    base = gerar_serie_com_regime()
    X = base.drop(columns="demanda")
    y = base["demanda"]

    print("=== MESMO MODELO, TRES ESTRATEGIAS DE CV ===")
    mae_shuffle = avaliar_estrategia(
        "KFold shuffle (vazamento!)", KFold(5, shuffle=True, random_state=7), X, y, embaralhar=True
    )
    mae_ordenado = avaliar_estrategia("KFold sem shuffle", KFold(5, shuffle=False), X, y)
    mae_temporal = avaliar_estrategia("TimeSeriesSplit", TimeSeriesSplit(5), X, y)

    inflacao = mae_temporal / mae_shuffle - 1
    print(
        f"\nO erro real em producao ({mae_temporal:.2f}) e "
        f"{inflacao:+.0%} maior que o prometido pelo shuffle ({mae_shuffle:.2f})."
    )
    print("Motivo: com embaralhamento, o modelo ve lags de dias que AINDA NAO EXISTIAM quando valida o futuro.")
    print("\nRegra pratica:")
    print("- dados independentes e identicamente distribuidos -> KFold estratificado ok")
    print("- series temporais -> TimeSeriesSplit (ou holdout out-of-time)")
