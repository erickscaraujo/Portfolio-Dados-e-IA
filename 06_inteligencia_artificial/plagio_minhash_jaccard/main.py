"""Plagio: shingles + Jaccard exato x aproximacao MinHash."""

import hashlib
import re

K_SHINGLE = 3
NUM_PERMUTACOES = 64
LIMIAR_SUSPEITA = 0.30


def shingles(texto: str, k: int = K_SHINGLE) -> set[str]:
    palavras = re.findall(r"[a-záéíóúâêôãõç]+", texto.lower())
    return {" ".join(palavras[i : i + k]) for i in range(len(palavras) - k + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _hash_shingle(shingle: str, semente: int) -> int:
    digesto = hashlib.md5(f"{semente}:{shingle}".encode()).hexdigest()
    return int(digesto[:8], 16)


def minhash(shingles_doc: set[str], permutacoes: int = NUM_PERMUTACOES) -> list[int]:
    """Menor hash por semente; assinatura de tamanho fixo por documento."""
    assinatura = []
    for semente in range(permutacoes):
        menor = min(_hash_shingle(s, semente) for s in shingles_doc)
        assinatura.append(menor)
    return assinatura


def similaridade_minhash(ass_a: list[int], ass_b: list[int]) -> float:
    concordancias = sum(1 for x, y in zip(ass_a, ass_b, strict=True) if x == y)
    return concordancias / len(ass_a)


DOCS = {
    "artigo_original.txt": (
        "A analise de dados transformou a forma como empresas tomam decisoes estrategicas. "
        "Com volume crescente de informacoes, times precisam de processos confiaveis "
        "para coletar limpar e analisar grandes bases em tempo habil."
    ),
    "copia_quase_total.txt": (
        "A analise de dados transformou a forma como empresas tomam decisoes estrategicas. "
        "Com volume crescente de informacoes, equipes precisam de processos confiaveis "
        "para coletar limpar e examinar grandes bases em tempo habil."
    ),
    "parcialmente_inspirado.txt": (
        "Empresas modernas dependem de dados para decidir. Sem processos solidos de "
        "qualidade, qualquer analise avancada vira apenas custo sem retorno mensuravel."
    ),
    "totalmente_diferente.txt": (
        "O cafe da manha do hotel inclui frutas frescas da estacao. A piscina abre as "
        "sete horas e o estacionamento e gratuito para hospedes do programa de pontos."
    ),
}


def main() -> None:
    conjuntos = {nome: shingles(texto) for nome, texto in DOCS.items()}
    assinaturas = {nome: minhash(conjunto) for nome, conjunto in conjuntos.items()}

    nomes = list(DOCS)
    erros = []
    suspeitos = []

    print("=== PARES DE DOCUMENTOS ===")
    for i in range(len(nomes)):
        for j in range(i + 1, len(nomes)):
            doc_a, doc_b = nomes[i], nomes[j]
            real = jaccard(conjuntos[doc_a], conjuntos[doc_b])
            estimado = similaridade_minhash(assinaturas[doc_a], assinaturas[doc_b])
            erro = abs(estimado - real)
            erros.append(erro)

            marcador = " <-- SUSPEITO" if estimado > LIMIAR_SUSPEITA else ""
            if estimado > LIMIAR_SUSPEITA:
                suspeitos.append((doc_a, doc_b, estimado))
            print(
                f"- {doc_a} x {doc_b}\n    jaccard real={real:.3f} | minhash={estimado:.3f} (erro {erro:.3f}){marcador}"
            )

    print(f"\nErro medio do MinHash com {NUM_PERMUTACOES} permutacoes: {np_mean(erros):.4f}")
    print("Pares marcados para revisao humana:")
    for a, b, score in suspeitos:
        print(f"  * {a} x {b} ({score:.0%})")


def np_mean(valores: list[float]) -> float:
    return sum(valores) / len(valores)


if __name__ == "__main__":
    main()
