"""Ranking anual de vendedores: atingimento, consistencia e premios."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

VENDEDORES = {
    "Ana": {"quota": 120_000, "habilidade": 1.12},
    "Bruno": {"quota": 100_000, "habilidade": 1.02},
    "Carla": {"quota": 150_000, "habilidade": 0.97},
    "Diego": {"quota": 90_000, "habilidade": 0.88},
    "Elisa": {"quota": 130_000, "habilidade": 1.05},
    "Felipe": {"quota": 110_000, "habilidade": 0.93},
}
MESES = 12
SEED = 55


def gerar_vendas() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    linhas = []
    for nome, cfg in VENDEDORES.items():
        # sazonalidade de fim de ano + habilidade individual + ruido
        for mes in range(1, MESES + 1):
            sazonal = 1.25 if mes in (11, 12) else (0.9 if mes in (1, 2) else 1.0)
            realizado = cfg["quota"] * cfg["habilidade"] * sazonal * rng.normal(1, 0.14)
            linhas.append(
                {
                    "vendedor": nome,
                    "mes": mes,
                    "quota": cfg["quota"],
                    "realizado": max(realizado, cfg["quota"] * 0.3),
                }
            )
    return pd.DataFrame(linhas)


def pontuar(anual: pd.DataFrame) -> pd.DataFrame:
    ranking = anual.copy()
    # consistencia: proporcao de meses com quota batida, ponderada pela magnitude do erro
    ranking["pontos"] = ranking["atingimento_medio"] * 0.8 + ranking["meses_batidos"] / MESES * 0.2
    ranking = ranking.sort_values("pontos", ascending=False)
    ranking["posicao"] = range(1, len(ranking) + 1)

    elegiveis = ranking["atingimento_medio"] >= 0.90
    ranking["premio"] = "nenhum"
    podio = ranking[elegiveis].head(3).index
    valores = ["ouro", "prata", "bronze"]
    for posicao, premio in zip(podio, valores, strict=False):
        ranking.loc[posicao, "premio"] = premio
    return ranking


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_vendas()

    anual = base.groupby("vendedor").agg(
        realizado_total=("realizado", "sum"),
        quota_total=("quota", "sum"),
        atingimento_medio=("realizado", lambda r: (r.sum()) / (base.loc[r.index, "quota"].iloc[0] * MESES)),
    )
    batidos = (
        base.assign(bateu=base["realizado"] >= base["quota"]).groupby("vendedor")["bateu"].sum().rename("meses_batidos")
    )
    anual = anual.join(batidos)
    anual["atingimento_medio"] = anual["realizado_total"] / anual["quota_total"]

    ranking = pontuar(anual)

    print("=== RANKING ANUAL ===")
    colunas = ["posicao", "vendedor" if "vendedor" in ranking.columns else None]
    ranking_exibicao = ranking.reset_index().rename(columns={ranking.index.name or "index": "vendedor"})
    print(
        ranking_exibicao[
            ["posicao", "vendedor", "realizado_total", "atingimento_medio", "meses_batidos", "pontos", "premio"]
        ].to_string(index=False, float_format=lambda x: f"{x:,.2f}")
    )

    com_flag = base.assign(bateu=base["realizado"] >= base["quota"])
    grupos_streak = (
        com_flag.groupby(["vendedor", (com_flag["bateu"] != com_flag["bateu"].shift()).cumsum()])["bateu"]
        .agg(lambda s: s.iloc[0] * len(s))
        .reset_index(level=1, drop=True)
        .groupby("vendedor")
        .max()
        .sort_values(ascending=False)
    )
    print(f"\nMaior sequencia de meses batendo quota: {grupos_streak.index[0]} ({int(grupos_streak.iloc[0])} meses)")

    plt.figure(figsize=(8.5, 4.6))
    plot = ranking.sort_values("atingimento_medio")
    plt.barh(
        plot.index,
        plot["atingimento_medio"] * 100,
        color=["#16a34a" if v >= 100 else "#f59e0b" if v >= 90 else "#dc2626" for v in plot["atingimento_medio"]],
    )
    plt.axvline(100, ls="--", color="black", lw=1)
    plt.xlabel("Atingimento medio da quota (%)")
    plt.title("Ranking de vendedores — linha 100% = quota")
    for i, (_nome, linha) in enumerate(plot.iterrows()):
        plt.text(linha["atingimento_medio"] * 100 + 1, i, f"{linha['atingimento_medio']:.0%}", va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig("outputs/ranking_vendedores.png", dpi=120)

    print("Grafico salvo em outputs/ranking_vendedores.png")
