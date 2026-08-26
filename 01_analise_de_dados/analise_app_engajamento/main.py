"""Engajamento do app: DAU/WAU, stickiness e retencao por cohort de instalacao."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIAS = 90
SEED = 71


def gerar_atividade(n_usuarios: int = 2_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    dia_instalacao = rng.integers(0, DIAS - 7, n_usuarios)
    # aderencia latente: poucos viciados, maioria esporadica
    aderencia = rng.beta(1.2, 4.0, n_usuarios)

    registros = []
    for usuario in range(n_usuarios):
        for offset in range(0, min(DIAS - dia_instalacao[usuario], 60)):
            proba = (
                aderencia[usuario] * np.exp(-0.12 * offset) * (1 + 0.3 * ((dia_instalacao[usuario] + offset) % 7 == 0))
            )
            if rng.random() < proba:
                registros.append(
                    {
                        "usuario": usuario,
                        "dia": int(dia_instalacao[usuario] + offset),
                        "offset": offset,
                    }
                )
    return pd.DataFrame(registros)


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    atividade = gerar_atividade()

    dau = atividade.groupby("dia")["usuario"].nunique()
    wau = atividade.groupby(atividade["dia"] // 7)["usuario"].nunique()
    stickiness = (dau.groupby(dau.index // 7).mean() / wau).dropna()

    print("=== DAU POR SEMANA ===")
    print(f"media DAU semanal : {[f'{v:.0f}' for v in dau.groupby(dau.index // 7).mean()]}")
    print(f"WAU por semana    : {[f'{v:.0f}' for v in wau]}")
    print(f"Stickiness DAU/WAU: {[f'{v:.0%}' for v in stickiness]}")

    print("\n=== RETENCAO MEDIA POR OFFSET ===")
    instalados_por_dia = pd.Series(1, index=range(DIAS)).groupby(lambda d: d).size()
    retencao_linhas = []
    for offset in (1, 7, 30):
        cohort_base = atividade[atividade["offset"] == 0].groupby("dia").size()
        voltaram = (
            atividade[atividade["offset"] == offset]
            .groupby("dia")["usuario"]
            .nunique()
            .reindex(cohort_base.index, fill_value=0)
        )
        # so cohorts que ja tiveram tempo de voltar contam na media
        elegiveis = cohort_base[cohort_base.index <= DIAS - 1 - offset]
        taxa = voltaram[elegiveis.index].sum() / elegiveis.sum()
        retencao_linhas.append({"offset": f"D{offset}", "retencao_pct": round(taxa * 100, 1)})
        print(f"- D{offset}: {taxa:.1%}")

    fig, eixos = plt.subplots(1, 2, figsize=(13, 4.3))
    dau.plot(ax=eixos[0], color="#2563eb", label="DAU")
    wau_reindexado = wau.set_axis(wau.index * 7)
    wau_reindexado.plot(ax=eixos[0], color="#9333ea", ls="--", label="WAU")
    eixos[0].set_title("Usuarios ativos")
    eixos[0].legend()
    offsets = [r["offset"] for r in retencao_linhas]
    valores = [r["retencao_pct"] for r in retencao_linhas]
    eixos[1].bar(offsets, valores, color="#059669")
    for i, valor in enumerate(valores):
        eixos[1].text(i, valor + 0.5, f"{valor}%", ha="center", fontsize=9)
    eixos[1].set_title("Retencao media (%)")
    plt.tight_layout()
    plt.savefig("outputs/engajamento_app.png", dpi=120)

    print("\nPainel salvo em outputs/engajamento_app.png")
