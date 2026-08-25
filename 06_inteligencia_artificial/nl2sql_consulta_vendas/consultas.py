"""Tradutor de perguntas em SQL sobre o schema de vendas (abordagem rule-based)."""

import re

CATEGORIAS = {"eletronicos", "casa", "livros", "beleza", "esportes"}
CIDADES = {"sao paulo", "rio de janeiro", "curitiba", "recife"}

TEMPLATE_BASE = """
SELECT {dimensao}, {agregacao}(p.valor) AS resultado
FROM pedidos p JOIN clientes c ON c.cliente_id = p.cliente_id
WHERE 1=1 {filtros}
GROUP BY {dimensao}
ORDER BY resultado DESC
"""

AGREGACOES = {
    "total": "SUM",
    "faturamento": "SUM",
    "media": "AVG",
    "ticket": "AVG",
    "quantidade": "COUNT",
    "quantos": "COUNT",
}


def _dimensao(texto: str) -> str:
    # marcacao explicita do usuario tem prioridade
    if "por mes" in texto or "mensal" in texto:
        return "strftime('%Y-%m', p.data)"
    if "por cidade" in texto:
        return "c.cidade"
    if "por categoria" in texto:
        return "p.categoria"
    # sem marcacao, deduz pelo que aparece na pergunta
    if "cidade" in texto or any(c in texto for c in CIDADES):
        return "c.cidade"
    if "mes" in texto or any(re.search(rf"\b{ano}\b", texto) for ano in ("2024", "2025")):
        return "strftime('%Y-%m', p.data)"
    return "p.categoria"


def traduzir(pergunta: str) -> str | None:
    """Reconhece padroes de linguagem natural e monta o SQL equivalente."""
    texto = pergunta.lower()

    agregacao = next((AGREGACOES[palavra] for palavra in AGREGACOES if palavra in texto), None)
    if agregacao is None:
        return None

    dimensao = _dimensao(texto)

    filtros = ""
    categoria = next((c for c in CATEGORIAS if c in texto), None)
    if categoria and dimensao != "p.categoria":
        filtros += f" AND p.categoria = '{categoria}'"
    cidade = next((c for c in CIDADES if c in texto), None)
    if cidade and dimensao != "c.cidade":
        filtros += f" AND lower(c.cidade) = '{cidade}'"
    ano = re.search(r"\b(20\d{2})\b", texto)
    if ano:
        filtros += f" AND strftime('%Y', p.data) = '{ano.group(1)}'"

    return TEMPLATE_BASE.format(dimensao=dimensao, agregacao=agregacao, filtros=filtros)


def capacidades() -> str:
    return (
        "Consigo responder perguntas de vendas com:\n"
        "- agregacao: total/faturamento, media/ticket, quantidade\n"
        "- agrupamento por: categoria, cidade ou mes/ano\n"
        "- filtros: categoria (ex.: eletronicos), cidade, ano (ex.: 2024)\n"
        "Exemplo: 'faturamento total de eletronicos em 2024'"
    )
