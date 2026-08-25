"""Sinistros de seguros: loss ratio, frequencia, severidade e aging."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PRODUTOS = {
    # produto: (apolices, premio medio, frequencia por apolice, severidade media)
    "Auto": {"apolices": 3_200, "premio_medio": 1_850, "frequencia": 0.14, "severidade": 9_500},
    "Residencial": {"apolices": 2_100, "premio_medio": 640, "frequencia": 0.08, "severidade": 4_200},
    "Vida": {"apolices": 1_700, "premio_medio": 1_120, "frequencia": 0.015, "severidade": 42_000},
}
TETO_LOSS_RATIO = 70.0

SEED = 310


def gerar_carteira() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    sinistros = []

    for produto, cfg in PRODUTOS.items():
        n_sinistros = int(cfg["apolices"] * cfg["frequencia"])
        valores = np.clip(
            rng.normal(cfg["severidade"], cfg["severidade"] * 0.45, n_sinistros), cfg["severidade"] * 0.15, None
        ).round(2)
        dias_abertos = rng.exponential(38, n_sinistros).round(0).astype(int)

        for i in range(n_sinistros):
            aberto = dias_abertos[i] > 45 and rng.random() < 0.35
            sinistros.append(
                {
                    "produto": produto,
                    "valor_indenizacao": valores[i],
                    "dias_em_aberto": dias_abertos[i],
                    "status": "aberto" if aberto else "fechado",
                }
            )

    return pd.DataFrame(sinistros)


def metricas_por_produto(sinistros: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for produto, cfg in PRODUTOS.items():
        sub = sinistros[sinistros["produto"] == produto]
        premios = cfg["apolices"] * cfg["premio_medio"]
        pagos = sub["valor_indenizacao"].sum()

        linhas.append(
            {
                "produto": produto,
                "apolices": cfg["apolices"],
                "sinistros": len(sub),
                "frequencia_por_mil": round(len(sub) / cfg["apolices"] * 1000, 1),
                "severidade_media": round(sub["valor_indenizacao"].mean(), 0),
                "loss_ratio_pct": round(pagos / premios * 100, 1),
            }
        )
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    sinistros = gerar_carteira()
    tabela = metricas_por_produto(sinistros).set_index("produto")

    print("=== METRICAS POR PRODUTO ===")
    print(tabela.to_string())

    acima_do_teto = tabela[tabela["loss_ratio_pct"] > TETO_LOSS_RATIO]
    if not acima_do_teto.empty:
        print(
            f"\nAcima do teto tecnico ({TETO_LOSS_RATIO}%): "
            + ", ".join(f"{p} ({r}%)".replace(".0%", "%") for p, r in acima_do_teto["loss_ratio_pct"].items())
        )

    abertos = sinistros[sinistros["status"] == "aberto"].copy()
    abertos["faixa_aging"] = pd.cut(
        abertos["dias_em_aberto"], bins=[0, 30, 90, np.inf], labels=["0-30d", "31-90d", "90+d"]
    )
    aging = abertos.groupby("faixa_aging", observed=True)["valor_indenizacao"].agg(["count", "sum"])
    print("\n=== AGING DE SINISTROS ABERTOS ===")
    print(aging.round(0).to_string())

    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.3))
    eixos[0].bar(tabela.index, tabela["loss_ratio_pct"], color="#b91c1c", alpha=0.85)
    eixos[0].axhline(TETO_LOSS_RATIO, ls="--", color="black")
    eixos[0].set_title("Loss ratio (%) x teto tecnico")
    eixos[1].scatter(
        tabela["frequencia_por_mil"], tabela["severidade_media"], s=tabela["apolices"], alpha=0.7, color="#0369a1"
    )
    for produto, linha in tabela.iterrows():
        eixos[1].annotate(produto, (linha["frequencia_por_mil"], linha["severidade_media"]))
    eixos[1].set_title("Frequencia x severidade (bolha = carteira)")
    matriz_aging = abertos.groupby(["produto", "faixa_aging"], observed=True).size().unstack(fill_value=0)
    matriz_aging.plot.bar(stacked=True, ax=eixos[2], color=["#4ade80", "#facc15", "#dc2626"])
    eixos[2].set_title("Aging de abertos por produto")
    plt.tight_layout()
    plt.savefig("outputs/sinistros_seguros.png", dpi=120)

    print("\nPainel salvo em outputs/sinistros_seguros.png")
