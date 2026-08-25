"""Mini-RAG: recupera trechos e monta resposta citando a fonte (sem LLM)."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

LIMIAR_SIMILARIDADE = 0.12

BASE_CONHECIMENTO = [
    {
        "titulo": "Politica de trocas",
        "texto": "O cliente pode trocar o produto em ate 30 dias corridos "
        "com a nota fiscal. Produtos de higiene nao aceitam troca por questoes sanitarias. A primeira troca tem frete pago pela loja.",
    },
    {
        "titulo": "Prazo de entrega",
        "texto": "Capitais recebem em ate 3 dias uteis e interior em ate 7 dias uteis. "
        "Pedidos com pagamento aprovado antes das 14h saem no mesmo dia. Rastreio e enviado automaticamente por email.",
    },
    {
        "titulo": "Pagamento",
        "texto": "Aceitamos pix, cartao em ate 12 vezes e boleto com vencimento em 2 dias. "
        "Pedidos pagos no pix ganham 5 por cento de desconto automatico. O boleto pode levar 2 dias uteis para compensar.",
    },
    {
        "titulo": "Programa de fidelidade",
        "texto": "Cada real gasto vale um ponto. Pontos expiram apos 18 meses "
        "e podem ser trocados por desconto a partir de 100 pontos. Funcionarios nao acumulam pontos.",
    },
    {
        "titulo": "Cancelamento",
        "texto": "O pedido pode ser cancelado gratuitamente antes da faturacao. "
        "Apos o envio, o cancelamento vira devolucao e segue a politica de trocas. Assinaturas cancelam ao fim do ciclo.",
    },
]


class RagSimples:
    def __init__(self, base: list[dict]) -> None:
        self.base = base
        self.vetorizador = TfidfVectorizer(ngram_range=(1, 2))
        self.matriz = self.vetorizador.fit_transform([doc["texto"] for doc in base])

    def _sentenca_mais_relevante(self, pergunta: str, texto: str) -> str:
        vetor_pergunta = self.vetorizador.transform([pergunta])
        sentencas = [s.strip() for s in texto.split(".") if s.strip()]
        vetores_sentencas = self.vetorizador.transform(sentencas)
        similaridades = cosine_similarity(vetor_pergunta, vetores_sentencas).ravel()
        return sentencas[int(similaridades.argmax())]

    def responder(self, pergunta: str) -> str:
        vetor_pergunta = self.vetorizador.transform([pergunta])
        similaridades = cosine_similarity(vetor_pergunta, self.matriz).ravel()
        melhor = int(similaridades.argmax())

        if similaridades[melhor] < LIMIAR_SIMILARIDADE:
            return "Nao encontrei isso na base de conhecimento. Reformule ou fale com um atendente."

        doc = self.base[melhor]
        frase = self._sentenca_mais_relevante(pergunta, doc["texto"])
        return f"{frase}. (fonte: '{doc['titulo']}', relevancia {similaridades[melhor]:.0%})"


if __name__ == "__main__":
    rag = RagSimples(BASE_CONHECIMENTO)

    perguntas = [
        "comprei errado, consigo devolver o produto?",
        "quanto tempo demora para chegar minha compra",
        "tem desconto pagando no pix?",
        "os pontos do programa vencem?",
        "voces vendem refeicao congelada?",  # fora da base
    ]
    print("=== PERGUNTAS E RESPOSTAS CITADAS ===")
    for pergunta in perguntas:
        print(f"\n[?] {pergunta}")
        print(f"[R] {rag.responder(pergunta)}")
