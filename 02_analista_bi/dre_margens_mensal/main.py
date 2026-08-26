"""DRE simplificada mes a mes: margens e comparacao ano contra ano."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

IMPOSTO_SOBRE_VENDA = 0.12
CMV_PROPORCAO = 0.44
DESPESA_FIXA_MENSAL = 210_000
MARKETING_PROPORCAO = 0.07

SEED = 63


def gerar_receita(meses: int = 24) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    periodo = pd.period_range("2024-01", periods=meses, freq="M").astype(str)
    receitas = []
    for i, mes in enumerate(periodo):
        crescimento = 1 + 0.011 * i
        sazonal = 1.3 if mes.endswith(("11", "12")) else (0.85 if mes.endswith(("01", "02")) else 1.0)
        receitas.append(780_000 * crescimento * sazonal * rng.normal(1, 0.05))
    return pd.DataFrame({"mes": periodo, "receita_bruta": np.round(receitas, 2)})


def montar_dre(base: pd.DataFrame) -> pd.DataFrame:
    dre = base.copy()
    dre["impostos"] = -(dre["receita_bruta"] * IMPOSTO_SOBRE_VENDA)
    dre["receita_liquida"] = dre["receita_bruta"] + dre["impostos"]
    dre["cmv"] = -(dre["receita_liquida"] * CMV_PROPORCAO)
    dre["margem_bruta_rs"] = dre["receita_liquida"] + dre["cmv"]
    dre["marketing"] = -(dre["receita_liquida"] * MARKETING_PROPORCAO)
    dre["despesas_fixas"] = -DESPESA_FIXA_MENSAL
    dre["ebitda_rs"] = dre["margem_bruta_rs"] + dre["marketing"] + dre["despesas_fixas"]
    dre["imposto_lucro"] = -(dre["ebitda_rs"].clip(lower=0) * 0.34)

    dre["margem_bruta_pct"] = dre["margem_bruta_rs"] / dre["receita_liquida"]
    dre["margem_ebitda_pct"] = dre["ebitda_rs"] / dre["receita_liquida"]
    return dre


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    dre = montar_dre(gerar_receita())

    print("=== DRE CONSOLIDADA POR ANO ===")
    consolidado = (
        dre.assign(ano=dre["mes"].str[:4]).groupby("ano")[["receita_liquida", "margem_bruta_rs", "ebitda_rs"]].sum()
    )
    consolidado["margem_ebitda_pct"] = (consolidado["ebitda_rs"] / consolidado["receita_liquida"] * 100).round(1)
    print(consolidado.round(2).to_string(float_format=lambda x: f"{x:,.0f}"))

    crescimento = consolidado["receita_liquida"].iloc[-1] / consolidado["receita_liquida"].iloc[0] - 1
    print(f"\nCrescimento de receita liquida no periodo: {crescimento:+.1%}")

    ultimo = dre.iloc[-1]
    print(f"\n=== ULTIMO MES ({ultimo['mes']}) ===")
    for linha in ("receita_bruta", "impostos", "cmv", "marketing", "despesas_fixas", "ebitda_rs"):
        valor = ultimo[linha]
        print(f"- {linha:<15} R$ {valor:>12,.2f}")
    print(f"- margem EBITDA   : {ultimo['margem_ebitda_pct']:.1%}")

    fig, eixos = plt.subplots(1, 2, figsize=(14, 4.5))
    linhas_custo = ["impostos", "cmv", "marketing", "despesas_fixas"]
    eixos[0].bar(
        linhas_custo, [abs(ultimo[c]) for c in linhas_custo], color=["#94a3b8", "#dc2626", "#f59e0b", "#64748b"]
    )
    eixos[0].set_title(f"Estrutura de custos — {ultimo['mes']}")
    eixos[0].set_ylabel("R$ (absoluto)")
    plt.setp(eixos[0].get_xticklabels(), rotation=20)
    dre.plot(x="mes", y=["margem_bruta_pct", "margem_ebitda_pct"], ax=eixos[1], marker="o")
    eixos[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    eixos[1].set_title("Evolucao das margens")
    plt.setp(eixos[1].get_xticklabels()[::4], visible=False)
    plt.tight_layout()
    plt.savefig("outputs/dre_margens.png", dpi=120)

    dre.to_csv("outputs/dre_mensal.csv", index=False)
    print("\nArtefatos salvos em outputs/ (PNG + CSV)")
