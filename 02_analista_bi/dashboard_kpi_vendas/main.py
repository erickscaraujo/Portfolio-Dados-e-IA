"""Dashboard comercial: calcula KPIs contra metas e publica um dashboard HTML estatico."""

import pathlib

import numpy as np
import pandas as pd
from dashboard import montar_html, salvar_dashboard


def gerar_base(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    meses = list(pd.period_range("2024-01", "2025-12", freq="M").astype(str))
    filiais = ["SP", "RJ", "MG", "RS"]
    registros = []
    for mes in meses:
        for filial in filiais:
            receita = rng.normal(420_000, 60_000)
            # crescimento organico ao longo do periodo
            idx = meses.index(mes)
            receita *= 1 + idx * 0.006
            registros.append(
                {
                    "mes": mes,
                    "filial": filial,
                    "receita": max(receita, 50_000),
                    "meta": 430_000 * (1 + idx * 0.005),
                    "pedidos": int(rng.normal(1_150, 130)),
                    "margem": rng.normal(0.39, 0.02),
                }
            )
    return pd.DataFrame(registros)


def calcular_kpis(base: pd.DataFrame) -> tuple[dict, list[dict]]:
    ano_atual = base[base["mes"].str.startswith("2025")]
    ano_anterior = base[base["mes"].str.startswith("2024")]

    fat = ano_atual["receita"].sum()
    meta = ano_atual["meta"].sum()
    ticket = fat / ano_atual["pedidos"].sum()
    ticket_ant = ano_anterior["receita"].sum() / ano_anterior["pedidos"].sum()
    margem = ano_atual["margem"].mean()

    kpis = {
        "faturamento": f"R$ {fat / 1e6:.2f} mi",
        "vs_meta": f"{fat / meta:.0%}",
        "meta_atingida": fat >= meta,
        "ticket_medio": f"R$ {ticket:,.2f}",
        "ticket_delta": f"{ticket / ticket_ant - 1:+.1%}",
        "ticket_ok": ticket >= ticket_ant,
        "pedidos": f"{ano_atual['pedidos'].sum():,}",
        "pedidos_delta": f"{ano_atual['pedidos'].sum() / ano_anterior['pedidos'].sum() - 1:+.1%}",
        "pedidos_ok": ano_atual["pedidos"].sum() >= ano_anterior["pedidos"].sum(),
        "margem": f"{margem:.1%}",
        "margem_ok": margem >= 0.38,
    }

    mensal_grp = ano_atual.groupby("mes").agg(receita=("receita", "sum"), meta=("meta", "sum"))
    mensal_grp["crescimento"] = mensal_grp["receita"].pct_change()
    tabela = []
    for mes, linha in mensal_grp.iterrows():
        pct = linha["receita"] / linha["meta"] * 100
        cresc = linha["crescimento"]
        tabela.append(
            {
                "mes": mes,
                "receita": f"R$ {linha['receita'] / 1000:,.0f}k",
                "meta": f"R$ {linha['meta'] / 1000:,.0f}k",
                "atingido": f"{pct:.0f}%",
                "pct": pct,
                "crescimento": "—" if pd.isna(cresc) else f"{cresc:+.1%}",
            }
        )
    return kpis, tabela


def destaques_filiais(base: pd.DataFrame) -> None:
    print("\n=== DESEMPENHO POR FILIAL (2025) ===")
    atual = base[base["mes"].str.startswith("2025")]
    resumo = atual.groupby("filial").agg(
        receita=("receita", "sum"),
        atingimento=("receita", "sum"),
    )
    metas = atual.groupby("filial")["meta"].sum()
    resumo["atingimento"] = resumo["receita"] / metas
    print(resumo.sort_values("receita", ascending=False).to_string(float_format=lambda x: f"{x:,.2f}"))


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_base()
    kpis, tabela_mensal = calcular_kpis(base)

    caminho = salvar_dashboard(montar_html(kpis, tabela_mensal))
    print(f"Dashboard gerado em {caminho}")
    print("\n=== KPIs DO ANO ===")
    for chave in ("faturamento", "ticket_medio", "pedidos", "margem"):
        print(f"- {chave.replace('_', ' ').title()}: {kpis[chave]}")

    destaques_filiais(base)
