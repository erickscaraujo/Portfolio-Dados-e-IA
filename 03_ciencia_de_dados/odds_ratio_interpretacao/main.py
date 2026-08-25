"""Regressao logistica interpretavel: odds ratios e cenarios de negocio."""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

SEED = 340


def gerar_base(n: int = 9_000) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(SEED)
    divida_renda = rng.beta(2, 5, n)
    renda = rng.lognormal(8.3, 0.45, n)
    atrasos_12m = rng.poisson(0.8, n)

    logit = -1.7 + 4.9 * divida_renda + 0.42 * atrasos_12m - 0.00028 * renda + rng.normal(0, 0.85, n)
    inadimpliu = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)

    return pd.DataFrame(
        {
            "divida_renda": divida_renda.round(3),
            "renda": renda.round(2),
            "atrasos_12m": atrasos_12m,
        }
    ), pd.Series(inadimpliu, name="inadimpliu")


def tabela_odds(modelo: LogisticRegression, features: list[str], incrementos: dict[str, float]) -> pd.DataFrame:
    linhas = []
    for i, feature in enumerate(features):
        coeficiente = modelo.coef_[0][i]
        incremento = incrementos.get(feature, 1.0)

        linhas.append(
            {
                "feature": feature,
                "coef_logit": round(float(coeficiente), 4),
                "odds_ratio_por_unidade": round(float(np.exp(coeficiente)), 3),
                f"odds_ratio_por_incremento ({incremento})": round(float(np.exp(coeficiente * incremento)), 3),
            }
        )
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    X, y = gerar_base()
    features = list(X.columns)

    modelo = LogisticRegression(max_iter=900).fit(X, y)
    incrementos_negocio = {
        "divida_renda": 0.10,  # +10 p.p. de comprometimento
        "renda": 1000.0,  # +R$ 1.000 de renda
        "atrasos_12m": 1.0,
    }  # +1 atraso no ano

    print("=== ODDS RATIOS (exp do coeficiente) ===")
    print(tabela_odds(modelo, features, incrementos_negocio).to_string(index=False))

    coeficientes = dict(zip(features, modelo.coef_[0], strict=True))
    p_medio = y.mean()
    fator_marginal = p_medio * (1 - p_medio)

    print("\n=== EFEITO MARGINAL NA MEDIA ===")
    for feature, incremento in incrementos_negocio.items():
        pp = coeficientes[feature] * fator_marginal * incremento * 100
        direcao = "+" if pp >= 0 else ""
        print(f"- {feature:<13} {direcao}{pp:.2f} p.p. de probabilidade por {incremento}")

    perfil_seguro = {"divida_renda": 0.15, "renda": 6_500.0, "atrasos_12m": 0}
    perfil_arriscado = {"divida_renda": 0.55, "renda": 2_100.0, "atrasos_12m": 4}

    def probabilidade(perfil: dict) -> float:
        entrada = pd.DataFrame([perfil])[features]
        return float(modelo.predict_proba(entrada)[0, 1])

    p_seguro, p_arriscado = probabilidade(perfil_seguro), probabilidade(perfil_arriscado)
    razao_chances = (p_arriscado / (1 - p_arriscado)) / max(p_seguro / (1 - p_seguro), 1e-12)

    print("\n=== CENARIO: PERFIL SEGURO x ARRISCADO ===")
    print(f"- seguro   : P(inadimplir) = {p_seguro:.1%}")
    print(f"- arriscado: P(inadimplir) = {p_arriscado:.1%}")
    print(f"razao de chances entre os dois perfis: {razao_chances:.1f}x")
