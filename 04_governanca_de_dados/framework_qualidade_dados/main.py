"""Relatorio de qualidade sobre clientes/pedidos com defeitos plantados de proposito."""

import json
import pathlib

import numpy as np
import pandas as pd
from motor_qualidade import Regra, executar, score_por_dimensao

EMAIL_PADRAO = r"^[\w.+-]+@[\w-]+\.[\w.-]+$"


def gerar_tabelas(seed: int = 5) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    n = 600

    clientes = pd.DataFrame(
        {
            "id": range(1, n + 1),
            "nome": [f"Cliente {i}" for i in range(1, n + 1)],
            "email": [f"cliente{i}@mail.com" for i in range(1, n + 1)],
            "uf": rng.choice(["SP", "RJ", "MG", "RS", "BA"], n),
            "nascimento": pd.Timestamp("1960-01-01") + pd.to_timedelta(rng.integers(0, 16_000, n), unit="D"),
            "limite_credito": np.round(rng.uniform(500, 25_000, n), 2),
        }
    )

    pedidos = pd.DataFrame(
        {
            "pedido_id": [f"O{i}" for i in range(1, 1500)],
            "cliente_id": rng.integers(1, n + 60, 1499),  # alguns ids nao existem em clientes
            "valor": np.round(rng.lognormal(6.5, 0.8, 1499), 2),
            "status": rng.choice(["pago", "pendente", "cancelado"], 1499),
        }
    )

    # --- defeitos tipicos de producao ---
    clientes.loc[[10, 250, 480], "email"] = ["sem-arroba", "a@b", ""]
    clientes.loc[120, "nome"] = None
    clientes.loc[130, "nascimento"] = "2099-12-31"  # data futura
    clientes.loc[[140, 141], "limite_credito"] = -500  # fora da faixa
    duplicata = clientes.iloc[[7]].copy()  # id repetido
    clientes = pd.concat([clientes, duplicata], ignore_index=True)
    pedidos.loc[[15, 900], "status"] = "processando"  # valor fora do dominio

    return {"clientes": clientes, "pedidos": pedidos}


def regras_do_contrato() -> list[Regra]:
    return [
        Regra("clientes", "id", "unico", "unicidade"),
        Regra("clientes", "nome", "nao_nulo", "completude"),
        Regra("clientes", "email", "regex", "validade", {"padrao": EMAIL_PADRAO}),
        Regra("clientes", "uf", "dominio", "validade", {"valores": ["SP", "RJ", "MG", "RS", "BA"]}),
        Regra("clientes", "nascimento", "data_passada", "consistencia"),
        Regra("clientes", "limite_credito", "intervalo", "validade", {"min": 0, "max": 50_000}),
        Regra("pedidos", "pedido_id", "unico", "unicidade"),
        Regra("pedidos", "valor", "intervalo", "validade", {"min": 0.01, "max": 100_000}),
        Regra(
            "pedidos",
            "status",
            "dominio",
            "validade",
            {"valores": ["pago", "pendente", "cancelado"]},
        ),
        Regra(
            "pedidos",
            "cliente_id",
            "integridade",
            "consistencia",
            {"tabela_pai": "clientes", "coluna_pai": "id"},
        ),
    ]


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    tabelas = gerar_tabelas()
    resultados = executar(tabelas, regras_do_contrato())
    scores = score_por_dimensao(resultados)
    score_geral = round(np.mean(list(scores.values())), 2)

    print("=== RELATORIO DE QUALIDADE ===")
    falhas = [r for r in resultados if r.violacoes]
    if not falhas:
        print("Nenhuma violacao encontrada.")
    for res in falhas:
        exemplos = ", ".join(res.exemplos) or "-"
        print(f"[{res.regra.tabela}.{res.regra.coluna}] {res.regra.tipo}: {res.violacoes} violacoes | ex.: {exemplos}")

    print("\n=== SCORES POR DIMENSAO ===")
    for dimensao, score in scores.items():
        barra = "#" * int(score // 5)
        print(f"{dimensao.capitalize():<13} {score:>6.2f}%  {barra}")
    print(f"\nSCORE GERAL: {score_geral:.2f}%")

    relatorio = {
        "score_geral": score_geral,
        "scores_por_dimensao": scores,
        "violacoes": [
            {
                "tabela": r.regra.tabela,
                "coluna": r.regra.coluna,
                "tipo": r.regra.tipo,
                "total_violacoes": r.violacoes,
            }
            for r in falhas
        ],
    }
    with open("outputs/relatorio_qualidade.json", "w", encoding="utf-8") as arq:
        json.dump(relatorio, arq, ensure_ascii=False, indent=2)
    print("\nJSON salvo em outputs/relatorio_qualidade.json")
