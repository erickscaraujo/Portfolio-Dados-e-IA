"""Projecao de receita em 12 meses via Monte Carlo (10 mil cenarios)."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

CENARIOS = 10_000
MESES = 12
RECEITA_INICIAL = 850_000.0
CRESCIMENTO_MEDIA, CRESCIMENTO_DESVIO = 0.018, 0.012
SOBREVIVENCIA_MEDIA, SOBREVIVENCIA_DESVIO = 0.985, 0.008
META_ANUAL = 9_500_000.0

SEED = 101


def simular() -> np.ndarray:
    rng = np.random.default_rng(SEED)
    receita_atual = np.full(CENARIOS, RECEITA_INICIAL)

    # fator sazonal fixo por mes (natal forte, janeiro fraco) aplica a todos os cenarios
    sazonalidade = np.array([0.86, 0.9, 0.98, 1.0, 1.02, 1.04, 1.0, 0.98, 1.06, 1.08, 1.28, 1.32])
    trajetorias = np.empty((CENARIOS, MESES))

    for mes in range(MESES):
        crescimento = rng.normal(CRESCIMENTO_MEDIA, CRESCIMENTO_DESVIO, CENARIOS)
        sobrevivencia = np.clip(rng.normal(SOBREVIVENCIA_MEDIA, SOBREVIVENCIA_DESVIO, CENARIOS), 0.9, 1.0)
        choque_mercado = np.where(rng.random(CENARIOS) < 0.02, 0.82, 1.0)  # crise rara

        receita_atual *= (1 + crescimento) * sobrevivencia * choque_mercado * sazonalidade[mes]
        trajetorias[:, mes] = receita_atual

    return trajetorias


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    trajetorias = simular()
    acumulado = trajetorias.sum(axis=1)

    print("=== PROJECAO MENSAL (P5 / mediana / P95, R$ milhoes) ===")
    percentis_mes = np.percentile(trajetorias, [5, 50, 95], axis=0)
    for mes in range(0, MESES, 2):
        p5, p50, p95 = percentis_mes[:, mes] / 1e6
        print(f"mes {mes + 1:>2}: {p5:6.2f} | {p50:6.2f} | {p95:6.2f}")

    p5_ano, p50_ano, p95_ano = np.percentile(acumulado, [5, 50, 95]) / 1e6
    prob_meta = float((acumulado >= META_ANUAL).mean())
    print("\n=== ACUMULADO DO ANO ===")
    print(f"P5: R$ {p5_ano:.2f} mi | mediana: R$ {p50_ano:.2f} mi | P95: R$ {p95_ano:.2f} mi")
    print(f"Meta anual: R$ {META_ANUAL / 1e6:.2f} mi -> probabilidade de bater: {prob_meta:.1%}")

    risco_queda = float((acumulado < RECEITA_INICIAL * 12 * 0.95).mean())
    print(f"Cenario de queda vs ano anterior (>5%): {risco_queda:.1%} dos casos")

    fig, ax = plt.subplots(figsize=(10, 4.8))
    meses_eixo = np.arange(1, MESES + 1)
    ax.fill_between(
        meses_eixo, percentis_mes[0] / 1e6, percentis_mes[2] / 1e6, alpha=0.25, color="#2563eb", label="P5-P95"
    )
    ax.plot(meses_eixo, percentis_mes[1] / 1e6, color="#2563eb", lw=2.2, label="mediana")
    ax.axhline(RECEITA_INICIAL / 1e6, ls=":", color="gray", label="receita atual")
    ax.set_title("Fan chart da projecao de receita mensal")
    ax.set_xlabel("Mes do ano")
    ax.set_ylabel("R$ milhoes")
    ax.legend()
    plt.tight_layout()
    plt.savefig("outputs/monte_carlo_receita.png", dpi=120)

    plt.figure(figsize=(7.5, 4.2))
    plt.hist(acumulado / 1e6, bins=60, color="#059669", alpha=0.85)
    plt.axvline(META_ANUAL / 1e6, color="#dc2626", ls="--", label=f"meta ({META_ANUAL / 1e6:.1f} mi)")
    plt.title(f"Distribuicao da receita anual — {prob_meta:.0%} de chance de bater a meta")
    plt.xlabel("R$ milhoes")
    plt.legend()
    plt.tight_layout()
    plt.savefig("outputs/monte_carlo_distribuicao.png", dpi=120)

    print("\nGraficos salvos em outputs/ (fan chart + distribuicao)")
