"""Teste de hipoteses entre criativos de campanha: ANOVA, Tukey HSD e tamanho de efeito."""

import hipoteses as hip
import numpy as np
from scipy import stats

SEED = 42
N_POR_GRUPO = 400
RECEITA_MEDIA = {"Controle": 52.0, "Criativo A": 55.5, "Criativo B": 53.0, "Criativo C": 61.0}


def simular_receitas(seed: int = SEED) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    # receita por usuario: lognormal com medias distintas por criativo
    return {
        nome: rng.lognormal(np.log(media) - 0.35, 0.7, N_POR_GRUPO).round(2) for nome, media in RECEITA_MEDIA.items()
    }


if __name__ == "__main__":
    grupos = simular_receitas()

    print("=== DESCRITIVO + NORMALIDADE (Shapiro) ===")
    descritivo = hip.resumo_descritivo(grupos)
    print(descritivo.to_string(index=False))
    nao_normais = descritivo[descritivo["normal_p"] < 0.05]["campanha"].tolist()
    if nao_normais:
        print(
            f"\nNota: {', '.join(nao_normais)} desviam da normalidade; com n=400/grupo a ANOVA segue robusta pelo TLC."
        )

    stat_levene, p_levene = stats.levene(*grupos.values())
    print(
        f"\nLevene (homocedasticidade): p={p_levene:.4f} -> "
        f"{'variancias equivalentes' if p_levene > 0.05 else 'variancias diferentes'}"
    )

    f_stat, p_anova = hip.anova_um_fator(grupos)
    print("\n=== ANOVA UM FATOR ===")
    print(f"F({len(grupos) - 1}, {sum(len(g) for g in grupos.values()) - len(grupos)}) = {f_stat:.3f}")
    print(f"p-valor = {p_anova:.4f} -> {'rejeita H0' if p_anova < 0.05 else 'sem evidencia de diferenca'}")

    if p_anova >= 0.05:
        print("\nDECISAO: nenhum criativo supera o controle com significancia estatistica.")
        raise SystemExit(0)

    print("\n=== TUKEY HSD (pares) ===")
    for par in hip.tukey_hsd(grupos):
        marca = "*" if par["significativo"] else " "
        print(f"- {par['par']:<22} dif={par['diferenca_media']:>+8.2f}  p={par['p_valor']:.4f} {marca}")

    controle = grupos["Controle"]
    melhor_nome, melhor = max(
        ((nome, valores) for nome, valores in grupos.items() if nome != "Controle"),
        key=lambda item: item[1].mean(),
    )
    d = hip.cohen_d(melhor, controle)
    lift = melhor.mean() / controle.mean() - 1
    print("\n=== VEREDICTO ===")
    print(f"Vencedor: {melhor_nome} | lift vs Controle: {lift:+.1%} | Cohen's d: {d:.2f}")
    receita_extra = (melhor.mean() - controle.mean()) * N_POR_GRUPO * 12
    print(f"Impacto estimado mensal na amostra: R$ {receita_extra:,.0f}")
