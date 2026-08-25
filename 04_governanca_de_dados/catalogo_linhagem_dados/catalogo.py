"""Catalogo tecnico de tabelas com estatisticas de perfil e persistencia em JSON."""

import json
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd


@dataclass
class TabelaMetadata:
    nome: str
    fonte: str
    linhas: int
    esquema: dict[str, str]
    nulos_pct: dict[str, float]
    atualizado_em: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class Catalogo:
    def __init__(self) -> None:
        self.tabelas: dict[str, TabelaMetadata] = {}

    def registrar(self, df: pd.DataFrame, nome: str, fonte: str) -> TabelaMetadata:
        meta = TabelaMetadata(
            nome=nome,
            fonte=fonte,
            linhas=len(df),
            esquema={col: str(dtype) for col, dtype in df.dtypes.items()},
            nulos_pct={col: round(float(df[col].isna().mean() * 100), 1) for col in df.columns},
        )
        self.tabelas[nome] = meta
        return meta

    def buscar(self, nome: str) -> TabelaMetadata | None:
        return self.tabelas.get(nome)

    def salvar(self, caminho: str) -> None:
        conteudo = {nome: vars(meta) for nome, meta in self.tabelas.items()}
        with open(caminho, "w", encoding="utf-8") as arq:
            json.dump(conteudo, arq, ensure_ascii=False, indent=2)

    def resumo(self) -> str:
        linhas = [f"{'tabela':<28} {'fonte':<12} {'linhas':>8}  colunas"]
        for meta in self.tabelas.values():
            colunas = ", ".join(meta.esquema)
            linhas.append(f"{meta.nome:<28} {meta.fonte:<12} {meta.linhas:>8}  {colunas}")
        return "\n".join(linhas)
