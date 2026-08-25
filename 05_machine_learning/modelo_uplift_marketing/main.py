"""Uplift modeling (T-learner): quem de fato compra PORQUE recebeu a campanha?"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

SEED = 15


def gerar_clientes(n: int = 8_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    renda = rng.lognormal(8.3, 0.45, n)
    visitas_30d = rng.poisson(2.5, n)
    comprou_90d = rng.binomial(1, 0.3, n)

    tratamento = rng.binomial(1, 0.5, n)  # randomizacao garante comparabilidade

    # tres segmentos latentes: persuadidos (campanha ajuda), sempre-compram e cachorros dorminhoes
    logit_base = -1.9 + 0.00012 * renda + 0.22 * visitas_30d + 0.5 * comprou_90d
    efeito_tratamento = np.where(
        (visitas_30d >= 2) & (comprou_90d == 0),
        +0.9,  # persuadiveis
        np.where(comprou_90d == 1, -0.4, 0.05),  # sempre compram / dorminhocos
    )
    probabilidade = 1 / (1 + np.exp(-(logit_base + efeito_tratamento * tratamento)))
    comprou_campanha = rng.binomial(1, probabilidade)

    return pd.DataFrame(
        {
            "renda": renda.round(2),
            "visitas_30d": visitas_30d,
            "comprou_90d": comprou_90d,
            "tratamento": tratamento,
            "converteu": comprou_campanha,
        }
    )


def treinar_t_learner(base: pd.DataFrame) -> tuple[LogisticRegression, LogisticRegression]:
    features = ["renda", "visitas_30d", "comprou_90d"]
    modelo_tratados = LogisticRegression(max_iter=1000)
    modelo_controle = LogisticRegression(max_iter=1000)

    tratados = base[base["tratamento"] == 1]
    controle = base[base["tratamento"] == 0]
    modelo_tratados.fit(tratados[features], tratados["converteu"])
    modelo_controle.fit(controle[features], controle["converteu"])
    return modelo_tratados, modelo_controle


def tabela_uplift_por_decil(uplift: np.ndarray, conversao_real: np.ndarray, tratamento: np.ndarray) -> pd.DataFrame:
    """Conversao incremental observada por decil de score predito."""
    df = pd.DataFrame(
        {
            "decil": pd.qcut(uplift, 10, labels=False, duplicates="drop") + 1,
            "converteu": conversao_real,
            "tratamento": tratamento,
        }
    )
    agregado = df.groupby("decil").apply(
        lambda g: g.loc[g["tratamento"] == 1, "converteu"].mean() - g.loc[g["tratamento"] == 0, "converteu"].mean(),
        include_groups=False,
    )
    return agregado.rename("uplift_observado").reset_index().sort_values("decil", ascending=False)


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_clientes()
    treino, teste = train_test_split(base, test_size=0.35, random_state=SEED)

    modelo_t, modelo_c = treinar_t_learner(treino)
    features = ["renda", "visitas_30d", "comprou_90d"]

    p_tratado = modelo_t.predict_proba(teste[features])[:, 1]
    p_controle = modelo_c.predict_proba(teste[features])[:, 1]
    teste = teste.assign(uplift=p_tratado - p_controle)

    print("=== UPLIFT MEDIO POR DECIL DE SCORE ===")
    decil = tabela_uplift_por_decil(
        teste["uplift"].to_numpy(), teste["converteu"].to_numpy(), teste["tratamento"].to_numpy()
    )
    print(decil.to_string(index=False, float_format=lambda x: f"{x:+.3f}"))

    alvo = decil.head(3)["decil"].tolist()
    publico_alvo = teste[pd.qcut(teste["uplift"], 10, labels=False, duplicates="drop").isin([d - 1 for d in alvo])]
    tamanho_campanha = len(publico_alvo)
    ganho_estimado = publico_alvo["uplift"].sum()
    print("\n=== RECOMENDACAO ===")
    print(f"Campanha apenas nos 3 decis com maior uplift: {tamanho_campanha:,} clientes")
    print(f"Conversoes incrementais estimadas: {ganho_estimado:,.0f}")
    custo_evitado = len(teste) - tamanho_campanha
    print(f"Clients que NAO devem receber (efeito nulo ou negativo): {custo_evitado:,}")

    ordenado = teste.sort_values("uplift", ascending=False).reset_index(drop=True)
    ganho_acumulado = ordenado.groupby(pd.qcut(ordenado.index, 10, labels=False))["uplift"].sum().cumsum()
    plt.figure(figsize=(7.5, 4.4))
    plt.plot(range(1, 11), ganho_acumulado.values, marker="o", color="#7c3aed")
    plt.xlabel("Decis de uplift (mais persuasivel -> menos)")
    plt.ylabel("Ganho acumulado de conversoes")
    plt.title("Curva de ganho do modelo de uplift")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/uplift_ganho.png", dpi=120)
    print("\nCurva salva em outputs/uplift_ganho.png")
