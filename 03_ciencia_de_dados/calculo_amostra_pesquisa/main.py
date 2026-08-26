"""Planejamento amostral: n minimo, margem de erro e simulacao de pesquisa estratificada."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import matplotlib.pyplot as plt
import numpy as np

Z_95 = 1.96
POPULACAO = 50_000
TAXA_VERDADEIRA = 0.62
REGIOES = {"Sudeste": 0.44, "Sul": 0.20, "Nordeste": 0.26, "Centro-Oeste": 0.10}

SEED = 90


def n_minimo(margem: float, proporcao: float = 0.5, confianca_z: float = Z_95, populacao: int | None = None) -> int:
    """Correção de população finita reduz o n quando o universo é pequeno."""
    n_infinito = (confianca_z**2 * proporcao * (1 - proporcao)) / margem**2
    if populacao is None:
        return int(np.ceil(n_infinito))
    ajuste = n_infinito / (1 + (n_infinito - 1) / populacao)
    return int(np.ceil(ajuste))


def margem_de_erro(n: int, proporcao: float = 0.5, confianca_z: float = Z_95) -> float:
    return confianca_z * np.sqrt(proporcao * (1 - proporcao) / n)


def coleta_estratificada(rng: np.random.Generator, n_total: int) -> tuple[int, int]:
    """Alocação proporcional por regiao; devolve (favoraveis, total)."""
    favoraveis = 0
    for _, peso in REGIOES.items():
        cota = round(n_total * peso)
        # cada regiao tem humor proprio em torno da taxa verdadeira
        taxa_regiao = np.clip(TAXA_VERDADEIRA + rng.normal(0, 0.05), 0.3, 0.9)
        favoraveis += int(rng.binomial(cota, taxa_regiao))
    return favoraveis, n_total


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)

    print("=== N MINIMO POR MARGEM DE ERRO ===")
    for margem in (0.05, 0.04, 0.03, 0.02):
        infinito = n_minimo(margem, populacao=None)
        finito = n_minimo(margem, populacao=POPULACAO)
        print(
            f"- margem {margem:.0%}: {infinito:,} (populacao infinita) | {finito:,} (com correcao para {POPULACAO:,})"
        )

    n_escolhido = n_minimo(0.04, populacao=POPULACAO)
    margem_realizada = margem_de_erro(n_escolhido)
    print(f"\nEscolhido: n={n_escolhido} -> margem teorica de {margem_realizada:.2%}")

    print("\n=== SIMULACAO DA PESQUISA (estratificada proporcional) ===")
    favoraveis, total = coleta_estratificada(rng, n_escolhido)
    estimativa = favoraveis / total
    intervalo = (
        max(0, estimativa - margem_realizada),
        min(1, estimativa + margem_realizada),
    )
    print(f"Favoraveis na amostra: {favoraveis}/{total} = {estimativa:.1%}")
    print(f"Intervalo de confianca 95%: [{intervalo[0]:.1%}, {intervalo[1]:.1%}]")
    dentro = intervalo[0] <= TAXA_VERDADEIRA <= intervalo[1]
    print(f"Taxa verdadeira da populacao: {TAXA_VERDADEIRA:.1%} -> {'capturada pelo IC' if dentro else 'FORA do IC'}")

    margens = np.linspace(0.01, 0.08, 60)
    ns = [n_minimo(m, populacao=POPULACAO) for m in margens]
    plt.figure(figsize=(7.5, 4.2))
    plt.plot(margens * 100, ns, color="#2563eb", lw=2)
    plt.scatter([4], [n_escolhido], color="#dc2626", zorder=5, label=f"escolhido (n={n_escolhido})")
    plt.xlabel("Margem de erro (%)")
    plt.ylabel("Amostra necessaria")
    plt.title("Quanto custa cada ponto percentual de precisao")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/amostra_margem.png", dpi=120)
    print("\nCurva salva em outputs/amostra_margem.png")
