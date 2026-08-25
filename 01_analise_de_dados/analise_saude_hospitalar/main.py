"""Analise hospitalar: permanencia, reinternacao e tempo de espera por especialidade."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ESPECIALIDADES = {
    "Clinica Geral": {"permanencia_media": 3.2, "peso": 0.38, "reinternacao_base": 0.09},
    "Cardiologia": {"permanencia_media": 5.1, "peso": 0.22, "reinternacao_base": 0.14},
    "Ortopedia": {"permanencia_media": 4.0, "peso": 0.20, "reinternacao_base": 0.07},
    "Pediatria": {"permanencia_media": 2.6, "peso": 0.20, "reinternacao_base": 0.05},
}

LEITOS = 120
SEED = 19


def gerar_internacoes(n: int = 2_400) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    nomes = list(ESPECIALIDADES)

    especialidade = rng.choice(nomes, size=n, p=[ESPECIALIDADES[e]["peso"] for e in nomes])
    entrada = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 360, n), unit="D")

    medias = pd.Series(especialidade).map({e: v["permanencia_media"] for e, v in ESPECIALIDADES.items()}).to_numpy()
    permanencia = np.clip(rng.exponential(medias), 1, None).round().astype(int)

    base_reint = pd.Series(especialidade).map({e: v["reinternacao_base"] for e, v in ESPECIALIDADES.items()}).to_numpy()
    # permanencias longas elevam a chance de volta ao hospital em ate 30 dias
    reinternou = rng.random(n) < (base_reint * (1 + permanencia / 12))

    espera_horas = np.clip(rng.gamma(2.0, 4.5, n), 0.5, None).round(1)

    return pd.DataFrame(
        {
            "entrada": entrada,
            "especialidade": especialidade,
            "dias_permanencia": permanencia,
            "reinternou_30d": reinternou,
            "espera_horas": espera_horas,
        }
    )


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_internacoes()

    print("=== INDICADORES POR ESPECIALIDADE ===")
    resumo = (
        base.groupby("especialidade")
        .agg(
            internacoes=("dias_permanencia", "count"),
            permanencia_media=("dias_permanencia", "mean"),
            p90_espera_h=("espera_horas", lambda s: s.quantile(0.9)),
            reinternacao_pct=("reinternou_30d", lambda s: s.mean() * 100),
        )
        .round(1)
    )
    print(resumo.sort_values("internacoes", ascending=False).to_string())

    ocupacao_media = base.groupby("entrada").size().mean()
    taxa_ocupacao = ocupacao_media / LEITOS
    print(f"\nOcupacao media estimada: {ocupacao_media:.0f} pacientes/dia ({taxa_ocupacao:.0%} de {LEITOS} leitos)")

    pior_espera = resumo["p90_espera_h"].idxmax()
    print(f"P90 de espera mais critico: {pior_espera} ({resumo.loc[pior_espera, 'p90_espera_h']}h)")

    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.3))
    dados_box = [base.loc[base["especialidade"] == e, "dias_permanencia"] for e in ESPECIALIDADES]
    eixos[0].boxplot(dados_box, tick_labels=list(ESPECIALIDADES), showfliers=False)
    eixos[0].set_title("Permanencia por especialidade (dias)")
    resumo["reinternacao_pct"].sort_values().plot.barh(ax=eixos[1], color="#be123c")
    eixos[1].set_title("Reinternacao em 30d (%)")
    eixos[2].hist(base["espera_horas"], bins=40, color="#0e7490", alpha=0.85)
    eixos[2].axvline(base["espera_horas"].quantile(0.9), ls="--", color="black")
    eixos[2].set_title("Espera para internacao (horas)")
    plt.tight_layout()
    plt.savefig("outputs/saude_hospitalar.png", dpi=120)

    print("\nPainel salvo em outputs/saude_hospitalar.png")
