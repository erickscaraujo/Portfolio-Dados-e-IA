"""Auditoria de acessos: privilegio minimo, contas dormentes e segregacao de funcoes."""

import json
import pathlib
from datetime import datetime

import pandas as pd

# sensibilidade dos datasets: restrito exige justificativa ativa no cadastro do acesso
DATASETS = {
    "vw_vendas_publica": "interno",
    "base_clientes_pii": "restrito",
    "financeiro_folha": "confidencial",
    "logs_aplicacao": "interno",
}

# pares que NAO podem pertencer a mesma pessoa (segregacao de funcoes)
CONFLITOS_SOD = [
    ("base_clientes_pii", "write", "financeiro_folha", "read"),
]

HOJE = datetime(2025, 7, 1)


def gerar_acessos() -> pd.DataFrame:
    acessos = [
        # usuario, dataset, permissao, ultimo_login_dias, tem_justificativa
        ("ana.souza", "vw_vendas_publica", "read", 2, False),
        ("ana.souza", "base_clientes_pii", "write", 3, True),
        ("bruno.lima", "financeiro_folha", "read", 140, False),  # dormente com dado sensivel
        ("bruno.lima", "base_clientes_pii", "write", 150, False),  # conflito SoD + sem justificativa
        ("carla.dias", "logs_aplicacao", "read", 10, False),
        ("diego.rocha", "financeiro_folha", "admin", 400, True),  # conta esquecida de ex-time
        ("elisa.melo", "vw_vendas_publica", "admin", 60, False),  # admin desnecessario p/ leitura
        ("felipe.cruz", "base_clientes_pii", "read", 5, False),  # restrito sem justificativa
        ("gabi.santos", "logs_aplicacao", "write", 45, False),
    ]
    return pd.DataFrame(
        acessos,
        columns=["usuario", "dataset", "permissao", "ultimo_login_dias", "justificado"],
    )


def auditar(acessos: pd.DataFrame) -> pd.DataFrame:
    achados = []

    for linha in acessos.itertuples(index=False):
        sensibilidade = DATASETS[linha.dataset]

        if sensibilidade == "restrito" and not linha.justificado:
            achados.append(
                {
                    "usuario": linha.usuario,
                    "dataset": linha.dataset,
                    "regra": "acesso_restrito_sem_justificativa",
                    "severidade": "alta",
                    "acao_sugerida": f"suspender ate formalizar necessidade ({linha.permissao})",
                }
            )

        if linha.ultimo_login_dias > 90:
            achados.append(
                {
                    "usuario": linha.usuario,
                    "dataset": linha.dataset,
                    "regra": "conta_dormente",
                    "severidade": "media" if sensibilidade == "interno" else "alta",
                    "acao_sugerida": f"revogar acesso (sem login ha {linha.ultimo_login_dias} dias)",
                }
            )

        if linha.dataset == "vw_vendas_publica" and linha.permissao == "admin":
            achados.append(
                {
                    "usuario": linha.usuario,
                    "dataset": linha.dataset,
                    "regra": "privilegio_excessivo",
                    "severidade": "baixa",
                    "acao_sugerida": "rebaixar para read (nao justifica admin em view)",
                }
            )

        for ds_a, perm_a, ds_b, perm_b in CONFLITOS_SOD:
            mesmo_usuario = (
                acessos[
                    (acessos["usuario"] == linha.usuario)
                    & (
                        ((acessos["dataset"] == ds_a) & (acessos["permissao"] == perm_a))
                        | ((acessos["dataset"] == ds_b) & (acessos["permissao"] == perm_b))
                    )
                ]["usuario"].nunique()
                == 1
            )
            tem_os_dois = (
                len(
                    acessos[
                        (acessos["usuario"] == linha.usuario)
                        & (
                            ((acessos["dataset"] == ds_a) & (acessos["permissao"] == perm_a))
                            | ((acessos["dataset"] == ds_b) & (acessos["permissao"] == perm_b))
                        )
                    ]
                )
                >= 2
            )
            if mesmo_usuario and tem_os_dois:
                ja_registrado = any(a["regra"] == "conflito_sod" and a["usuario"] == linha.usuario for a in achados)
                if not ja_registrado:
                    achados.append(
                        {
                            "usuario": linha.usuario,
                            "dataset": f"{ds_a} + {ds_b}",
                            "regra": "conflito_sod",
                            "severidade": "critica",
                            "acao_sugerida": "separar responsabilidades entre duas pessoas",
                        }
                    )

    resultado = pd.DataFrame(achados)
    ordem = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}
    return resultado.assign(_o=resultado["severidade"].map(ordem)).sort_values("_o").drop(columns="_o")


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    achados = auditar(gerar_acessos())

    print(f"=== AUDITORIA DE ACESSOS ({HOJE.date()}) ===")
    print(achados.to_string(index=False))

    print("\n=== RESUMO POR REGRA ===")
    print(achados.groupby("regra")["usuario"].count().to_string())

    caminho = "outputs/achados_auditoria.json"
    with open(caminho, "w", encoding="utf-8") as arq:
        json.dump(achados.to_dict(orient="records"), arq, ensure_ascii=False, indent=2)
    print(f"\nPlano de remediacao salvo em {caminho}")
