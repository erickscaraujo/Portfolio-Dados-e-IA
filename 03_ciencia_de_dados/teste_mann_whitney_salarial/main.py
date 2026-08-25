"""Diferenca salarial entre areas com a mesma funcao: teste nao-parametrico completo."""

import matplotlib

matplotlib.use("Agg")

import estatistica_np as enp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

SEED = 44


def gerar_salarios(n_por_area: int = 320) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    # mesma funcao, areas diferentes: lognormal com mediana distinta e caudas longas
    area_a = rng.lognormal(np.log(9_500), 0.45, n_por_area)
    area_b = rng.lognormal(np.log(8_700), 0.55, n_por_area)

    return pd.DataFrame(
        {
            "area": ["Engenharia de Dados"] * n_por_area + ["Analytics Geral"] * n_por_area,
            "salario": np.concatenate([area_a, area_b]).round(2),
        }
    )


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_salarios()

    print("=== RESUMO POR AREA ===")
    enp.resumo_salarios(base)

    assimetrias = base.groupby("area")["salario"].apply(lambda s: float(stats.skew(s)))
    print(f"\nAssimetria (skew): {assimetrias.round(2).to_dict()}")
    print("Caudas longas -> mediana e o centro mais honesto; teste parametrico ficaria fragilizado.")

    grupo_a = base.loc[base["area"] == "Engenharia de Dados", "salario"].to_numpy()
    grupo_b = base.loc[base["area"] == "Analytics Geral", "salario"].to_numpy()

    u_stat, p_valor = enp.mann_whitney(grupo_a, grupo_b)
    efeito = enp.rank_biserial(grupo_a, grupo_b, u_stat)
    ic_inferior, ic_superior = enp.bootstrap_diferenca_medianas(grupo_a, grupo_b)

    print("\n=== MANN-WHITNEY U ===")
    print(f"U = {u_stat:,.0f} | p-valor = {p_valor:.4f}")
    print(
        f"Efeito rank-biserial = {efeito:+.3f} "
        f"({'pequeno' if abs(efeito) < 0.3 else 'moderado' if abs(efeito) < 0.5 else 'grande'})"
    )

    print("\n=== BOOTSTRAP DA DIFERENCA DE MEDIANAS (10k reamostragens) ===")
    diferenca_real = np.median(grupo_a) - np.median(grupo_b)
    print(f"Diferenca observada: R$ {diferenca_real:,.2f}")
    print(f"IC 95%: [R$ {ic_inferior:,.2f}, R$ {ic_superior:,.2f}]")

    if p_valor < 0.05 and ic_inferior > 0:
        decisao = (
            "DIFERENCA CONFIRMADA: Engenharia de Dados ganha mais em mediana, com intervalo inteiramente positivo."
        )
    elif p_valor >= 0.05:
        decisao = "SEM EVIDENCIA de diferenca entre as areas."
    else:
        decisao = "Resultado ambiguo: significativo, mas o IC cruza o zero. Ampliar a amostra."

    print(f"\nDECISAO: {decisao}")

    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    dados_plot = [grupo_a, grupo_b]
    caixas = ax.boxplot(
        dados_plot,
        tick_labels=["Eng. de Dados", "Analytics Geral"],
        showfliers=False,
        patch_artist=True,
    )
    for caixa, cor in zip(caixas["boxes"], ["#1d4ed8", "#dc2626"], strict=True):
        caixa.set_facecolor(cor)
        caixa.set_alpha(0.65)
    ax.set_title(f"Distribuicao salarial | diferenca de medianas R$ {diferenca_real:,.0f}")
    ax.set_ylabel("Salario mensal (R$)")
    plt.tight_layout()
    plt.savefig("outputs/salarios_areas.png", dpi=120)
    print("\nGrafico salvo em outputs/salarios_areas.png")
