"""Indicadores de estoque: giro, cobertura, curva ABC e risco de ruptura."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEED = 23


def gerar_skus(n: int = 220) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    categorias = rng.choice(["Eletronicos", "Casa", "Livros", "Beleza", "Esporte"], n)

    # receita concentrada: poucos SKUs vendem muito (efeito cauda longa)
    demanda_diaria = np.clip(rng.pareto(1.4, n) * 2 + 0.1, 0.1, None).round(1)
    preco_custo = rng.lognormal(3.5, 0.9, n).round(2)
    estoque_atual = np.ceil(demanda_diaria * rng.uniform(3, 90, n)).astype(int)
    lead_time_dias = rng.integers(5, 45, n)

    return pd.DataFrame(
        {
            "sku": [f"SKU{i:04d}" for i in range(n)],
            "categoria": categorias,
            "demanda_diaria": demanda_diaria,
            "preco_custo": preco_custo,
            "estoque_atual": estoque_atual,
            "lead_time_reposicao": lead_time_dias,
        }
    )


def enriquecer(base: pd.DataFrame) -> pd.DataFrame:
    df = base.copy()
    df["receita_anual"] = df["demanda_diaria"] * 365 * df["preco_custo"]
    df["giro_anual"] = np.where(df["estoque_atual"] > 0, df["demanda_diaria"] * 365 / df["estoque_atual"], 0)
    df["dias_cobertura"] = np.where(df["demanda_diaria"] > 0, df["estoque_atual"] / df["demanda_diaria"], 0)

    # curva ABC por receita acumulada (80/15/5)
    ordenado = df.sort_values("receita_anual", ascending=False)
    participacao = ordenado["receita_anual"].cumsum() / ordenado["receita_anual"].sum()
    classe = np.where(participacao <= 0.80, "A", np.where(participacao <= 0.95, "B", "C"))
    df.loc[ordenado.index, "classe_abc"] = classe

    df["risco_ruptura"] = df["dias_cobertura"] < df["lead_time_reposicao"]
    return df


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    estoque = enriquecer(gerar_skus())

    print("=== CURVA ABC ===")
    abc = estoque.groupby("classe_abc").agg(
        skus=("sku", "count"),
        receita=("receita_anual", "sum"),
        giro_medio=("giro_anual", "mean"),
    )
    abc["participacao"] = (abc["receita"] / abc["receita"].sum() * 100).round(1)
    print(abc.to_string(float_format=lambda x: f"{x:,.1f}"))

    print("\n=== RISCO DE RUPTURA (cobertura < lead time) ===")
    criticos = estoque[estoque["risco_ruptura"]]
    print(f"{len(criticos)} SKUs em risco | receita anual exposta: R$ {criticos['receita_anual'].sum():,.0f}")
    print(
        criticos.nlargest(5, "receita_anual")[
            ["sku", "categoria", "dias_cobertura", "lead_time_reposicao", "receita_anual"]
        ].to_string(index=False)
    )

    fig, eixos = plt.subplots(1, 2, figsize=(13, 4.5))
    ordenado = estoque.sort_values("receita_anual", ascending=False)
    eixos[0].plot(
        np.arange(len(ordenado)),
        ordenado["receita_anual"].cumsum() / ordenado["receita_anual"].sum() * 100,
        color="#7c3aed",
    )
    for corte in (0.80, 0.95):
        eixos[0].axhline(corte * 100, ls="--", color="gray", lw=1)
    eixos[0].set_title("Curva ABC (Pareto da receita)")
    eixos[0].set_ylabel("% acumulado")

    cores = {"A": "#16a34a", "B": "#f59e0b", "C": "#94a3b8"}
    for classe, grupo in estoque.groupby("classe_abc"):
        eixos[1].scatter(grupo["dias_cobertura"], grupo["giro_anual"], s=18, alpha=0.6, label=classe, c=cores[classe])
    eixos[1].set_xscale("log")
    eixos[1].set_title("Giro x cobertura (por classe)")
    eixos[1].set_xlabel("Dias de cobertura (log)")
    eixos[1].legend(title="Classe")
    plt.tight_layout()
    plt.savefig("outputs/estoque_abc.png", dpi=120)

    estoque.to_csv("outputs/indicadores_estoque.csv", index=False)
    print("\nCSV e PNG salvos em outputs/")
