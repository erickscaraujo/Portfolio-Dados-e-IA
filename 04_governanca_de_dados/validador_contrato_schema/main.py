"""Contrato de schema aplicado a duas versoes de uma fonte: a v2 veio com mudancas."""

import pathlib

import numpy as np
import pandas as pd
import validador as vd
from validador import Contrato

SEED = 9

CONTRATO_PEDIDOS = Contrato(
    tabela="pedidos",
    colunas={"pedido_id": "str", "cliente_id": "int", "valor": "float", "status": "str", "criado_em": "datetime"},
    nao_nulas=["pedido_id", "cliente_id", "valor"],
    dominios={"status": {"novo", "pago", "enviado", "cancelado"}},
    chave_primaria="pedido_id",
)


def gerar_v1(n: int = 800) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    return pd.DataFrame(
        {
            "pedido_id": [f"P{i}" for i in range(n)],
            "cliente_id": rng.integers(1, 300, n),
            "valor": rng.uniform(10, 900, n).round(2),
            "status": rng.choice(["novo", "pago", "enviado", "cancelado"], n),
            "criado_em": pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 180, n), unit="D"),
        }
    )


def gerar_v2(n: int = 850) -> pd.DataFrame:
    """Time de origem mudou o schema sem avisar (cenario classico de incidente)."""
    v2 = gerar_v1(n).rename(columns={"criado_em": "data_pedido"})  # renomeou coluna
    v2["valor"] = v2["valor"].astype(str)  # passou a virar string
    v2.loc[v2.sample(20, random_state=1).index, "cliente_id"] = np.nan  # nulos em campo obrigatorio
    v2["cupom"] = "nenhum"  # coluna nova sem contrato
    return v2


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    cenarios = {
        "v1 (conforme)": gerar_v1(),
        "v2 (com breaking changes)": gerar_v2(),
    }

    for nome, df in cenarios.items():
        achados = vd.validar(df, CONTRATO_PEDIDOS)

        print(f"\n=== {nome}: {len(achados)} achado(s) ===")
        if not achados:
            print("Schema conforme ao contrato. Pipeline pode seguir.")
        for item in achados:
            icone = "X" if item["severidade"] == vd.QUEBRA else "!"
            print(f" [{icone}] {item['severidade']:<6} {item['regra']:<18} {item['detalhe']}")

        sufixo = "v1" if "v1" in nome else "v2"
        vd.relatorio_json(CONTRATO_PEDIDOS.tabela, achados, f"outputs/contrato_{sufixo}.json")

    tem_quebra = any(
        a["severidade"] == vd.QUEBRA for a in vd.validar(cenarios["v2 (com breaking changes)"], CONTRATO_PEDIDOS)
    )
    print(f"\nGate de deploy da v2: {'BLOQUEADO' if tem_quebra else 'LIBERADO'}")
