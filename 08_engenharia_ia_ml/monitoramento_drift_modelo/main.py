"""Monitoramento semanal de drift de dados e do score do modelo em producao."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from metricas import psi, score_modelo, status_do_drift, teste_ks

SEMANAS = 8
LIMIAR_CRITICO_CONSECUTIVO = 2


def simular_producao(seed: int = 4) -> list[dict]:
    """Renda da base de treino vs semanas com piora economica gradual."""
    rng = np.random.default_rng(seed)
    treino_renda = rng.lognormal(8.2, 0.45, 8_000)

    historico = []
    for semana in range(1, SEMANAS + 1):
        # a cada semana a renda media da carteira cai ~4% (contexto de crise)
        drift = 0.04 * (semana - 1)
        renda_semana = rng.lognormal(8.2, 0.5 + 0.02 * semana, 2_000) / (1 + drift)

        probas = score_modelo(renda_semana, drift)
        estat_ks, p_ks = teste_ks(treino_renda, renda_semana)

        historico.append(
            {
                "semana": semana,
                "psi_renda": round(psi(treino_renda, renda_semana), 3),
                "ks_estatistica": round(estat_ks, 3),
                "ks_pvalor": round(p_ks, 4),
                "score_medio": round(float(probas.mean()), 4),
                "taxa_aprovacao": round(float((probas < 0.40).mean()), 4),
            }
        )
    return historico


def gerar_relatorio(historico: list[dict]) -> None:
    df = pd.DataFrame(historico)
    df["status"] = df["psi_renda"].map(status_do_drift)

    print("=== MONITORAMENTO SEMANAL DO MODELO ===")
    print(df.to_string(index=False))

    criticos_consecutivos = 0
    decisao = "manter modelo atual"
    for linha in df.itertuples():
        criticos_consecutivos = criticos_consecutivos + 1 if linha.status == "critico" else 0
        if criticos_consecutivos >= LIMIAR_CRITICO_CONSECUTIVO:
            decisao = f"RETREINAR: {criticos_consecutivos} semanas criticas consecutivas (semana {linha.semana})"
            break
    print(f"\nDECISAO: {decisao}")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.axhspan(0, 0.10, color="#dcfce7", alpha=0.6)
    ax.axhspan(0.10, 0.25, color="#fef9c3", alpha=0.6)
    ax.axhspan(0.25, max(0.5, df["psi_renda"].max() * 1.1), color="#fee2e2", alpha=0.6)
    ax.plot(df["semana"], df["psi_renda"], marker="o", color="#b91c1c", lw=2, label="PSI renda")
    ax.set_xticks(df["semana"])
    ax.set_xlabel("Semana")
    ax.set_ylabel("PSI")
    ax.set_title("Drift da feature renda por semana")
    ax.text(
        0.99,
        0.05,
        "verde: estavel | amarelo: alerta | vermelho: critico",
        transform=ax.transAxes,
        ha="right",
        fontsize=8,
        color="#374151",
    )
    plt.tight_layout()
    plt.savefig("outputs/monitoramento_psi.png", dpi=120)
    print("\nGrafico salvo em outputs/monitoramento_psi.png")


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)
    gerar_relatorio(simular_producao())
