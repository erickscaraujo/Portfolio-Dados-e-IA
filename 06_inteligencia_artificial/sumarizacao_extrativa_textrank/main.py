"""Sumarizacao extrativa: TextRank com PageRank implementado a mao."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ARTIGO = [
    "A empresa finalizou a migracao do legado de dados para o novo data lakehouse.",
    "O projeto durou nove meses e envolveu quatro times multidisciplinares.",
    "Na fase bronze, todos os eventos brutos passaram a ser capturados sem transformacao.",
    "A camada silver aplicou tipagem, deduplicacao e contratos minimos de qualidade.",
    "Falhas de ingestao caíram 78 por cento apos os contratos entrarem em vigor.",
    "A camada gold publica agregados diarios consumidos pelo BI e pelos modelos.",
    "Analistas relataram reducao de dois dias no ciclo de preparacao de dados.",
    "Os custos de armazenamento caíram porque dados frios ficam particionados e comprimidos.",
    "O monitoramento de frescura alerta quando alguma tabela fica fora do SLA.",
    "Proximos passos incluem catalogo automatico e linhagem em nivel de coluna.",
    "A diretoria aprovou a segunda onda, cobrindo areas de marketing e logistica.",
    "A liacao central do projeto foi tratar qualidade como codigo versionado.",
]


def matriz_similaridade(sentencas: list[str]) -> np.ndarray:
    vetorizador = TfidfVectorizer(lowercase=True)
    vetores = vetorizador.fit_transform(sentencas)
    similaridades = cosine_similarity(vetores)
    # grafo sem lacos: uma sentenca nao vota nela mesma
    np.fill_diagonal(similaridades, 0.0)
    return similaridades


def pagerank(similaridades: np.ndarray, amortecimento: float = 0.85, iteracoes: int = 100) -> np.ndarray:
    """Iteracao de potencia: score converge para a importancia estacionaria."""
    n = len(similaridades)
    soma_linhas = similaridades.sum(axis=1, keepdims=True)
    transicao = np.divide(similaridades, soma_linhas, out=np.full_like(similaridades, 1 / n), where=soma_linhas > 0)

    score = np.ones(n) / n
    for _ in range(iteracoes):
        novo_score = (1 - amortecimento) / n + amortecimento * transicao.T @ score
        if np.abs(novo_score - score).sum() < 1e-9:
            break
        score = novo_score
    return score


def resumir(sentencas: list[str], k: int = 4) -> list[int]:
    scores = pagerank(matriz_similaridade(sentencas))
    top = np.argsort(scores)[::-1][:k]
    return sorted(top.tolist())  # devolve na ordem original do texto


if __name__ == "__main__":
    indices_textrank = resumir(ARTIGO)
    baseline_posicao = [0, 1, 2]  # "pegar as primeiras frases" que todo mundo faz

    print("=== RESUMO POR POSICAO (baseline) ===")
    for i in baseline_posicao:
        print(f"- {ARTIGO[i]}")

    print("\n=== RESUMO POR TEXTRANK ===")
    for i in indices_textrank:
        print(f"- {ARTIGO[i]}")

    print("\nPesos das sentencas:")
    pesos = pagerank(matriz_similaridade(ARTIGO))
    for i in np.argsort(pesos)[::-1][:5]:
        print(f"  [{pesos[i]:.3f}] {ARTIGO[i][:60]}...")

    sobreposicao = len(set(indices_textrank) & set(baseline_posicao)) / len(baseline_posicao)
    print(
        f"\nSobreposicao com o baseline: {sobreposicao:.0%} "
        f"(TextRank trouxe conteudo do meio/fim que a posicao ignoraria)"
    )
