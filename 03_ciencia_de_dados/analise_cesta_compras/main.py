"""Market basket analysis: descobre combinacoes de produtos a partir de cupons sinteticos."""

import numpy as np
import regras_associacao as ra

CATALOGO = [
    "pao",
    "leite",
    "cafe",
    "manteiga",
    "queijo",
    "ovos",
    "arroz",
    "feijao",
    "cerveja",
    "vinho",
    "salgadinho",
    "refrigerante",
    "fralda",
    "sabonete",
    "detergente",
    "banana",
    "maca",
    "chocolate",
]

# padroes plantados que o algoritmo deve redescobrir
COMBOS_FREQUENTES = [
    (("pao", "manteiga"), 0.30),
    (("cafe", "leite"), 0.28),
    (("cerveja", "salgadinho"), 0.22),
    (("fralda", "cerveja"), 0.12),
    (("arroz", "feijao"), 0.25),
]

SEED = 5


def gerar_cupons(n_cupons: int = 3_000) -> list[frozenset]:
    rng = np.random.default_rng(SEED)
    transacoes = []

    for _ in range(n_cupons):
        cesta = set()
        # cada combo tem chance independente de entrar no cupom
        for combo, probabilidade in COMBOS_FREQUENTES:
            if rng.random() < probabilidade:
                cesta.update(combo)
        # itens aleatorios completam a compra com ruido
        n_aleatorios = rng.integers(1, 6)
        cesta.update(rng.choice(CATALOGO, size=n_aleatorios, replace=False).tolist())
        transacoes.append(frozenset(cesta))

    return transacoes


if __name__ == "__main__":
    cupons = gerar_cupons()

    regras = ra.gerar_regras(
        cupons,
        min_suporte=0.04,
        min_confianca=0.35,
        min_lift=1.2,
    )

    print(f"Cupons analisados: {len(cupons)} | regras aprovadas: {len(regras)}")
    print("\n=== TOP REGRAS POR LIFT ===")
    print(f"{'se':<14} {'entao':<14} {'suporte':>8} {'confianca':>10} {'lift':>6}")
    for regra in regras[:12]:
        print(
            f"{regra['se']:<14} {regra['entao']:<14} "
            f"{regra['suporte']:>8.2%} {regra['confianca']:>10.1%} {regra['lift']:>6.2f}"
        )

    combos_esperados = {" & ".join(sorted(c)) for c, _ in COMBOS_FREQUENTES}
    regras_descobertas = {f"{r['se']} & {r['entao']}" for r in regras}
    recuperados = [
        c for c in combos_esperados if any(r in regras_descobertas for r in [c, " & ".join(reversed(c.split(" & ")))])
    ]
    print(f"\nPadroes plantados redescobertos: {len(recuperados)}/{len(combos_esperados)}")
