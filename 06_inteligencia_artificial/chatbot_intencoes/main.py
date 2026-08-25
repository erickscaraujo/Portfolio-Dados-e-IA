"""Chatbot de atendimento bancario: NLU de intencoes com fallback por confianca."""

import random

from classificador import LIMIAR_CONFIANCA, ClassificadorIntencoes
from dados_intencoes import INTENCOES
from sklearn.model_selection import train_test_split

MENSAGEM_SAIDA = {"sair", "exit", "quit"}


def montar_dataset() -> tuple[list[str], list[str]]:
    frases: list[str] = []
    rotulos: list[str] = []
    for intencao, (exemplos, _) in INTENCOES.items():
        frases.extend(exemplos)
        rotulos.extend([intencao] * len(exemplos))
    return frases, rotulos


def main() -> None:
    random.seed(7)
    frases, rotulos = montar_dataset()

    # holdout rapido para garantir que o modelo generaliza fora das frases exatas
    treino_x, teste_x, treino_y, teste_y = train_test_split(
        frases, rotulos, test_size=0.25, stratify=rotulos, random_state=42
    )
    bot = ClassificadorIntencoes({k: v[1] for k, v in INTENCOES.items()})
    bot.treinar(treino_x, treino_y)
    print(f"Acuracia em mensagens nunca vistas: {bot.acuracia_holdout(teste_x, teste_y):.1%}")
    print(f"(fallback ativado quando confianca < {LIMIAR_CONFIANCA:.0%})")
    print("\nChat iniciado — digite sua mensagem ('sair' encerra).\n")

    while True:
        try:
            mensagem = input("voce> ").strip()
        except EOFError:
            break
        if not mensagem or mensagem.lower() in MENSAGEM_SAIDA:
            print("bot> Ate logo!")
            break
        resposta = bot.responder(mensagem)
        print(f"bot> {resposta.texto}  [intencao={resposta.intencao}, conf={resposta.confianca:.0%}]")


if __name__ == "__main__":
    main()
