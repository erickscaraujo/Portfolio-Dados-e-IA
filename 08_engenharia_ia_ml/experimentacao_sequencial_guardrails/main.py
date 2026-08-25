"""Peeking em teste A/B: quantos falsos positivos a ansiedade custa?"""

import numpy as np
from scipy import stats

EXPERIMENTOS_COM_EFETIVO = 1_500
N_POR_GRUPO = 4_000
LOTE = 500
TAXA_BASE = 0.10
ALPHA = 0.05
LIMITE_LATENCIA_MS = 250.0


def rodar_experimento(rng: np.random.Generator, efeito_real: float, latencia_desafiador_ms: float) -> dict:
    """H0 verdadeira quando efeito_real=0; guarda o veredito de cada estrategia."""
    if latencia_desafiador_ms > LIMITE_LATENCIA_MS:
        # guardrail operacional: nem comeca a valer, aborta antes de olhar p-valor
        return {"horizon_fixo": False, "peeking": False, "guardrail_abortou": True}

    conversoes_a = conversoes_b = 0
    decisao_peeking = False

    for lote in range(1, N_POR_GRUPO // LOTE + 1):
        conversoes_a += int(rng.binomial(LOTE, TAXA_BASE))
        conversoes_b += int(rng.binomial(LOTE, TAXA_BASE + efeito_real))

        n_atual = lote * LOTE
        p_pool = (conversoes_a + conversoes_b) / (2 * n_atual)
        erro_padrao = np.sqrt(p_pool * (1 - p_pool) * (2 / n_atual))
        z = ((conversoes_b - conversoes_a) / n_atual) / max(erro_padrao, 1e-12)
        significativo = 1 - stats.norm.cdf(abs(z)) < ALPHA / 2

        if lote == N_POR_GRUPO // LOTE:
            return {
                "horizon_fixo": significativo,
                "peeking": decisao_peeking or significativo,
                "guardrail_abortou": False,
            }
        if significativo and not decisao_peeking:
            # pratica errada comum: para no primeiro p<0.05 que aparece
            decisao_peeking = True

    raise AssertionError("nao deveria chegar aqui")


def main() -> None:
    rng = np.random.default_rng(240)

    falsos_fixo = falsos_peeking = abortados_guardrail = executados = 0
    for i in range(EXPERIMENTOS_COM_EFETIVO):
        # metade dos desafiadores tem problema de performance
        latencia = 260.0 if i % 2 == 0 else 235.0
        resultado = rodar_experimento(rng, efeito_real=0.0, latencia_desafiador_ms=latencia)

        if resultado["guardrail_abortou"]:
            abortados_guardrail += 1
            continue
        executados += 1
        falsos_fixo += resultado["horizon_fixo"]
        falsos_peeking += resultado["peeking"]

    print(f"=== {EXPERIMENTOS_COM_EFETIVO} experimentos SEM efeito real (H0 verdadeira) ===")
    print(f"- abortados pelo guardrail de latencia (> {LIMITE_LATENCIA_MS:.0f}ms): {abortados_guardrail}")

    print(f"\nEntre os {executados} que rodaram ate o fim:")
    print(
        f"- horizon fixo    : {falsos_fixo} falsos positivos "
        f"({falsos_fixo / executados:.1%}) -> proximo do alpha={ALPHA:.0%} planejado"
    )
    print(
        f"- peeking por lote: {falsos_peeking} falsos positivos "
        f"({falsos_peeking / executados:.1%}) -> inflacao de "
        f"{falsos_peeking / max(falsos_fixo, 1):.1f}x"
    )

    print("\nRecomendacoes:")
    print("- pre-registre o tamanho da amostra OU use testes sequenciais formais (SPRT/mSPRT);")
    print("- guardrails tecnicos (latencia/erros) abortam o teste antes de qualquer lift.")


if __name__ == "__main__":
    main()
