"""Modelo de propensao para priorizar a lista de cross-sell de seguros."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import precision_score, roc_auc_score
from sklearn.model_selection import train_test_split

PRODUTOS = ["cartao", "emprestimo", "investimento", "seguro"]
SEED = 190


def gerar_clientes(n: int = 9_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    renda = rng.lognormal(8.4, 0.45, n)
    tempo_casa_meses = rng.integers(1, 120, n)
    canal_digital = rng.binomial(1, 0.6, n)

    # afinidade latente: relacionamento + patrimonio elevam a chance de seguro
    afinidade = 0.00002 * renda + 0.010 * np.minimum(tempo_casa_meses, 60) + 1.1 * canal_digital + rng.normal(0, 0.8, n)
    probabilidade_por_produto = {
        "cartao": 1 / (1 + np.exp(-(afinidade * 0.8 - 0.2))),
        "emprestimo": 1 / (1 + np.exp(-(afinidade * 0.5 - 0.9))),
        "investimento": 1 / (1 + np.exp(-(afinidade * 0.7 - 1.3))),
        "seguro": 1 / (1 + np.exp(-(afinidade - 1.1))),
    }
    base = pd.DataFrame(
        {
            "renda": renda.round(2),
            "tempo_casa_meses": tempo_casa_meses,
            "canal_digital": canal_digital,
        }
    )
    for produto, probas in probabilidade_por_produto.items():
        base[produto] = rng.random(n) < probas

    return base


def main() -> None:
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    clientes = gerar_clientes()
    tem_seguro = clientes["seguro"]
    features = ["renda", "tempo_casa_meses", "canal_digital", "cartao", "emprestimo", "investimento"]

    elegiveis = clientes[~tem_seguro].reset_index(drop=True)
    alvo_treino = clientes[tem_seguro]
    # treino usa todos com rotulo; scoring so nos que NAO tem o produto
    X_tr, X_te, y_tr, y_te = train_test_split(
        pd.concat([alvo_treino[features], elegiveis[features]]),
        np.concatenate([np.ones(len(alvo_treino)), np.zeros(len(elegiveis))]),
        test_size=0.3,
        random_state=SEED,
    )

    modelo = GradientBoostingClassifier(random_state=SEED)
    modelo.fit(X_tr, y_tr)

    auc = roc_auc_score(y_te, modelo.predict_proba(X_te)[:, 1])
    print(f"AUC holdout: {auc:.3f}")

    propensao = modelo.predict_proba(elegiveis[features])[:, 1]
    ranking = elegiveis.assign(propensao=propensao).sort_values("propensao", ascending=False)

    # validacao por proxy: quanto maior a propensao, maior a taxa de outros produtos caros
    top_10pct = ranking.head(max(len(ranking) // 10, 1))
    proxy_top = top_10pct["investimento"].mean()
    proxy_resto = ranking.tail(len(ranking) - len(top_10pct))["investimento"].mean()
    lift = proxy_top / max(proxy_resto, 1e-9)
    print(f"Precision@10% (proxy investimento): {proxy_top:.1%} | lift vs resto da base: {lift:.2f}x")

    curva = (
        ranking.assign(faixa=pd.qcut(ranking.index, 10, labels=False)).groupby("faixa")["propensao"].sum().cumsum()
        / ranking["propensao"].sum()
    )

    plt.figure(figsize=(7.8, 4.4))
    plt.plot(range(1, 11), curva.values * 100, marker="o", color="#7c3aed")
    plt.plot([1, 10], [10, 100], ls="--", color="gray", label="aleatorio")
    plt.xlabel("Decil da lista priorizada")
    plt.ylabel("% do ganho acumulado")
    plt.title("Curva de ganho — cross-sell de seguros")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/cross_sell_ganho.png", dpi=120)

    lista_final = ranking.head(50)[["renda", "tempo_casa_meses", "canal_digital", "propensao"]]
    lista_final.to_csv("outputs/lista_cross_sell.csv", index=False)
    print("\nTop-5 da lista priorizada:")
    print(lista_final.head().to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    precision_check = precision_score(y_te, modelo.predict_proba(X_te)[:, 1] >= 0.5, zero_division=0)
    print(f"\n(precision padrao no holdout: {precision_check:.2f})")
    print("Lista top-50 salva em outputs/lista_cross_sell.csv")


if __name__ == "__main__":
    main()
