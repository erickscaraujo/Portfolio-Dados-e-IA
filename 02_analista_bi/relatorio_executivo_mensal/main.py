"""Fechamento mensal por filial: consolida indicadores e exporta o Excel da diretoria."""

import pathlib

import numpy as np
import pandas as pd
from excel import exportar

FILIAIS = ["SP", "RJ", "MG", "RS", "BA"]


def gerar_fechamento(meses: int = 18, seed: int = 2024) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    periodo = pd.period_range("2024-03", periods=meses, freq="M").astype(str)
    linhas = []
    for mes in periodo:
        for filial in FILIAIS:
            porte = {"SP": 1.6, "RJ": 1.2, "MG": 1.0, "RS": 0.8, "BA": 0.6}[filial]
            receita = rng.normal(500_000, 70_000) * porte
            meta = rng.normal(510_000, 40_000) * porte
            linhas.append(
                {
                    "mes": mes,
                    "filial": filial,
                    "receita": max(receita, 80_000),
                    "meta": max(meta, 80_000),
                    "despesas": receita * rng.normal(0.72, 0.03),
                    "nps": int(np.clip(rng.normal(62, 12), 0, 100)),
                }
            )
    return pd.DataFrame(linhas)


def montar_resumo(base: pd.DataFrame) -> pd.DataFrame:
    """Atingimento com folga de 2% sobre a meta, pratica adotada pela diretoria."""
    resumo = base.groupby("filial").agg(
        receita_total=("receita", "sum"),
        meta_total=("meta", "sum"),
        margem_pct=("receita", lambda r: 1 - base.loc[r.index, "despesas"].sum() / r.sum()),
        nps_medio=("nps", "mean"),
    )
    resumo["atingimento"] = resumo["receita_total"] / (resumo["meta_total"] * 0.98)
    resumo["status"] = np.where(resumo["atingimento"] >= 1, "meta batida", "abaixo da meta")
    return resumo.reset_index()


def montar_detalhe(base: pd.DataFrame) -> pd.DataFrame:
    detalhe = base.copy()
    detalhe["resultado"] = detalhe["receita"] - detalhe["despesas"]
    detalhe["atingimento"] = detalhe["receita"] / (detalhe["meta"] * 0.98)
    return detalhe.sort_values(["mes", "filial"])


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    fechamento = gerar_fechamento()
    resumo = montar_resumo(fechamento)
    detalhe = montar_detalhe(fechamento)

    caminho = exportar(resumo, detalhe)

    print("=== RESUMO POR FILIAL ===")
    print(
        resumo[["filial", "receita_total", "atingimento", "margem_pct", "nps_medio", "status"]].to_string(
            index=False, float_format=lambda x: f"{x:,.2f}"
        )
    )

    piores = detalhe.nsmallest(3, "atingimento")[["mes", "filial", "atingimento"]]
    print("\nPontos de atencao (meses mais criticos):")
    for _, linha in piores.iterrows():
        print(f"- {linha['mes']} | {linha['filial']}: {linha['atingimento']:.0%} da meta")

    print(f"\nArquivo gerado: {caminho}")
