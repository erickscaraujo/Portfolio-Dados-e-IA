"""Busca semantica leve: TF-IDF + similaridade de cosseno sobre uma base de FAQ."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class BuscadorSemantico:
    def __init__(self, documentos: list[dict]) -> None:
        self.documentos = documentos
        textos = [doc["texto"] for doc in documentos]
        # bigramas de palavras capturam expressoes do FAQ ("cartao virtual", "segunda via")
        self.vetorizador = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        self.matriz_docs = self.vetorizador.fit_transform(textos)

    def buscar(self, consulta: str, top_k: int = 3) -> list[dict]:
        vetor_consulta = self.vetorizador.transform([consulta])
        similaridades = cosine_similarity(vetor_consulta, self.matriz_docs).ravel()

        ordem = np.argsort(similaridades)[::-1][:top_k]
        return [
            {
                "titulo": self.documentos[i]["titulo"],
                "score": round(float(similaridades[i]), 3),
                "trecho": self.documentos[i]["texto"][:110] + "...",
            }
            for i in ordem
        ]

    def acuracia_hits(self, casos_teste: list[tuple[str, str]], k: int = 2) -> float:
        """Fracasso do buscador = documento esperado fora do top-k."""
        acertos = sum(
            any(caso["titulo"] == esperado for caso in self.buscar(consulta, top_k=k))
            for consulta, esperado in casos_teste
        )
        return acertos / len(casos_teste)
