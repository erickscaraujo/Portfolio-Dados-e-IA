"""Campanhas de marketing: CTR, CPC, CPA, ROAS e pacing do orcamento."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TICKET_MEDIO = 60.0
META_ROAS = 4.0
ORCAMENTO_MENSAL = 45_000.0
DIAS = 30

CAMPANHAS = {
    # canal: (investimento mensal, cpm, ctr, taxa de conversao por clique)
    "Google Ads": {"investido": 18_000, "cpm": 14.0, "ctr": 0.045, "conv_clique": 0.055},
    "Meta Ads": {"investido": 14_000, "cpm": 9.5, "ctr": 0.022, "conv_clique": 0.048},
    "Email": {"investido": 6_000, "cpm": 30.0, "ctr": 0.040, "conv_clique": 0.060},
    "Influencer": {"investido": 9_500, "cpm": 26.0, "ctr": 0.013, "conv_clique": 0.031},
}

SEED = 320


def metricas_campanhas() -> pd.DataFrame:
    linhas = []
    for canal, cfg in CAMPANHAS.items():
        impressoes = cfg["investido"] / cfg["cpm"] * 1000
        cliques = impressoes * cfg["ctr"]
        conversoes = cliques * cfg["conv_clique"]

        linhas.append(
            {
                "canal": canal,
                "investido": cfg["investido"],
                "impressoes": int(impressoes),
                "cliques": int(cliques),
                "conversoes": int(conversoes),
                "ctr_pct": round(cfg["ctr"] * 100, 2),
                "cpc_rs": round(cfg["investido"] / max(cliques, 1), 2),
                "cpa_rs": round(cfg["investido"] / max(conversoes, 1), 2),
                "roas": round(conversoes * TICKET_MEDIO / cfg["investido"], 2),
            }
        )
    return pd.DataFrame(linhas).sort_values("roas", ascending=False)


def pacing_diario(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dias = np.arange(1, DIAS + 1)
    ideal = ORCAMENTO_MENSAL / DIAS * dias
    # gastos reais com aceleracao no fim de mes (empurra o pacing)
    gasto_acumulado = ideal * rng.normal(1, 0.04, DIAS).cumprod() ** 0 + rng.normal(0, 120, DIAS).cumsum()
    gasto_acumulado = np.clip(gasto_acumulado, None, None)
    return pd.DataFrame({"dia": dias, "ideal": ideal.round(0), "realizado": gasto_acumulado.round(0)})


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    campanhas = metricas_campanhas()

    print("=== DESEMPENHO POR CAMPANHA ===")
    print(campanhas.to_string(index=False))

    abaixo_meta = campanhas[campanhas["roas"] < META_ROAS]
    melhor = campanhas.iloc[0]
    print(
        f"\nMeta de ROAS: {META_ROAS}x | acima da meta: "
        f"{', '.join(campanhas.loc[campanhas['roas'] >= META_ROAS, 'canal']) or 'nenhuma'}"
    )
    print(f"Melhor ROAS: {melhor['canal']} ({melhor['roas']}x) com CPA R$ {melhor['cpa_rs']}")

    if not abaixo_meta.empty:
        pior = abaixo_meta.sort_values("roas").iloc[0]
        realocar = min(pior["investido"] * 0.3, 5_000)
        print(
            f"Sugestao: realocar R$ {realocar:,.0f} de '{pior['canal']}' "
            f"(ROAS {pior['roas']}x) para '{melhor['canal']}'"
        )

    pacing = pacing_diario()
    desvio_final = pacing.iloc[-1]["realizado"] - pacing.iloc[-1]["ideal"]
    ritmo = "acima" if desvio_final > 0 else "abaixo"
    print(
        f"\nPacing dia {DIAS}: R$ {pacing.iloc[-1]['realizado']:,.0f} gastos "
        f"({ritmo} do planejado em R$ {abs(desvio_final):,.0f})"
    )

    fig, eixos = plt.subplots(1, 3, figsize=(16.5, 4.4))
    eixos[0].barh(campanhas["canal"], campanhas["roas"], color="#7c3aed")
    eixos[0].axvline(META_ROAS, ls="--", color="black")
    eixos[0].set_title("ROAS por campanha (meta 4x)")
    eixos[1].scatter(campanhas["cpa_rs"], campanhas["roas"], s=campanhas["investido"] / 40, color="#2563eb", alpha=0.75)
    for _, linha in campanhas.iterrows():
        eixos[1].annotate(linha["canal"], (linha["cpa_rs"], linha["roas"]), fontsize=8)
    eixos[1].set_title("CPA x ROAS (bolha = investimento)")
    eixos[2].plot(pacing["dia"], pacing["ideal"], ls="--", label="ideal")
    eixos[2].plot(pacing["dia"], pacing["realizado"], label="realizado", lw=2)
    eixos[2].fill_between(pacing["dia"], pacing["ideal"], pacing["realizado"], alpha=0.15)
    eixos[2].set_title("Pacing do orcamento acumulado (R$)")
    eixos[2].legend()
    plt.tight_layout()
    plt.savefig("outputs/marketing_campanhas.png", dpi=120)

    pacing.to_csv("outputs/pacing_orcamento.csv", index=False)
    print("\nCSV e painel salvos em outputs/")
