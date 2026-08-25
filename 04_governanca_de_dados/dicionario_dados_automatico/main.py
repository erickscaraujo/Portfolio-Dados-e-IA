"""Dicionario de dados gerado de duas tabelas com glossario parcial da equipe."""

import pathlib

import numpy as np
import pandas as pd
from gerador_dicionario import gerar_dicionario, salvar_dicionario

SEED = 12

# documentacao que ja existia na wiki da equipe (tem prioridade no documento)
GLOSSARIO = {
    ("clientes", "score_credito"): "Score interno 0-1000 calculado pelo modelo de credito v3",
    ("pedidos", "valor_total"): "Soma dos itens com descontos aplicados; sem frete",
}


def montar_tabelas(n: int = 400) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)

    clientes = pd.DataFrame(
        {
            "cliente_id": range(1, n + 1),
            "nome_completo": [f"Cliente {i} Silva" for i in range(1, n + 1)],
            "email": [f"cliente{i}@mail.com" for i in range(1, n + 1)],
            "renda": rng.lognormal(8.4, 0.4, n).round(2),
            "score_credito": rng.integers(250, 950, n),
            "ativo": rng.choice([True, False], n, p=[0.8, 0.2]),
        }
    )

    pedidos = pd.DataFrame(
        {
            "pedido_id": [f"P{i:05d}" for i in range(1, n * 2)],
            "cliente_id": rng.integers(1, n + 40, n * 2 - 1),
            "valor_total": rng.uniform(25, 4_000, n * 2 - 1).round(2),
            "canal_venda": rng.choice(["site", "app", "loja"], n * 2 - 1),
            "criado_em": pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 300, n * 2 - 1), unit="D"),
        }
    )

    return {"clientes": clientes, "pedidos": pedidos}


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    markdown = gerar_dicionario(montar_tabelas(), GLOSSARIO)
    caminho = salvar_dicionario(markdown)

    print("=== PREVIEW DO DICIONARIO ===")
    for linha in markdown.splitlines()[:18]:
        print(linha)

    piis = sum("**SIM**" in linha for linha in markdown.splitlines())
    print(f"\nColunas marcadas com PII: {piis}")
    print(f"Dicionario completo salvo em {caminho}")
