"""Validacao de contratos de schema: tipos, obrigatoriedade e dominios por tabela."""

import json
from dataclasses import dataclass, field

import pandas as pd

QUEBRA = "quebra"
AVISO = "aviso"


@dataclass(frozen=True)
class Contrato:
    tabela: str
    colunas: dict[str, str]  # nome -> tipo esperado ("int", "float", "str", "datetime")
    nao_nulas: list[str] = field(default_factory=list)
    dominios: dict[str, set[str]] = field(default_factory=dict)
    chave_primaria: str | None = None


def _tipo_conforme(serie: pd.Series, esperado: str) -> bool:
    mapeamento = {
        "int": lambda s: pd.api.types.is_integer_dtype(s),
        "float": lambda s: pd.api.types.is_float_dtype(s) or pd.api.types.is_integer_dtype(s),
        "str": lambda s: pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s),
        "datetime": lambda s: pd.api.types.is_datetime64_any_dtype(s),
    }
    return mapeamento[esperado](serie)


def validar(df: pd.DataFrame, contrato: Contrato) -> list[dict]:
    achados: list[dict] = []

    faltantes = set(contrato.colunas) - set(df.columns)
    for coluna in sorted(faltantes):
        # coluna do contrato ausente na fonte e quebra dura: downstream depende dela
        achados.append(
            {"severidade": QUEBRA, "regra": "coluna_obrigatoria", "detalhe": f"'{coluna}' ausente no dataframe"}
        )

    extras = set(df.columns) - set(contrato.colunas)
    for coluna in sorted(extras):
        achados.append(
            {
                "severidade": AVISO,
                "regra": "coluna_nova",
                "detalhe": f"'{coluna}' existe na fonte mas nao esta no contrato",
            }
        )

    for coluna, tipo in contrato.colunas.items():
        if coluna not in df.columns:
            continue
        if not _tipo_conforme(df[coluna], tipo):
            real = str(df[coluna].dtype)
            achados.append(
                {"severidade": QUEBRA, "regra": "tipo", "detalhe": f"'{coluna}': esperado {tipo}, recebido {real}"}
            )

        if coluna in contrato.nao_nulas:
            nulos = int(df[coluna].isna().sum())
            if nulos:
                achados.append(
                    {"severidade": QUEBRA, "regra": "nao_nula", "detalhe": f"'{coluna}' contem {nulos} nulos"}
                )

        if coluna in contrato.dominios:
            invalidos = ~df[coluna].isin(contrato.dominios[coluna]) & df[coluna].notna()
            if invalidos.any():
                exemplos = df.loc[invalidos, coluna].astype(str).unique()[:3].tolist()
                achados.append(
                    {
                        "severidade": QUEBRA,
                        "regra": "dominio",
                        "detalhe": f"'{coluna}' com valores fora do dominio: {exemplos}",
                    }
                )

    if contrato.chave_primaria and contrato.chave_primaria in df.columns:
        duplicadas = int(df[contrato.chave_primaria].duplicated().sum())
        if duplicadas:
            achados.append(
                {
                    "severidade": QUEBRA,
                    "regra": "chave_primaria",
                    "detalhe": f"'{contrato.chave_primaria}' tem {duplicadas} duplicatas",
                }
            )

    return achados


def relatorio_json(tabela: str, achados: list[dict], caminho: str) -> None:
    conteudo = {
        "tabela": tabela,
        "status": "aprovado" if not achados else "reprovado",
        "violacoes": achados,
    }
    with open(caminho, "w", encoding="utf-8") as arq:
        json.dump(conteudo, arq, ensure_ascii=False, indent=2)
