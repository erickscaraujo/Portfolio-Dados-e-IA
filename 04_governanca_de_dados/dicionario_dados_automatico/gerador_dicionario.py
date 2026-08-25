"""Gerador de dicionario de dados em Markdown a partir dos DataFrames."""

import re
from datetime import datetime

import pandas as pd

PADRAO_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.")
PADRAO_CPF = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")


def _suspeita_pii(nome_coluna: str, amostra: list[str]) -> bool:
    pistas_nome = {"email", "cpf", "telefone", "nome", "endereco", "celular"}
    if any(pista in nome_coluna.lower() for pista in pistas_nome):
        return True
    textos = [str(v) for v in amostra[:20] if pd.notna(v)]
    return any(PADRAO_EMAIL.search(t) or PADRAO_CPF.search(t) for t in textos)


def _descrever(serie: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(serie):
        return f"min {serie.min():,.2f} | max {serie.max():,.2f} | media {serie.mean():,.2f}"
    unicos = serie.dropna().unique()[:3]
    exemplos = ", ".join(f"'{v}'" for v in unicos)
    return f"{serie.nunique()} valores distintos | ex.: {exemplos}"


def gerar_dicionario(
    tabelas: dict[str, pd.DataFrame],
    glossario_manual: dict[tuple[str, str], str] | None = None,
) -> str:
    """Glossario manual tem prioridade; o resto e inferido do proprio dado."""
    glossario = glossario_manual or {}
    secoes = [
        "# Dicionario de Dados",
        f"_Gerado automaticamente em {datetime.now().isoformat(timespec='seconds')}_\n",
    ]

    for nome_tabela, df in tabelas.items():
        secoes.append(f"\n## Tabela `{nome_tabela}` — {len(df):,} linhas\n")
        secoes.append("| coluna | tipo | nulos % | descricao/estatisticas | PII |")
        secoes.append("|---|---|---|---|---|")

        for coluna in df.columns:
            serie = df[coluna]
            tipo = str(serie.dtype)
            nulos_pct = serie.isna().mean() * 100

            chave = (nome_tabela, coluna)
            descricao = glossario.get(chave, _descrever(serie))

            # amostra so para detectar PII; nunca entra no documento final
            pii = _suspeita_pii(coluna, serie.dropna().astype(str).tolist())
            marcador_pii = "**SIM** - tratar antes de compartilhar" if pii else "não"

            secoes.append(f"| {coluna} | {tipo} | {nulos_pct:.1f}% | {descricao} | {marcador_pii} |")

    return "\n".join(secoes)


def salvar_dicionario(markdown: str, caminho: str = "outputs/dicionario_dados.md") -> str:
    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write(markdown)
    return caminho
