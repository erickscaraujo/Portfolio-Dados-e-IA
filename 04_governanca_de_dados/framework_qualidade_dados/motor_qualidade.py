"""Motor de regras de qualidade: executa validacoes declarativas sobre as tabelas."""

import re
from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class Regra:
    tabela: str
    coluna: str
    tipo: str
    dimensao: str
    params: dict = field(default_factory=dict)


@dataclass
class Resultado:
    regra: Regra
    total_linhas: int
    violacoes: int
    exemplos: list[str]


def _mascaras(df: pd.DataFrame, coluna: str, regra: Regra) -> pd.Series:
    """Retorna a mascara booleana das LINHAS VIOLADORAS para cada tipo de regra."""
    serie = df[coluna]

    match regra.tipo:
        case "nao_nulo":
            return serie.isna()
        case "unico":
            return serie.duplicated(keep=False)
        case "regex":
            padrao = re.compile(regra.params["padrao"])
            texto = serie.dropna().astype(str)
            invalidos = ~texto.str.match(padrao)
            return pd.Series(invalidos, index=texto.index)
        case "dominio":
            return ~serie.isin(regra.params["valores"]) & serie.notna()
        case "intervalo":
            fora_min = serie < regra.params.get("min", float("-inf"))
            fora_max = serie > regra.params.get("max", float("inf"))
            return (fora_min | fora_max) & serie.notna()
        case "data_passada":
            datas = pd.to_datetime(serie, errors="coerce")
            return datas > pd.Timestamp.now()
        case "integridade":
            pai = regra.params["tabela_pai"]
            coluna_pai = regra.params["coluna_pai"]
            chaves_validas = set(regra.params["_tabelas"][pai][coluna_pai].dropna())
            return ~serie.isin(chaves_validas) & serie.notna()
        case _:
            raise ValueError(f"tipo de regra desconhecido: {regra.tipo}")


def executar(tabelas: dict[str, pd.DataFrame], regras: list[Regra]) -> list[Resultado]:
    # integridade precisa enxergar todas as tabelas; injeta sem poluir a regra declarativa
    resultados = []
    for regra in regras:
        regra_exec = regra
        if regra.tipo == "integridade":
            regra_exec = Regra(
                regra.tabela,
                regra.coluna,
                regra.tipo,
                regra.dimensao,
                {**regra.params, "_tabelas": tabelas},
            )
        df = tabelas[regra.tabela]
        mascara = _mascaras(df, regra.coluna, regra_exec)

        exemplos = df.loc[mascara, regra.coluna].dropna().astype(str).unique()[:5].tolist()
        resultados.append(Resultado(regra, len(df), int(mascara.sum()), exemplos))
    return resultados


def score_por_dimensao(resultados: list[Resultado]) -> dict[str, float]:
    """Percentual de linhas conformes por dimensao, ponderado pelo volume verificado."""
    acumulado: dict[str, tuple[int, int]] = {}
    for res in resultados:
        violadas, total = acumulado.get(res.regra.dimensao, (0, 0))
        acumulado[res.regra.dimensao] = (violadas + res.violacoes, total + res.total_linhas)

    return {
        dimensao: round(max(0.0, (1 - violadas / total)) * 100, 2)
        for dimensao, (violadas, total) in sorted(acumulado.items())
    }
