"""EDA de RH: rotatividade, satisfacao e faixas salariais de uma base sintetica."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEED = 15
DEPARTAMENTOS = {
    "Tecnologia": {"peso": 0.25, "salario": (7_500, 2_200)},
    "Vendas": {"peso": 0.30, "salario": (4_800, 1_400)},
    "Operacoes": {"peso": 0.25, "salario": (3_600, 900)},
    "Marketing": {"peso": 0.12, "salario": (5_200, 1_300)},
    "Financeiro": {"peso": 0.08, "salario": (6_100, 1_500)},
}


def gerar_colaboradores(n: int = 1_200) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    departamentos = rng.choice(
        list(DEPARTAMENTOS),
        size=n,
        p=[d["peso"] for d in DEPARTAMENTOS.values()],
    )

    salario = np.array([max(rng.normal(*DEPARTAMENTOS[dept]["salario"]), 1_800) for dept in departamentos]).round(2)
    satisfacao = np.clip(rng.normal(3.3, 0.9, n), 1, 5).round(1)
    tempo_casa = np.clip(rng.gamma(2, 2.5, n), 0.2, 25).round(1)

    # quem esta insatisfeito e recente sai com mais frequencia
    logit = -0.8 - 0.9 * (satisfacao - 3) + 0.35 * (tempo_casa < 2) + rng.normal(0, 0.5, n)
    saiu = rng.binomial(1, 1 / (1 + np.exp(-logit)))

    return pd.DataFrame(
        {
            "departamento": departamentos,
            "idade": rng.integers(22, 60, n),
            "salario": salario,
            "satisfacao": satisfacao,
            "tempo_casa_anos": tempo_casa,
            "saiu": saiu,
        }
    )


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    rh = gerar_colaboradores()

    print("=== VISAO GERAL ===")
    taxa_geral = rh["saiu"].mean()
    print(f"Colaboradores: {len(rh)} | Rotatividade geral: {taxa_geral:.1%}")

    print("\n=== ROTATIVIDADE POR DEPARTAMENTO ===")
    por_depto = rh.groupby("departamento").agg(taxa=("saiu", "mean"), headcount=("saiu", "count"))
    por_depto["taxa"] = (por_depto["taxa"] * 100).round(1)
    print(por_depto.sort_values("taxa", ascending=False).to_string())

    print("\n=== SATISFACAO X SAIDA ===")
    faixas = pd.cut(rh["satisfacao"], bins=[1, 2, 3, 4, 5], labels=["1-2", "2-3", "3-4", "4-5"])
    tabela_satisfacao = rh.groupby(faixas, observed=True)["saiu"].mean().mul(100).round(1)
    print(tabela_satisfacao.to_string(name="taxa de saida (%)"))

    correlacao = rh[["satisfacao", "tempo_casa_anos", "salario", "saiu"]].corr()["saiu"].drop("saiu")
    print("\nCorrelacao com a saida:")
    print(correlacao.to_string(float_format=lambda x: f"{x:.2f}"))

    fig, eixos = plt.subplots(1, 3, figsize=(15, 4.2))
    por_depto["taxa"].sort_values().plot.barh(ax=eixos[0], color="#b91c1c", title="Rotatividade por departamento (%)")
    rh.boxplot(column="salario", by="departamento", ax=eixos[1], showfliers=False)
    eixos[1].set_title("Salario por departamento")
    cores = rh["saiu"].map({0: "#2563eb", 1: "#dc2626"})
    eixos[2].scatter(rh["tempo_casa_anos"], rh["satisfacao"], c=cores, s=10, alpha=0.5)
    eixos[2].set_title("Tempo de casa x satisfacao (vermelho = saiu)")
    eixos[2].set_xlabel("Anos de casa")
    plt.suptitle("")
    plt.tight_layout()
    plt.savefig("outputs/painel_rh.png", dpi=120)

    print("\nPainel salvo em outputs/painel_rh.png")
