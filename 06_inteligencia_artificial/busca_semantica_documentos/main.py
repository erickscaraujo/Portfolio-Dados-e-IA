"""Busca semantica em FAQ bancario com ranking por similaridade de cosseno."""

from buscador import BuscadorSemantico

FAQ = [
    {
        "titulo": "Cartao virtual",
        "texto": "O cartao virtual gera um numero temporario para compras online com mais seguranca. Pode ser criado no app na aba cartoes.",
    },
    {
        "titulo": "Segunda via de fatura",
        "texto": "A segunda via da fatura pode ser emitida no app ou site, disponivel em ate 2 minutos por email.",
    },
    {
        "titulo": "Taxa de transferencia",
        "texto": "Transferencias via pix sao gratuitas para pessoas fisicas. TED tem custo conforme tabela do contrato.",
    },
    {
        "titulo": "Bloqueio de cartao",
        "texto": "Perdeu o cartao? Bloqueie imediatamente no app em cartoes, selecionar bloquear. O desbloqueio e imediato se encontrar.",
    },
    {
        "titulo": "Limite de credito",
        "texto": "O aumento de limite e analisado automaticamente a cada 3 meses considerando renda e historico de pagamento.",
    },
    {
        "titulo": "Rendimento poupanca",
        "texto": "A poupanca rende mensalmente no aniversario do deposito, seguindo a taxa vigente do Banco Central.",
    },
    {
        "titulo": "CDB liquidez diaria",
        "texto": "O CDB com liquidez diaria permite resgate a qualquer momento; o rendimento acompanha percentual do CDI.",
    },
    {
        "titulo": "Abertura de conta",
        "texto": "Abrir conta leva cerca de 8 minutos com selfie e documento. Sem tarifa mensal para pessoa fisica.",
    },
    {
        "titulo": "Pagamento por QR code",
        "texto": "Pague boletos e lojas com QR code do pix direto na tela inicial do aplicativo.",
    },
    {
        "titulo": "Atendimento humano",
        "texto": "Para falar com atendente humano, use o chat do app e digite atendente durante a conversa com o assistente.",
    },
    {
        "titulo": "Seguro celular",
        "texto": "O seguro celular cobre quebra acidental e roubo, com carencia de 30 dias e franquia fixa por sinistro.",
    },
    {
        "titulo": "Consorcio",
        "texto": "No consorcio voce paga parcelas mensais e participa de sorteios ou lance para receber a carta de credito.",
    },
    # variantes com outras palavras para testar generalizacao
    {
        "titulo": "Cartao virtual (variantes)",
        "texto": "Gerar numero descartavel para ecommerce evita clonagem do cartao fisico nas compras pela internet.",
    },
    {
        "titulo": "Fatura em atraso",
        "texto": "Fatura vencida gera juros pro rata dia. Emita a segunda via atualizada e pague o quanto antes para evitar restricoes.",
    },
]

CASOS_TESTE = [
    ("como faco compra segura na internet sem expor meu cartao", "Cartao virtual"),
    ("paguei errado como falo com uma pessoa", "Atendimento humano"),
    ("minha fatura venceu e nao paguei o que acontece", "Fatura em atraso"),
    ("quero investir e sacar quando quiser", "CDB liquidez diaria"),
    ("perdi meu cartao preciso cancelar agora", "Bloqueio de cartao"),
    ("quanto rende o dinheiro na poupanca", "Rendimento poupanca"),
]


def main() -> None:
    buscador = BuscadorSemantico(FAQ)

    print("=== RANKING POR CONSULTA ===")
    for consulta, esperado in CASOS_TESTE:
        resultados = buscador.buscar(consulta)
        marca = "OK" if resultados[0]["titulo"] == esperado else "MISS"
        print(f"\n[consulta] {consulta}")
        for i, item in enumerate(resultados, start=1):
            print(f"  {i}. ({item['score']:.2f}) {item['titulo']}")
        print(f"  esperado: {esperado} -> {marca}")

    hits = buscador.acuracia_hits(CASOS_TESTE, k=2)
    print(f"\nHits@2 no conjunto de teste: {hits:.0%}")


if __name__ == "__main__":
    main()
