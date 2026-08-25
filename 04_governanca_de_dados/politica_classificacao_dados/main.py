"""Politica de classificacao: rotula colunas por sensibilidade e define tratamento."""

import json
import re

import pandas as pd

NIVEIS = ["publico", "interno", "confidencial", "restrito"]

# tratamento obrigatorio por nivel (quem consome precisa saber o que pode fazer)
TRATAMENTO = {
    "publico": {"exibir": True, "compartilhar_externo": True, "observacao": "livre"},
    "interno": {"exibir": True, "compartilhar_externo": False, "observacao": "uso interno"},
    "confidencial": {
        "exibir": "mascarado",
        "compartilhar_externo": False,
        "observacao": "mascarar em ambientes nao produtivos",
    },
    "restrito": {
        "exibir": False,
        "compartilhar_externo": False,
        "observacao": "acesso nominal + criptografia em repouso",
    },
}

# regras em ordem de prioridade: primeira que casar define o nivel
REGRAS = [
    ("restrito", re.compile(r"cpf|rg\b|cartao|senha|token", re.I)),
    ("confidencial", re.compile(r"email|telefone|celular|nome|endereco|salario", re.I)),
    ("confidencial", re.compile(r"^[\w.+-]+@[\w-]+\.")),  # conteudo com email
    ("interno", re.compile(r"valor|receita|custo|preco|margem", re.I)),
    ("publico", re.compile(r".*")),
]


def classificar_coluna(tabela: str, coluna: str, serie: pd.Series) -> str:
    for nivel, padrao in REGRAS:
        if padrao.search(coluna):
            return nivel
        # amostra do conteudo para colunas cujo nome nao entrega nada
        amostra = serie.dropna().astype(str).head(30)
        if any(padrao.search(valor) for valor in amostra):
            return nivel
    return "interno"


def gerar_manifesto(tabelas: dict[str, pd.DataFrame]) -> list[dict]:
    manifesto = []
    for tabela, df in tabelas.items():
        for coluna in df.columns:
            nivel = classificar_coluna(tabela, coluna, df[coluna])
            manifesto.append(
                {
                    "tabela": tabela,
                    "coluna": coluna,
                    "nivel": nivel,
                    **TRATAMENTO[nivel],
                }
            )
    return manifesto


def main() -> None:
    clientes = pd.DataFrame(
        {
            "cliente_id": range(1, 51),
            "nome_completo": [f"Cliente {i}" for i in range(1, 51)],
            "email_contato": [f"c{i}@mail.com" for i in range(1, 51)],
            "cpf_titular": [f"{100 + i}.{200 + i}.333-44" for i in range(50)],
            "faixa_renda": ["alta"] * 20 + ["media"] * 30,
            "ativo": [True] * 45 + [False] * 5,
        }
    )
    vendas = pd.DataFrame(
        {
            "pedido_id": [f"P{i}" for i in range(1, 61)],
            "valor_total": [round(100 + i * 3.7, 2) for i in range(60)],
            "canal": ["site", "app"] * 30,
        }
    )

    manifesto = gerar_manifesto({"clientes": clientes, "vendas": vendas})

    print("=== CLASSIFICACAO POR COLUNA ===")
    print(f"{'tabela':<10} {'coluna':<16} {'nivel':<13} tratamento")
    for item in manifesto:
        print(f"- {item['tabela']:<9} {item['coluna']:<16} {item['nivel']:<12} {item['observacao']}")

    contagem = pd.Series([m["nivel"] for m in manifesto]).value_counts()
    print("\n=== RESUMO ===")
    print(contagem.to_string())

    with open("outputs/manifesto_classificacao.json", "w", encoding="utf-8") as arq:
        json.dump(manifesto, arq, ensure_ascii=False, indent=2)

    criticos = [m["coluna"] for m in manifesto if m["nivel"] == "restrito"]
    print(f"\nColunas restritas (prioridade maxima de protecao): {', '.join(criticos)}")
    print("Manifesto salvo em outputs/manifesto_classificacao.json")


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)
    main()
