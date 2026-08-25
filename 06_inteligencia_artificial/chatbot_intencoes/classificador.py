"""Classificador de intencoes (NLU leve) com TF-IDF + regressao logistica."""

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion

LIMIAR_CONFIANCA = 0.30


@dataclass
class Resposta:
    intencao: str
    confianca: float
    texto: str


class ClassificadorIntencoes:
    def __init__(self, respostas: dict[str, list[str]], seed: int = 21) -> None:
        self.respostas_por_intencao = respostas
        # combina vocabulario exato com char n-grams, que toleram erros de digitacao
        self.vetorizador = FeatureUnion(
            [
                ("palavras", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
                ("caracteres", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True)),
            ]
        )
        self.modelo = LogisticRegression(C=10, max_iter=1000)
        self._contador_resposta = 0
        self._seed = seed

    def treinar(self, frases: list[str], rotulos: list[str]) -> None:
        X = self.vetorizador.fit_transform(frases)
        self.modelo.fit(X, rotulos)

    def responder(self, mensagem: str) -> Resposta:
        X = self.vetorizador.transform([mensagem])
        probas = self.modelo.predict_proba(X)[0]
        melhor_idx = probas.argmax()
        intencao = self.modelo.classes_[melhor_idx]
        confianca = float(probas[melhor_idx])

        if confianca < LIMIAR_CONFIANCA or intencao not in self.respostas_por_intencao:
            return Resposta(
                "fallback",
                confianca,
                "Desculpe, nao entendi. Posso ajudar com saldo, transferencias ou faturas.",
            )

        opcoes = self.respostas_por_intencao[intencao]
        # alterna entre respostas para o botao repetir a mesma frase
        texto = opcoes[self._contador_resposta % len(opcoes)]
        self._contador_resposta += 1
        return Resposta(intencao, confianca, texto)

    def acuracia_holdout(self, frases_teste: list[str], rotulos_teste: list[str]) -> float:
        preditos = self.modelo.predict(self.vetorizador.transform(frases_teste))
        acertos = sum(p == r for p, r in zip(preditos, rotulos_teste, strict=True))
        return acertos / len(rotulos_teste)
