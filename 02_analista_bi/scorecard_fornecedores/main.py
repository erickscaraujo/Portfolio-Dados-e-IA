"""Scorecard ponderado de fornecedores com classificacao A/B/C."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PESOS = {"otd": 0.35, "qualidade": 0.30, "preco": 0.20, "lead_time": 0.15}

SEED = 33


def gerar_fornecedores(n: int = 24) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    return pd.DataFrame(
        {
            "fornecedor": [f"Forn-{i:02d}" for i in range(1, n + 1)],
            "entregas": rng.integers(40, 260, n),
            "otd_pct": np.clip(rng.normal(0.88, 0.09, n), 0.55, 1.0),
            "defeito_pct": np.clip(rng.beta(2, 40, n), 0, 0.12),
            "indice_preco": rng.normal(1.0, 0.10, n).round(3),  # 1.0 = preco de mercado
            "lead_time_dias": rng.integers(4, 35, n),
        }
    )


def pontuar(df: pd.DataFrame) -> pd.DataFrame:
    nota = df.copy()

    # preco: mais barato que o mercado soma; normaliza em faixa plausivel (0.7 a 1.3)
    nota["nota_preco"] = ((1.3 - nota["indice_preco"]) / 0.6).clip(0, 1)
    nota["nota_lead"] = (1 - (nota["lead_time_dias"] - 4) / 26).clip(0, 1)

    nota["score_final"] = (
        PESOS["otd"] * nota["otd_pct"]
        + PESOS["qualidade"] * (1 - nota["defeito_pct"])
        + PESOS["preco"] * nota["nota_preco"]
        + PESOS["lead_time"] * nota["nota_lead"]
    ) * 100

    # cortes de gestao: A = parceiro estrategico, C = plano de desenvolvimento
    nota["classe"] = np.select(
        [nota["score_final"] >= 85, nota["score_final"] >= 70],
        ["A", "B"],
        default="C",
    )
    return nota.sort_values("score_final", ascending=False).round({"otd_pct": 3, "defeito_pct": 4, "score_final": 1})


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    ranking = pontuar(gerar_fornecedores())

    print("=== RANKING DE FORNECEDORES ===")
    colunas = [
        "fornecedor",
        "entregas",
        "otd_pct",
        "defeito_pct",
        "indice_preco",
        "lead_time_dias",
        "score_final",
        "classe",
    ]
    print(ranking[colunas].to_string(index=False))

    resumo_classe = ranking.groupby("classe").agg(
        fornecedores=("fornecedor", "count"),
        score_medio=("score_final", "mean"),
        otd_media=("otd_pct", "mean"),
    )
    print("\n=== RESUMO POR CLASSE ===")
    print(resumo_classe.round(2).to_string())

    piores = ranking[ranking["classe"] == "C"]["fornecedor"].tolist()
    if piores:
        print(f"\nPlano de acao sugerido para classe C: {', '.join(piores)}")

    plt.figure(figsize=(9, 8))
    cores = {"A": "#16a34a", "B": "#f59e0b", "C": "#dc2626"}
    plot = ranking.sort_values("score_final")
    plt.barh(plot["fornecedor"], plot["score_final"], color=[cores[c] for c in plot["classe"]])
    plt.axvline(70, ls="--", color="gray", lw=1)
    plt.axvline(85, ls="--", color="gray", lw=1)
    plt.xlabel("Score final (0-100)")
    plt.title("Scorecard de fornecedores")
    plt.tight_layout()
    plt.savefig("outputs/scorecard_fornecedores.png", dpi=120)

    ranking.to_csv("outputs/scorecard_fornecedores.csv", index=False)
    print("\nCSV e PNG salvos em outputs/")
