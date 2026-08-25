"""Corretor ortografico probabilistico (abordagem classica de Peter Norvig)."""

import re
from collections import Counter

CORPUS = """
o cliente entrou em contato porque nao recebeu o pedido e quer saber o prazo de entrega
a fatura do cartao chegou com valor errado e o cliente pediu segunda via urgente
o sistema esta lento no horario de almoco e os usuarios reclamam do tempo de resposta
precisamos revisar o contrato antes de enviar a proposta comercial para o cliente novo
a entrega foi feita no prazo porem o produto chegou com a embalagem danificada
quando o pagamento cai na conta o sistema envia automaticamente a confirmacao por email
o time de dados analisou o relatorio de vendas e encontrou uma queda nas regioes norte
para abrir uma conta basta apresentar documento com foto e comprovante de endereco
o suporte tecnico resolveu o problema do login depois de atualizar a senha do usuario
reclamacoes sobre atraso na entrega cresceram neste mes segundo o painel de indicadores
"""

PALAVRAS = re.findall(r"[a-záéíóúâêôãõç]+", CORPUS.lower())
FREQUENCIA = Counter(PALAVRAS)
VOCABULARIO = set(FREQUENCIA)
LETRAS = "abcdefghijklmnopqrstuvwxyz"


def _edicoes_uma(palavra: str) -> set[str]:
    """Todas as strings a distancia 1: deletar, trocar, inserir, transpor."""
    particoes = [(palavra[:i], palavra[i:]) for i in range(len(palavra) + 1)]
    deletadas = [e + d[1:] for e, d in particoes if d]
    trocadas = [e + b + d[1:] for e, d in particoes if len(d) > 1 for b in LETRAS]
    inseridas = [e + b + d for e, d in particoes for b in LETRAS]
    transpostas = [e + d[1] + d[0] + d[2:] for e, d in particoes if len(d) > 1]
    return set(deletadas + trocadas + inseridas + transpostas)


def _edicoes_duas(palavra: str) -> set[str]:
    return {correcao for e1 in _edicoes_uma(palavra) for correcao in _edicoes_uma(e1)}


def corrigir(palavra: str) -> str:
    """Candidatos mais proximos ganham; dentro da mesma distancia, frequencia decide."""
    palavra = palavra.lower()
    if palavra in VOCABULARIO:
        return palavra

    candidatos = _edicoes_uma(palavra) & VOCABULARIO or _edicoes_duas(palavra) & VOCABULARIO or {palavra}
    return max(candidatos, key=FREQUENCIA.get)


def corrigir_frase(frase: str) -> str:
    return " ".join(corrigir(palavra) for palavra in frase.split())


if __name__ == "__main__":
    print(f"vocabulario do corpus: {len(VOCABULARIO)} palavras\n")

    typos_plantados = {
        "sistma": "sistema",
        "faturra": "fatura",
        "clente": "cliente",
        "entrga": "entrega",
        "relatorio": "relatorio",  # ultima ja esta certa
        "contratro": "contrato",
        "pagamnto": "pagamento",
        "usurio": "usuario",
    }
    acertos = 0
    print("=== CORRECOES ===")
    for typo, esperado in typos_plantados.items():
        sugestao = corrigir(typo)
        ok = sugestao == esperado
        acertos += ok
        marca = "[ok]" if ok else f"[esperado: {esperado}]"
        print(f"- {typo:<12} -> {sugestao:<12} {marca}")

    frases = [
        "o sistma estaa lentto hoje",
        "nao recebi a faturra do mes",
        "o clente quer saber da entrga",
    ]
    print("\n=== FRASES CORRIGIDAS ===")
    for frase in frases:
        print(f"- ({frase})\n  -> {corrigir_frase(frase)}")

    taxa = acertos / len(typos_plantados)
    print(f"\nAcuracia nos typos plantados: {taxa:.0%}")
