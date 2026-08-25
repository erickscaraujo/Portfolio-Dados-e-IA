"""Analise de teste A/B de um checkout: simulacao, inferencia e decisao de negocio."""

import numpy as np
from estatistica import (
    intervalo_confianca,
    p_valor_bilateral,
    poder_estatistico,
    tamanho_amostral,
    taxa_conversao,
    z_estatistica,
)

ALPHA = 0.05
PODER_ALVO = 0.80
MDE = 0.015  # lift minimo que vale o esforco de implantacao


def simular_experimento(n_por_grupo: int, p_controle: float = 0.104, seed: int = 99) -> dict:
    rng = np.random.default_rng(seed)
    conv_a = int(rng.binomial(n_por_grupo, p_controle))
    # versao nova com checkout em uma etapa: efeito real de +1.5 p.p.
    conv_b = int(rng.binomial(n_por_grupo, p_controle + 0.015))
    return {"conv_a": conv_a, "conv_b": conv_b, "n": n_por_grupo}


def main() -> None:
    exp = simular_experimento(5_200)

    tx_a = taxa_conversao(exp["conv_a"], exp["n"])
    tx_b = taxa_conversao(exp["conv_b"], exp["n"])

    ic_a = intervalo_confianca(exp["conv_a"], exp["n"])
    ic_b = intervalo_confianca(exp["conv_b"], exp["n"])

    z = z_estatistica(exp["conv_a"], exp["n"], exp["conv_b"], exp["n"])
    p_valor = p_valor_bilateral(z)

    n_necessario = tamanho_amostral(tx_a, MDE, ALPHA, PODER_ALVO)
    poder_real = poder_estatistico(0.104, 0.119, exp["n"], ALPHA)

    print("=== TESTE A/B — CHECKOUT EM UMA ETAPA ===")
    print(f"\nControle : {exp['conv_a']}/{exp['n']} = {tx_a:.2%} (IC95 {ic_a[0]:.2%} a {ic_a[1]:.2%})")
    print(f"Variacao : {exp['conv_b']}/{exp['n']} = {tx_b:.2%} (IC95 {ic_b[0]:.2%} a {ic_b[1]:.2%})")
    print(f"\nLift absoluto   : {(tx_b - tx_a) * 100:+.2f} p.p.")
    print(f"Lift relativo   : {tx_b / tx_a - 1:+.2%}")
    print(f"Estatistica z   : {z:.3f}")
    print(f"p-valor         : {p_valor:.4f}")

    significativo = p_valor < ALPHA
    print(f"\nSignificancia (alpha={ALPHA}): {'SIM' if significativo else 'NAO'}")

    print("\n=== SANIDADE DO EXPERIMENTO ===")
    status_amostra = "suficiente" if exp["n"] >= n_necessario else "insuficiente"
    print(f"- N por grupo: {exp['n']} | necessario para MDE de {MDE:.1%}: {n_necessario} ({status_amostra})")
    print(f"- Poder estatistico no cenario real: {poder_real:.1%}")

    if significativo and tx_b > tx_a:
        receita_extra_anual = exp["n"] * (tx_b - tx_a) * 12 * 180  # ticket medio R$ 180
        decisao = (
            f"IMPLANTAR: ganho de {(tx_b - tx_a) * 100:.1f} p.p. com significancia "
            f"estatistica. Impacto estimado de R$ {receita_extra_anual:,.0f}/ano no volume testado."
        )
    elif not significativo:
        decisao = "CONTINUAR O TESTE: resultado ainda nao distingue ruido de efeito real."
    else:
        decisao = "REVISAR: variacao performou abaixo do controle."

    print(f"\nDECISAO: {decisao}")


if __name__ == "__main__":
    main()
