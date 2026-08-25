"""NPS detalhado: evolucao mensal, regioes e drivers de nota."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def calcular_nps(notas: pd.Series) -> float:
    promotores = (notas >= 9).mean()
    detratores = (notas <= 6).mean()
    return (promotores - detratores) * 100


def gerar_respostas(n: int = 3_000, seed: int = 81) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    meses = rng.integers(0, 12, n)
    regioes = rng.choice(["Sudeste", "Sul", "Nordeste", "Centro-Oeste"], n)

    # tempo de resposta piora a nota; regioes tem bases distintas
    tempo_atendimento_horas = rng.exponential(14, n).round(1)
    ajuste_regiao = (
        pd.Series(regioes).map({"Sudeste": 0.3, "Sul": 0.5, "Nordeste": -0.2, "Centro-Oeste": 0.1}).to_numpy()
    )
    notas = (
        np.clip(
            8.4 - 0.09 * tempo_atendimento_horas.clip(0, 48) + ajuste_regiao + rng.normal(0, 1.6, n),
            0,
            10,
        )
        .round(0)
        .astype(int)
    )
    # tendencia de melhora ao longo do ano
    notas = np.clip(notas + (meses // 4), 0, 10)

    return pd.DataFrame(
        {
            "mes": meses,
            "regiao": regioes,
            "tempo_h": tempo_atendimento_horas,
            "nota": notas,
        }
    )


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    respostas = gerar_respostas()

    print("=== NPS GERAL ===")
    nps_geral = calcular_nps(respostas["nota"])
    promotores = (respostas["nota"] >= 9).mean() * 100
    neutros = respostas["nota"].between(7, 8).mean() * 100
    detratores = (respostas["nota"] <= 6).mean() * 100
    print(
        f"NPS: {nps_geral:+.0f} | promotores {promotores:.0f}% | neutros {neutros:.0f}% | detratores {detratores:.0f}%"
    )

    print("\n=== NPS POR MES (evolucao) ===")
    por_mes = respostas.groupby("mes")["nota"].apply(calcular_nps).round(0).astype(int)
    print(por_mes.to_string())

    print("\n=== NPS POR REGIAO ===")
    por_regiao = (
        respostas.groupby("regiao")["nota"].apply(calcular_nps).sort_values(ascending=False).round(0).astype(int)
    )
    print(por_regiao.to_string())

    faixas = pd.cut(respostas["tempo_h"], bins=[0, 6, 24, 72, np.inf], labels=["ate 6h", "6-24h", "24-72h", "72h+"])
    nps_por_espera = respostas.groupby(faixas, observed=True)["nota"].apply(calcular_nps).round(0).astype(int)
    print("\n=== NPS POR TEMPO DE ATENDIMENTO (driver) ===")
    print(nps_por_espera.to_string())
    correlacao = respostas[["tempo_h", "nota"]].corr().iloc[0, 1]
    print(f"Correlacao tempo x nota: {correlacao:.2f}")

    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.2))
    por_mes.plot(ax=eixos[0], marker="o", color="#2563eb")
    eixos[0].set_title("NPS por mes")
    eixos[1].axhline(nps_geral, ls="--", color="gray")
    por_regiao.plot.barh(ax=eixos[1], color="#7c3aed")
    eixos[1].set_title("NPS por regiao")
    nps_por_espera.plot.bar(ax=eixos[2], color="#b45309")
    eixos[2].set_title("NPS por tempo de atendimento")
    plt.tight_layout()
    plt.savefig("outputs/nps_experiencia.png", dpi=120)

    print("\nPainel salvo em outputs/nps_experiencia.png")
