"""Analise logistica: OTD por transportadora, atrasos e custo por kg."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TRANSPORTADORAS = {
    "RapidaLog": {"otd_base": 0.93, "custo_kg": 4.2, "peso": 0.45},
    "TransNorte": {"otd_base": 0.86, "custo_kg": 3.1, "peso": 0.35},
    "EconomiCarga": {"otd_base": 0.74, "custo_kg": 2.2, "peso": 0.20},
}

SEED = 11


def gerar_embarques(n: int = 5_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    nomes = list(TRANSPORTADORAS)
    pesos = [TRANSPORTADORAS[t]["peso"] for t in nomes]
    transportadora = rng.choice(nomes, size=n, p=np.array(pesos) / sum(pesos))

    # piora sazonal no fim do ano (apertos de capacidade)
    datas = pd.Timestamp("2024-01-02") + pd.to_timedelta(rng.integers(0, 540, n), unit="D")
    fator_natal = np.where(datas.month.isin([11, 12]), 0.08, 0)

    otd_por_transportadora = np.array([TRANSPORTADORAS[t]["otd_base"] for t in transportadora])
    entregue_no_prazo = rng.random(n) < (otd_por_transportadora - fator_natal)

    peso_kg = np.clip(rng.lognormal(1.6, 0.9, n), 0.3, None).round(2)
    prazo_prometido = rng.integers(2, 9, n)
    atraso_dias = np.where(entregue_no_prazo, 0, np.ceil(rng.exponential(2.6, n))).astype(int)
    custo = (
        np.array([TRANSPORTADORAS[t]["custo_kg"] for t in transportadora]) * peso_kg * rng.normal(1, 0.12, n)
    ).round(2)

    return pd.DataFrame(
        {
            "data": datas,
            "transportadora": transportadora,
            "destino_uf": rng.choice(["SP", "RJ", "MG", "RS", "BA", "PE"], n),
            "peso_kg": peso_kg,
            "prazo_prometido": prazo_prometido,
            "atraso_dias": atraso_dias,
            "custo_frete": custo,
            "no_prazo": entregue_no_prazo,
        }
    )


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_embarques()

    print("=== OTD POR TRANSPORTADORA ===")
    por_transportadora = base.groupby("transportadora").agg(
        embarques=("no_prazo", "size"),
        otd=("no_prazo", "mean"),
        atraso_medio_dias=("atraso_dias", "mean"),
        custo_medio_kg=("custo_frete", lambda c: c.sum() / base.loc[c.index, "peso_kg"].sum()),
    )
    por_transportadora["otd"] = (por_transportadora["otd"] * 100).round(1)
    print(por_transportadora.sort_values("otd", ascending=False).to_string())

    meta_otd = 90.0
    criticas = por_transportadora[por_transportadora["otd"] < meta_otd].index.tolist()
    print(f"\nMeta de OTD: {meta_otd:.0f}% | abaixo da meta: {', '.join(criticas) or 'ninguem'}")

    print("\n=== OTD MENSAL (evolucao) ===")
    mensal = (
        base.assign(mes=base["data"].dt.to_period("M").astype(str))
        .groupby(["mes", "transportadora"])["no_prazo"]
        .mean()
        .unstack()
        .mul(100)
        .round(1)
    )
    print(mensal.tail(6).to_string())

    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.2))
    mensal.plot(ax=eixos[0], marker="o")
    eixos[0].axhline(meta_otd, ls="--", color="gray")
    eixos[0].set_title("OTD mensal (%)")
    por_transportadora["custo_medio_kg"].plot.barh(ax=eixos[1], color="#0369a1")
    eixos[1].set_title("Custo medio por kg")
    atrasos = base.loc[base["atraso_dias"] > 0, "atraso_dias"]
    eixos[2].hist(atrasos, bins=range(1, int(atrasos.max()) + 2), color="#b45309", alpha=0.85)
    eixos[2].set_title("Distribuicao de dias de atraso")
    plt.tight_layout()
    plt.savefig("outputs/logistica.png", dpi=120)

    print("\nPainel salvo em outputs/logistica.png")
