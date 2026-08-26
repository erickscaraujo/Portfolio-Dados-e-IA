"""Curvas de aprendizado: overfit x underfit com diagnostico automatico."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

TAMANHOS = [50, 150, 400, 1_000, 2_500, 4_000]
SEED = 390


def gerar_base(n: int = 5_000) -> tuple[pd.DataFrame, pd.Series]:
    """Relação não-linear: árvore consegue, linear não."""
    rng = np.random.default_rng(SEED)
    area = rng.uniform(30, 300, n)
    quartos = rng.integers(1, 6, n)
    idade = rng.integers(0, 60, n)

    preco = 40 * np.sqrt(area) + 15_000 * quartos - 900 * idade - 0.008 * (idade**2) + rng.normal(0, 25_000, n)
    return pd.DataFrame({"area": area, "quartos": quartos, "idade": idade}), pd.Series(preco)


def curva_aprendizado(modelo_fabrica, X: pd.DataFrame, y: pd.Series) -> dict[str, list[float]]:
    X_tr_total, X_val, y_tr_total, y_val = train_test_split(X, y, test_size=0.25, random_state=SEED)

    treino_rmse, validacao_rmse = [], []
    for tamanho in TAMANHOS:
        if tamanho > len(X_tr_total):
            continue
        modelo = modelo_fabrica()
        modelo.fit(X_tr_total.iloc[:tamanho], y_tr_total.iloc[:tamanho])

        rmse_treino = mean_squared_error(y_tr_total.iloc[:tamanho], modelo.predict(X_tr_total.iloc[:tamanho])) ** 0.5
        rmse_val = mean_squared_error(y_val, modelo.predict(X_val)) ** 0.5

        treino_rmse.append(rmse_treino)
        validacao_rmse.append(rmse_val)

    return {"treino": treino_rmse, "validacao": validacao_rmse, "tamanhos_usados": TAMANHOS[: len(treino_rmse)]}


def diagnosticar(curva: dict) -> str:
    gap_final = curva["validacao"][-1] - curva["treino"][-1]
    escala = curva["validacao"][-1]

    if gap_final / escala > 0.25:
        return (
            "OVERFIT: gap grande entre treino e validacao. "
            "Regularizar mais, simplificar o modelo ou coletar mais dados."
        )
    if curva["treino"][-1] > 0.6 * escala:
        return "UNDERFIT: erro alto nos dois lados. Modelo/feature set mais expressivos."
    return "BOM equilibrio: gap pequeno e erro convergindo."


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    X, y = gerar_base()

    candidatos = {
        "RandomForest sem limites": lambda: RandomForestRegressor(random_state=SEED),
        "Regressao Linear": lambda: LinearRegression(),
    }

    fig, eixos = plt.subplots(1, 2, figsize=(13.5, 4.8), sharey=True)
    for eixo, (nome, fabrica) in zip(eixos, candidatos.items(), strict=True):
        curva = curva_aprendizado(fabrica, X, y)
        eixo.plot(curva["tamanhos_usados"], curva["treino"], marker="o", label="treino")
        eixo.plot(curva["tamanhos_usados"], curva["validacao"], marker="s", label="validacao")
        eixo.set_title(nome)
        eixo.set_xlabel("tamanho do conjunto de treino")
        eixo.set_ylabel("RMSE (R$)")
        eixo.legend()
        eixo.grid(alpha=0.3)

        print(f"=== {nome} ===")
        print(f"- RMSE final: treino {curva['treino'][-1]:,.0f} | validacao {curva['validacao'][-1]:,.0f}")
        print(f"- Diagnostico: {diagnosticar(curva)}\n")

    plt.tight_layout()
    plt.savefig("outputs/aprendizado_diagnostico.png", dpi=120)
    print("Curvas salvas em outputs/aprendizado_diagnostico.png")
