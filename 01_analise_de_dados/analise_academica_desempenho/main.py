"""Desempenho academico: notas, frequencia e fatores de aprovacao."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MATERIAS = {"Matematica": -0.6, "Portugues": 0.0, "Historia": 0.4, "Ciencias": -0.2}
N_ALUNOS = 600
SEED = 112


def gerar_alunos() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    horas_estudo = np.clip(rng.gamma(2.5, 3.0, N_ALUNOS), 1, 25).round(1)
    frequencia = np.clip(rng.normal(84, 11, N_ALUNOS), 40, 100).round(1)

    base = 5.0 + 0.16 * horas_estudo + rng.normal(0, 0.9, N_ALUNOS)
    registros = []
    for i in range(N_ALUNOS):
        for materia, dificuldade in MATERIAS.items():
            nota = np.clip(base[i] + dificuldade + rng.normal(0, 0.7), 0, 10).round(1)
            registros.append(
                {
                    "aluno": i,
                    "materia": materia,
                    "nota": nota,
                    "horas_estudo": horas_estudo[i],
                    "frequencia": frequencia[i],
                }
            )

    return pd.DataFrame(registros)


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    notas = gerar_alunos()
    medias = (
        notas.groupby("aluno")
        .agg(
            media=("nota", "mean"),
            frequencia=("frequencia", "first"),
            horas_estudo=("horas_estudo", "first"),
        )
        .reset_index()
    )
    medias["aprovado"] = (medias["media"] >= 6) & (medias["frequencia"] >= 75)

    print("=== MEDIA POR MATERIA ===")
    por_materia = notas.groupby("materia")["nota"].mean().sort_values(ascending=False)
    print(por_materia.round(2).to_string())

    taxa_aprovacao = medias["aprovado"].mean()
    print(f"\nAprovacao geral: {taxa_aprovacao:.1%}")

    print("\n=== APROVACAO POR HORAS SEMANAIS DE ESTUDO ===")
    faixas_horas = pd.cut(medias["horas_estudo"], bins=[0, 5, 10, 15, 30], labels=["1-5h", "5-10h", "10-15h", "15h+"])
    aprovacao_por_faixa = (
        medias.assign(faixa=faixas_horas).groupby("faixa", observed=True)["aprovado"].mean() * 100
    ).round(1)
    print(aprovacao_por_faixa.to_string())

    reprovados_por_falta = ((medias["media"] >= 6) & (~medias["aprovado"])).sum()
    correlacoes = medias[["horas_estudo", "frequencia", "media"]].corr()["media"].drop("media")
    print(f"\nCorrelacao com a media: {correlacoes.round(2).to_dict()}")
    reprovados_falta = int(reprovados_por_falta)
    print(f"Reprovados somente por falta (media ok, frequencia <75%): {reprovados_falta}")

    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.3))
    medias["media"].plot.hist(bins=24, ax=eixos[0], color="#2563eb", alpha=0.85)
    eixos[0].axvline(6, ls="--", color="black")
    eixos[0].set_title("Distribuicao das medias")
    aprovacao_por_faixa.plot.bar(ax=eixos[1], color="#059669")
    eixos[1].set_title("Aprovacao (%) por horas de estudo")
    cores = np.where(medias["aprovado"], "#16a34a", "#dc2626")
    eixos[2].scatter(medias["frequencia"], medias["media"], c=cores, s=9, alpha=0.45)
    eixos[2].axvline(75, ls="--", color="gray")
    eixos[2].axhline(6, ls="--", color="gray")
    eixos[2].set_title("Frequencia x media (verde = aprovado)")
    plt.tight_layout()
    plt.savefig("outputs/desempenho_academico.png", dpi=120)

    with open("outputs/resumo_academico.md", "w", encoding="utf-8") as arq:
        arq.write(
            f"# Desempenho academico\n\n- Aprovacao geral: **{taxa_aprovacao:.1%}**\n"
            f"- Materia mais dificil: **{por_materia.index[-1]}** ({por_materia.iloc[-1]:.2f})\n"
            f"- Reprovados apenas por falta: **{reprovados_falta}**\n"
        )

    print("\nArtefatos salvos em outputs/")
