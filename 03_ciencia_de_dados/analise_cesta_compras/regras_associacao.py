"""Suporte, confianca e lift calculados manualmente sobre as transacoes."""

from collections import Counter
from itertools import combinations


def gerar_regras(
    transacoes: list[frozenset],
    min_suporte: float,
    min_confianca: float,
    min_lift: float,
) -> list[dict]:
    """Gera regras A -> B para pares de itens que passarem nos tres filtros."""
    total = len(transacoes)

    contagem_itens: Counter = Counter()
    contagem_pares: Counter = Counter()
    for cesta in transacoes:
        for item in cesta:
            contagem_itens[item] += 1
        # pares ordenados evitam contar (a,b) e (b,a) duas vezes
        for par in combinations(sorted(cesta), 2):
            contagem_pares[frozenset(par)] += 1

    regras = []
    for par, quantidade in contagem_pares.items():
        suporte_par = quantidade / total
        if suporte_par < min_suporte:
            continue

        item_a, item_b = sorted(par)
        candidatos = [(item_a, item_b), (item_b, item_a)]
        for se, entao in candidatos:
            suporte_se = contagem_itens[se] / total
            suporte_entao = contagem_itens[entao] / total

            confianca = suporte_par / suporte_se
            lift = confianca / suporte_entao

            if confianca >= min_confianca and lift >= min_lift:
                regras.append(
                    {
                        "se": se,
                        "entao": entao,
                        "suporte": round(suporte_par, 4),
                        "confianca": round(confianca, 4),
                        "lift": round(lift, 2),
                    }
                )

    return sorted(regras, key=lambda regra: (-regra["lift"], -regra["confianca"]))
