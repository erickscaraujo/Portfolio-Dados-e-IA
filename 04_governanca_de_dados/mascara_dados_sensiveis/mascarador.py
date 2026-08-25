"""Mascaramento de PII para compartilhamento seguro de bases (LGPD)."""

import hashlib
import re

import pandas as pd

PADRAO_CPF = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
PADRAO_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PADRAO_TELEFONE = re.compile(r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}")


def mascarar_texto(texto: str) -> str:
    """Aplica mascara parcial em qualquer PII embutida em texto livre."""
    texto = PADRAO_EMAIL.sub("***@***", texto)
    texto = PADRAO_CPF.sub(lambda m: _mascara_cpf(m.group()), texto)
    texto = PADRAO_TELEFONE.sub(lambda m: _mascara_telefone(m.group()), texto)
    return texto


def _mascara_cpf(cpf: str) -> str:
    digitos = re.sub(r"\D", "", cpf)
    return f"{digitos[:3]}.***.***-{digitos[-2:]}"


def _mascara_telefone(telefone: str) -> str:
    digitos = re.sub(r"\D", "", telefone)
    return f"({digitos[:2]}) *****-{digitos[-4:]}"


def pseudonimizar(valor: str) -> str:
    """Hash deterministico: mesmo valor gera mesma chave sem expor o dado original."""
    return hashlib.sha256(valor.encode()).hexdigest()[:12]


def anonimizar_base(clientes: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Aplica a estrategia adequada por coluna e devolve o resumo de auditoria."""
    df = clientes.copy()

    df["nome"] = df["nome"].map(lambda nome: "PESSOA " + pseudonimizar(nome)[:6])
    df["email"] = df["email"].map(pseudonimizar)
    df["cpf"] = df["cpf"].map(_mascara_cpf)
    df["telefone"] = df["telefone"].map(_mascara_telefone)

    # texto livre pode conter PII em qualquer posicao; conta quem tinha algo mascarado
    antes = df["observacoes"].fillna("")
    depois = antes.map(mascarar_texto)
    df["observacoes"] = depois
    piis_no_texto = int((antes != depois).sum())

    auditoria = {
        "colunas_pseudonimizadas": 2,
        "cpfs_mascarados": len(df),
        "telefones_mascarados": len(df),
        "registros_com_pii_em_texto_livre": piis_no_texto,
    }
    return df, auditoria
