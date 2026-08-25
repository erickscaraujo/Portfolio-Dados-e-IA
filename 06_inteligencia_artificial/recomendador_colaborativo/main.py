"""Avalia o recomendador em holdout e mostra recomendacoes interpretaveis."""

import numpy as np
from recomendador import RecomendadorItemItem, gerar_ratings

SEED = 12
FRACAO_HOLDOUT = 0.15


def separar_holdout(ratings: np.ndarray, seed: int = SEED) -> tuple[np.ndarray, list[tuple[int, int, float]]]:
    rng = np.random.default_rng(seed)
    observados = np.argwhere(~np.isnan(ratings))
    mascara = rng.random(len(observados)) < FRACAO_HOLDOUT

    holdout = [(int(u), int(i), ratings[u, i]) for u, i in observados[mascara]]
    treino = ratings.copy()
    for u, i, _ in holdout:
        treino[u, i] = np.nan
    return treino, holdout


if __name__ == "__main__":
    completo, titulos = gerar_ratings()
    treino, holdout = separar_holdout(completo)

    modelo = RecomendadorItemItem(n_vizinhos=12)
    modelo.treinar(treino)

    erros = [modelo.prever(u, i) - real for u, i, real in holdout]
    rmse = float(np.sqrt(np.mean(np.square(erros))))
    print(f"Holdout: {len(holdout)} avaliacoes escondidas")
    print(f"RMSE das predicoes: {rmse:.3f} (escala 1 a 5)")

    hits = 0
    usuarios_teste = sorted({u for u, _, _ in holdout})[:40]
    for usuario in usuarios_teste:
        itens_reais = [(i, real) for u2, i, real in holdout if u2 == usuario]
        melhor_item = max(itens_reais, key=lambda par: par[1])[0]
        top_n = {i for i, _ in modelo.recomendar(usuario, top_n=5)}
        hits += melhor_item in top_n
    print(f"Hit@5 (item preferido escondido apareceu no top-5): {hits / len(usuarios_teste):.0%}")

    print("\n=== EXEMPLO DE RECOMENDACOES ===")
    for usuario in (7, 42, 128):
        sugestoes = modelo.recomendar(usuario, top_n=4)
        formatadas = ", ".join(f"{titulos[i]} ({nota:.1f})" for i, nota in sugestoes)
        print(f"Usuario {usuario:>3}: {formatadas}")
