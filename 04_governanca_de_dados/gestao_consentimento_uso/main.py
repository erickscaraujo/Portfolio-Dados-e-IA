"""Consentimentos LGPD: publico de campanha filtrado e opt-out propagado."""

import json
import pathlib
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

VALIDADE_MESES = 12

FINALIDADES = ["marketing", "compartilhamento_terceiros"]


def gerar_consentimentos(n: int = 800, seed: int = 180) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    hoje = datetime(2025, 7, 1)

    linhas = []
    for cliente in range(1, n + 1):
        for finalidade in FINALIDADES:
            concedido = rng.random() < (0.55 if finalidade == "marketing" else 0.35)
            data_consentimento = hoje - timedelta(days=int(rng.integers(0, 900)))
            # opt-out recente: revoga o consentimento anterior
            revogou = concedido and rng.random() < 0.08

            linhas.append(
                {
                    "cliente_id": cliente,
                    "finalidade": finalidade,
                    "concedido": bool(concedido and not revogou),
                    "data": data_consentimento.isoformat(),
                    "revogado_em": (hoje - timedelta(days=int(rng.integers(1, 60)))).isoformat() if revogou else None,
                }
            )
    return pd.DataFrame(linhas)


def consentimento_vigente(df: pd.DataFrame, cliente_id: int, finalidade: str, agora: datetime) -> bool:
    registros = df[(df["cliente_id"] == cliente_id) & (df["finalidade"] == finalidade)]
    ultimo = registros.sort_values("data").iloc[-1]
    if not ultimo["concedido"]:
        return False

    data_consentimento = datetime.fromisoformat(ultimo["data"])
    expirou = agora - data_consentimento > timedelta(days=VALIDADE_MESES * 30)
    return not expirou


def main() -> None:
    pathlib.Path("outputs").mkdir(exist_ok=True)
    agora = datetime(2025, 7, 1)

    consentimentos = gerar_consentimentos()

    # campanha de marketing quer um publico-alvo; o juridico pediu auditoria
    rng = np.random.default_rng(181)
    publico_candidato = rng.choice(range(1, 801), size=250, replace=False).tolist()

    decisoes = []
    for cliente_id in publico_candidato:
        permitido = consentimento_vigente(consentimentos, cliente_id, "marketing", agora)
        motivo = "consentimento vigente" if permitido else "sem consentimento / revogado / expirado"
        decisoes.append({"cliente_id": int(cliente_id), "permitido": permitido, "motivo": motivo})

    tabela = pd.DataFrame(decisoes)
    bloqueados = tabela[~tabela["permitido"]]

    print("=== CAMPANHA DE MARKETING — FILTRO DE CONSENTIMENTO ===")
    print(f"publico candidato : {len(tabela)}")
    print(f"autorizados       : {(tabela['permitido']).sum()}")
    print(f"bloqueados        : {len(bloqueados)}")

    # opt-out propagado: cliente 7 revoga tudo; nenhuma lista pode mante-lo
    opt_out = pd.DataFrame(
        [
            {
                "cliente_id": 7,
                "finalidade": f,
                "concedido": False,
                "data": agora.isoformat(),
                "revogado_em": agora.isoformat(),
            }
            for f in FINALIDADES
        ]
    )
    consentimentos = pd.concat([consentimentos, opt_out], ignore_index=True)
    ainda_permitido = consentimento_vigente(consentimentos, 7, "marketing", agora)
    print(f"\nOpt-out do cliente 7 propagado -> marketing permitido? {ainda_permitido}")

    with open("outputs/auditoria_consentimentos.json", "w", encoding="utf-8") as arq:
        json.dump(
            {
                "gerado_em": agora.isoformat(),
                "decisoes": decisoes,
                "opt_out_total_cliente_7": not ainda_permitido,
            },
            arq,
            ensure_ascii=False,
            indent=2,
        )

    print("Trilha de auditoria salva em outputs/auditoria_consentimentos.json")


if __name__ == "__main__":
    main()
