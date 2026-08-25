"""Lexico sentimental PT-BR com tratamento de negacao e intensificadores."""

NEGACOES = {"nao", "nunca", "nem", "jamais", "nenhum", "nada"}
INTENSIFICADORES = {"muito": 1.5, "super": 1.5, "extremamente": 1.8, "pouco": -0.6}

POSITIVAS = {
    "otimo",
    "excelente",
    "maravilhoso",
    "adorei",
    "amo",
    "perfeito",
    "rapido",
    "atencioso",
    "recomendo",
    "incrivel",
    "fantastico",
    "gostei",
    "eficiente",
    "simpatico",
    "qualidade",
    "barato",
    "confortavel",
    "facil",
    "intuitivo",
    "resolveu",
    "parabens",
    "surpreendente",
    "confiavel",
    "melhor",
    "amei",
}
NEGATIVAS = {
    "pessimo",
    "horrivel",
    "odiei",
    "detestei",
    "lento",
    "caro",
    "quebrado",
    "atrasado",
    "rude",
    "grosso",
    "problema",
    "defeito",
    "travando",
    "bugado",
    "complicado",
    "dificil",
    "insatisfeito",
    "decepcionante",
    "pior",
    "lixo",
    "nunca_compre",
    "arrependido",
    "frustrante",
    "desorganizado",
    "sujo",
}

JANELA_NEGACAO = 3


def pontuar(texto: str) -> float:
    """Score continuo aproximadamente entre -1 e 1; perto de zero indica neutro."""
    palavras = [p for p in texto.lower().replace(",", "").replace(".", "").split() if p]
    score = 0.0
    for i, palavra in enumerate(palavras):
        peso = INTENSIFICADORES.get(palavra)
        if peso is not None:
            continue  # o peso do intensificador entra na palavra seguinte
        valor = 1.0 if palavra in POSITIVAS else (-1.0 if palavra in NEGATIVAS else 0.0)
        if valor == 0:
            continue
        # negacao nas ultimas palavras inverte o sentimento ("nao gostei")
        contexto = palavras[max(0, i - JANELA_NEGACAO) : i]
        if any(neg in contexto for neg in NEGACOES):
            valor *= -0.9
        if i > 0 and palavras[i - 1] in INTENSIFICADORES:
            valor *= INTENSIFICADORES[palavras[i - 1]]
        score += valor
    return max(-1.0, min(1.0, score / 3))


def classificar(texto: str, limiar_neutro: float = 0.15) -> str:
    score = pontuar(texto)
    if abs(score) < limiar_neutro:
        return "neutro"
    return "positivo" if score > 0 else "negativo"
