"""Regressao de preco de imoveis: linear interpretavel vs gradient boosting."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

SEED = 31
BAIRROS = {"Centro": 1.35, "Jardins": 1.55, "Industrial": 0.75, "Suburbio": 0.6, "Lagoa Sul": 1.25}


def gerar_imoveis(n: int = 3_500) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    bairro = rng.choice(list(BAIRROS), n)
    area = np.clip(rng.lognormal(4.4, 0.35, n), 30, None).round()
    quartos = np.clip(rng.poisson(2.2, n) + 1, 1, 6)
    banheiros = np.clip((quartos // 2) + rng.integers(0, 2, n), 1, 5)
    vagas = rng.integers(0, 4, n)
    idade = rng.integers(0, 45, n)

    # preco base por m2 do bairro, deprecacao pela idade e ruido de negociacao
    preco_m2 = pd.Series(bairro).map(BAIRROS).to_numpy() * 6_800
    preco = (
        area * preco_m2
        + quartos * 18_000
        + banheiros * 12_000
        + vagas * 22_000
        - idade * 2_200
        + rng.normal(0, 60_000, n)
    )
    return pd.DataFrame(
        {
            "bairro": bairro,
            "area_m2": area.astype(int),
            "quartos": quartos,
            "banheiros": banheiros,
            "vagas": vagas,
            "idade_anos": idade,
            "preco": np.clip(preco, 80_000, None).round(-2),
        }
    )


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = pd.get_dummies(df, columns=["bairro"], drop_first=True)
    return df


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    imoveis = preparar(gerar_imoveis())
    alvo = "preco"
    features = [c for c in imoveis.columns if c != alvo]

    X_tr, X_te, y_tr, y_te = train_test_split(imoveis[features], imoveis[alvo], test_size=0.25, random_state=SEED)

    modelos = {
        "Linear": LinearRegression(),
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=400, learning_rate=0.08, random_state=SEED),
    }

    ajustados = {}
    print("=== COMPARACAO DE MODELOS (holdout) ===")
    for nome, modelo in modelos.items():
        modelo.fit(X_tr, y_tr)
        pred = modelo.predict(X_te)
        mae = mean_absolute_error(y_te, pred)
        r2 = r2_score(y_te, pred)
        print(f"- {nome:<22} MAE R$ {mae:>10,.0f} | R2 {r2:.3f}")
        ajustados[nome] = (modelo, pred)

    melhor_nome = min(
        ajustados,
        key=lambda nome: mean_absolute_error(y_te, ajustados[nome][1]),
    )
    melhor, previsao = ajustados[melhor_nome]
    print(f"\nMelhor modelo: {melhor_nome}")

    if melhor_nome == "Linear":
        coeficientes = pd.Series(melhor.coef_, index=features).sort_values(key=abs, ascending=False)
        print("\nCoeficientes (impacto em R$ por unidade):")
        print(coeficientes.head(8).to_string(float_format=lambda x: f"{x:,.0f}"))
    else:
        importancia = permutation_importance(melhor, X_te, y_te, random_state=SEED, n_repeats=5)
        ranking = pd.Series(importancia.importances_mean, index=features).sort_values(ascending=False)
        print("\nImportancia por permutacao:")
        print(ranking.head(8).to_string(float_format=lambda x: f"{x:.3f}"))

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    amostra = np.random.default_rng(SEED).choice(len(y_te), 800, replace=False)
    ax.scatter(np.asarray(y_te)[amostra], previsao[amostra], s=9, alpha=0.45)
    limite = [y_te.min(), y_te.max()]
    ax.plot(limite, limite, "--", color="#b91c1c")
    ax.set_title(f"Real x previsto ({melhor_nome})")
    ax.set_xlabel("Preco real (R$)")
    ax.set_ylabel("Preco previsto (R$)")
    plt.tight_layout()
    plt.savefig("outputs/imoveis_real_previsto.png", dpi=120)

    joblib.dump(melhor, "outputs/modelo_imoveis.joblib")
    print("\nModelo salvo em outputs/modelo_imoveis.joblib")
