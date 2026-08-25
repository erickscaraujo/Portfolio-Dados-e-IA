"""Filtragem colaborativa item-item sobre uma matriz esparsa de avaliacoes."""

import numpy as np

SEED = 12


class RecomendadorItemItem:
    def __init__(self, n_vizinhos: int = 10) -> None:
        self.n_vizinhos = n_vizinhos
        self.ratings: np.ndarray | None = None
        self.media_usuario: np.ndarray | None = None
        self.similaridade: np.ndarray | None = None

    def treinar(self, ratings: np.ndarray) -> None:
        """ratings: matriz usuarios x itens com NaN onde nao houve interacao."""
        self.ratings = ratings
        self.media_usuario = np.nanmean(np.where(np.isnan(ratings), np.nan, ratings), axis=1)

        # centraliza apenas nas celulas observadas; nao observado vira 0 para o cosseno
        centralizada = np.where(np.isnan(ratings), 0, ratings - self._media_expandida())
        normas = np.sqrt((centralizada**2).sum(axis=0))
        normas[normas == 0] = 1

        normalizada = centralizada / normas
        self.similaridade = normalizada.T @ normalizada
        np.fill_diagonal(self.similaridade, 0)

    def _media_expandida(self) -> np.ndarray:
        return self.media_usuario[:, None] * np.ones_like(self.ratings)

    def prever(self, usuario: int, item: int) -> float:
        """Media ponderada dos vizinhos mais proximos ja avaliados pelo usuario."""
        linha_usuario = self.ratings[usuario]
        observados = ~np.isnan(linha_usuario)
        observados[item] = False  # o proprio item entra como alvo, nunca como vizinho

        candidatos_idx = np.where(observados)[0]
        if len(candidatos_idx) == 0:
            return float(self.media_usuario[usuario])

        # ordena apenas os realmente observados para nao trazer NaN de celulas vazias
        ordem = candidatos_idx[np.argsort(self.similaridade[item][candidatos_idx])[::-1]]
        # similaridades negativas puxam a media ponderada para longe da escala real
        ordem = [idx for idx in ordem if self.similaridade[item][idx] > 0][: self.n_vizinhos]
        if len(ordem) == 0:
            return float(self.media_usuario[usuario])

        vizinhos_sims = self.similaridade[item][ordem]

        soma_sim = vizinhos_sims.sum()
        if soma_sim <= 1e-9:
            return float(self.media_usuario[usuario])

        desvios = linha_usuario[ordem] - self.media_usuario[usuario]
        return float(self.media_usuario[usuario] + (vizinhos_sims @ desvios) / soma_sim)

    def recomendar(self, usuario: int, top_n: int = 5) -> list[tuple[int, float]]:
        nao_avaliados = np.isnan(self.ratings[usuario])
        previsoes = [(item, self.prever(usuario, item)) for item in np.where(nao_avaliados)[0]]
        previsoes.sort(key=lambda par: par[1], reverse=True)
        return previsoes[:top_n]


def gerar_ratings(
    n_usuarios: int = 300, n_itens: int = 60, densidade: float = 0.18, seed: int = SEED
) -> tuple[np.ndarray, dict]:
    """Gostos latentes por genero produzem padroes que a colaboracao consegue capturar."""
    rng = np.random.default_rng(seed)
    generos = ["acao", "comedia", "drama", "terror"]

    gosto_usuarios = rng.dirichlet([2, 2, 2, 2], size=n_usuarios)
    perfil_itens = rng.dirichlet([3, 3, 3, 3], size=n_itens)

    afinidade = gosto_usuarios @ perfil_itens.T  # compatibilidade usuario x item
    ratings = np.full((n_usuarios, n_itens), np.nan)

    for u in range(n_usuarios):
        itens_avaliados = rng.choice(n_itens, size=int(n_itens * densidade), replace=False)
        nota_base = 1 + 4 * afinidade[u, itens_avaliados]
        notas = np.clip(nota_base + rng.normal(0, 0.6, len(itens_avaliados)), 1, 5).round(1)
        ratings[u, itens_avaliados] = notas

    titulos = {i: f"{generos[np.argmax(perfil_itens[i])].capitalize()} #{i:02d}" for i in range(n_itens)}
    return ratings, titulos
