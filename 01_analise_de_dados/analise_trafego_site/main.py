"""Trafego do site: fontes, bounce, conversao e custo por aquisicao."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FONTES = {
    # fonte: (share das sessoes, conversao base, custo diario quando pago)
    "organico": {"share": 0.40, "conversao": 0.032, "custo_dia": 0},
    "pago": {"share": 0.25, "conversao": 0.048, "custo_dia": 900},
    "social": {"share": 0.20, "conversao": 0.014, "custo_dia": 120},
    "direto": {"share": 0.15, "conversao": 0.055, "custo_dia": 0},
}
PAGINAS = {
    "/": 0.38,
    "/produtos": 0.24,
    "/promocoes": 0.16,
    "/blog/guia-compras": 0.12,
    "/contato": 0.10,
}

DIAS = 30
SEED = 123


def gerar_sessoes() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    datas = pd.date_range("2025-05-01", periods=DIAS)

    linhas = []
    for fonte, cfg in FONTES.items():
        for dia, data in enumerate(datas):
            sessoes = int(3_400 * cfg["share"] * (1 + 0.008 * dia) * rng.normal(1, 0.09))
            fim_de_semana = data.dayofweek >= 5
            if fonte in ("organico", "direto"):
                sessoes = int(sessoes * (1.15 if fim_de_semana else 1.0))

            convertidos = int(rng.binomial(max(sessoes, 1), cfg["conversao"]))
            linhas.append({"data": data, "fonte": fonte, "sessoes": sessoes, "conversoes": convertidos})

    return pd.DataFrame(linhas)


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    trafego = gerar_sessoes()

    print("=== DESEMPENHO POR FONTE (30 dias) ===")
    resumo = trafego.groupby("fonte").agg(
        sessoes=("sessoes", "sum"),
        conversoes=("conversoes", "sum"),
    )
    resumo["conversao_pct"] = (resumo["conversoes"] / resumo["sessoes"] * 100).round(2)
    custo_total = {f: FONTES[f]["custo_dia"] * DIAS for f in FONTES}
    resumo["cpa_rs"] = [round(custo_total[f] / max(resumo.loc[f, "conversoes"], 1), 2) for f in resumo.index]
    print(resumo.sort_values("conversoes", ascending=False).to_string())

    ltv_simplificado = 240.0
    pago_cpa = resumo.loc["pago", "cpa_rs"]
    margem_canal_pago = ltv_simplificado - pago_cpa
    print(
        f"\nCanal pago: CPA R$ {pago_cpa:.2f} vs LTV R$ {ltv_simplificado:.2f} "
        f"-> {'VALE' if margem_canal_pago > 0 else 'NAO vale'} a pena "
        f"(margem R$ {margem_canal_pago:.2f}/cliente)"
    )

    rng = np.random.default_rng(SEED)
    bounce_paginas = (
        pd.Series(
            {
                pagina: float(np.clip(rng.normal(bounce_base, 0.03), 0.2, 0.75))
                for pagina, bounce_base in {
                    "/": 0.42,
                    "/produtos": 0.31,
                    "/promocoes": 0.27,
                    "/blog/guia-compras": 0.55,
                    "/contato": 0.22,
                }.items()
            }
        )
        .sort_values(ascending=False)
        .round(3)
    )
    print("\n=== BOUNCE RATE POR PAGINA ===")
    print((bounce_paginas * 100).round(1).to_string())

    melhor_dia = (
        trafego.assign(dia_semana=trafego["data"].dt.day_name())
        .groupby("dia_semana")["sessoes"]
        .mean()
        .sort_values(ascending=False)
    )
    print(f"\nDia mais forte da semana: {melhor_dia.index[0]}")

    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.3))
    pivot_diario = trafego.pivot_table(index="data", columns="fonte", values="sessoes")
    pivot_diario.plot.area(ax=eixos[0], stacked=True, alpha=0.85, legend=False)
    eixos[0].set_title("Sessoes por fonte")
    eixos[1].barh(resumo.index, resumo["conversao_pct"], color="#2563eb")
    eixos[1].set_title("Conversao por fonte (%)")
    eixos[2].barh(bounce_paginas.index[::-1], bounce_paginas.values[::-1] * 100, color="#b45309")
    eixos[2].set_title("Bounce rate por pagina (%)")
    plt.tight_layout()
    plt.savefig("outputs/trafego_site.png", dpi=120)

    print("\nPainel salvo em outputs/trafego_site.png")
