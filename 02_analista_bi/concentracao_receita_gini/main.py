"""Concentracao de receita: Lorenz, Gini, HHI e dependencia de poucos clientes."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

N_CLIENTES = 900
SEED = 330


def gerar_receitas() -> pd.DataFrame:
    """Pareto: poucos clientes grandes, muitos pequenos (cauda realista)."""
    rng = np.random.default_rng(SEED)
    receita = (rng.pareto(1.35, N_CLIENTES) + 1) * 900
    return pd.DataFrame(
        {
            "cliente": [f"C{i:04d}" for i in range(N_CLIENTES)],
            "receita": np.round(receita, 2),
        }
    )


def gini(valores: np.ndarray) -> float:
    """Gini via trapezios na curva de Lorenz: 0 = perfeitamente distribuido."""
    ordenado = np.sort(valores)
    acumulado = np.cumsum(ordenado) / ordenado.sum()
    lorenz_x = np.linspace(0, 1, len(ordenado))
    return float(1 - 2 * np.trapezoid(acumulado, lorenz_x))


def hhi(receitas: np.ndarray) -> int:
    participacoes = receitas / receitas.sum()
    return int((participacoes**2).sum() * 10_000)


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_receitas().sort_values("receita", ascending=False).reset_index(drop=True)
    total = base["receita"].sum()

    print("=== CONCENTRACAO POR TOP N ===")
    for n_pct in (1, 5, 10):
        k = max(int(N_CLIENTES * n_pct / 100), 1)
        share = base.head(k)["receita"].sum() / total
        print(f"- top {n_pct:>2}% ({k} clientes): {share:.1%} da receita")

    indice_gini = gini(base["receita"].to_numpy())
    indice_hhi = hhi(base["receita"].to_numpy())
    leitura_hhi = (
        "concentrado" if indice_hhi > 2500 else "moderadamente concentrado" if indice_hhi > 1500 else "desconcentrado"
    )
    print(f"\nGini: {indice_gini:.3f} | HHI: {indice_hhi} -> {leitura_hhi}")

    dependentes = base[base["receita"] / total > 0.10]
    if len(dependentes):
        print(f"\nALERTA: {len(dependentes)} cliente(s) acima de 10% da receita:")
        for _, linha in dependentes.iterrows():
            print(f"  - {linha['cliente']}: {linha['receita'] / total:.1%}")
    else:
        maior = base.iloc[0]
        print(f"\nMaior cliente responde por {maior['receita'] / total:.1%} (abaixo do limite de risco de 10%)")

    # curva de Lorenz
    acumulado = np.concatenate([[0], np.cumsum(base.sort_values("receita")["receita"])])
    lorenz_y = acumulado / acumulado[-1]
    lorenz_x = np.linspace(0, 1, len(lorenz_y))

    plt.figure(figsize=(7.8, 5.4))
    plt.plot(lorenz_x * 100, lorenz_y * 100, lw=2.2, color="#b91c1c", label=f"real (Gini {indice_gini:.2f})")
    plt.plot([0, 100], [0, 100], ls="--", color="gray", label="igualdade perfeita")
    plt.fill_between(lorenz_x * 100, lorenz_y * 100, lorenz_x * 100, color="#fca5a5", alpha=0.35)
    plt.xlabel("% acumulado de clientes (do menor para o maior)")
    plt.ylabel("% acumulado da receita")
    plt.title("Curva de Lorenz — concentração da receita")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/lorenz_concentracao.png", dpi=120)

    print("\nCurva de Lorenz salva em outputs/lorenz_concentracao.png")
