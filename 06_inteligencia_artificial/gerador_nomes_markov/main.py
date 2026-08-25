"""Cadeia de Markov de caracteres para gerar nomes plausiveis de produto."""

import random
from collections import defaultdict

ORDEM = 3
CORPUS_NOMES = [
    "NexaFlow",
    "Quantix",
    "Lumina Core",
    "Vortex Pro",
    "Zentra Hub",
    "Kairos",
    "Orbita Max",
    "Pulse One",
    "Nova Track",
    "Flexi Cloud",
    "Astra Sync",
    "Helio Drive",
    "Momentum X",
    "Vertex Go",
    "Solari Data",
    "Zenit App",
    "Dinamo Kit",
    "Elevate Pro",
    "Fusion Lab",
    "Gravity Box",
    "Horizon AI",
    "Infinito Pay",
    "Jupter Scan",
    "Kinetic Link",
    "Lumen Grid",
    "Meta Vault",
    "Nimbus Run",
    "Optic Sense",
    "Prisma Stack",
    "Quanta Fit",
]


def treinar_cadeia(nomes: list[str], ordem: int = ORDEM) -> dict[tuple, list[str]]:
    """Mapa estado -> proximos caracteres; tokens <> delimitam inicio e fim."""
    cadeia: dict[tuple, list[str]] = defaultdict(list)
    for nome in nomes:
        nome_formatado = "<" * ordem + nome + ">"
        for i in range(ordem, len(nome_formatado)):
            estado = tuple(nome_formatado[i - ordem : i])
            cadeia[estado].append(nome_formatado[i])
    return cadeia


def _proximo_caractere(cadeia: dict[tuple, list[str]], estado: tuple, temperatura: float) -> str | None:
    opcoes = cadeia.get(estado)
    if not opcoes:
        return None
    if temperatura >= 10:
        return random.choice(opcoes)

    # temperatura baixa favorece os mais comuns (distribuicao elevada a 1/T)
    contagem = {opcao: opcoes.count(opcao) for opcao in set(opcoes)}
    pesos = [(frequencia) ** (1 / max(temperatura, 0.1)) for frequencia in contagem.values()]
    return random.choices(list(contagem), weights=pesos, k=1)[0]


def gerar_nome(cadeia: dict[tuple, list[str]], temperatura: float = 1.0, tamanho_maximo: int = 14) -> str:
    estado = tuple("<" * ORDEM)
    nome = ""
    while True:
        caractere = _proximo_caractere(cadeia, estado, temperatura)
        if caractere is None or caractere == ">":
            break
        nome += caractere
        if len(nome) >= tamanho_maximo:
            break
        estado = tuple((("<" * ORDEM) + nome)[-ORDEM:])
    return nome


def main() -> None:
    random.seed(210)
    cadeia = treinar_cadeia(CORPUS_NOMES)

    print("=== NOMES GERADOS POR TEMPERATURA ===")
    for temperatura, rotulo in ((0.4, "conservador"), (1.0, "equilibrado"), (2.2, "criativo")):
        gerados = []
        tentativas = 0
        while len(gerados) < 6 and tentativas < 60:
            tentativas += 1
            nome = gerar_nome(cadeia, temperatura)
            if len(nome) >= 5 and nome not in gerados and nome not in CORPUS_NOMES:
                gerados.append(nome)
        diversidade = len(set(gerados)) / max(len(gerados), 1)
        print(f"\nT={temperatura} ({rotulo}) | diversidade {diversidade:.0%}")
        for nome in gerados:
            print(f"  - {nome}")

    # nomes reais devem ser reproduziveis com T muito baixo
    recuperado = gerar_nome(cadeia, temperatura=0.05)
    print(f"\nT=0.05 tende a copiar padroes dominantes do corpus (ex.: '{recuperado}')")


if __name__ == "__main__":
    main()
