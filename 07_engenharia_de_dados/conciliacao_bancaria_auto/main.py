"""Conciliacao extrato x ledger: matching por valor com janela de datas."""

import pathlib
from datetime import date, timedelta

import numpy as np
import pandas as pd

JANELA_DIAS = 3
TOLERANCIA_CENTAVOS = 0.011


def gerar_lancamentos(seed: int = 220) -> tuple[list[dict], list[dict]]:
    """Ledger interno e extrato do banco; o extrato tem ruído realista."""

    rng = np.random.default_rng(seed)

    ledger = []
    for i in range(1, 121):
        dia = date(2025, 5, 1) + timedelta(days=int(rng.integers(0, 30)))
        valor = round(float(rng.uniform(50, 5_000)), 2)
        ledger.append({"id": f"L{i:04d}", "data": dia, "valor": valor, "historico": f"recebimento pedido {i}"})

    # banco: a maioria entra no mesmo dia; alguns caem com atraso; tarifas aparecem
    extrato = []
    for lancamento in ledger[:115]:
        atraso = int(rng.choice([0, 0, 0, 1, 2, 3]))
        valor_banco = lancamento["valor"]
        if rng.random() < 0.05:  # diferenca de tarifa embutida
            valor_banco = round(valor_banco - rng.uniform(1.5, 8.0), 2)
        extrato.append(
            {"id": f"B{len(extrato):04d}", "data": lancamento["data"] + timedelta(days=atraso), "valor": valor_banco}
        )
    for _ in range(4):  # recebimentos que o banco registrou em dobro
        origem = extrato[int(rng.integers(0, len(extrato)))]
        extrato.append({**origem, "id": f"B{len(extrato):04d}"})
    for _ in range(3):  # tarifas que existem so no banco
        extrato.append(
            {
                "id": f"B{len(extrato):04d}",
                "data": date(2025, 5, 20),
                "valor": -round(float(rng.uniform(15, 90)), 2),
            }
        )
    return ledger, extrato


def conciliar(ledger: list[dict], extrato: list[dict]) -> dict[str, list]:
    pendentes_ledger = {item["id"]: item for item in ledger}
    pendentes_extrato = {item["id"]: item for item in extrato}
    resultado = {"conciliados": [], "diferenca_valor": [], "so_no_ledger": [], "so_no_extrato": []}

    # fase 1: valor exato (com tolerancia de centavos), data mais proxima primeiro
    for id_ledger in sorted(pendentes_ledger):
        lancamento = pendentes_ledger[id_ledger]
        melhor_id, menor_dias = None, JANELA_DIAS + 1
        for id_extrato, entrada in pendentes_extrato.items():
            dias = abs((entrada["data"] - lancamento["data"]).days)
            if (
                dias <= JANELA_DIAS
                and abs(entrada["valor"] - lancamento["valor"]) <= TOLERANCIA_CENTAVOS
                and dias < menor_dias
            ):
                melhor_id, menor_dias = id_extrato, dias
        if melhor_id:
            resultado["conciliados"].append((id_ledger, melhor_id))
            del pendentes_extrato[melhor_id]
            del pendentes_ledger[id_ledger]

    # fase 2: valores proximos (diferenca pequena) na janela — suspeita de tarifa
    for id_ledger in list(pendentes_ledger):
        lancamento = pendentes_ledger[id_ledger]
        candidato = min(
            (
                (abs(e["valor"] - lancamento["valor"]), abs((e["data"] - lancamento["data"]).days), eid)
                for eid, e in pendentes_extrato.items()
                if abs((e["data"] - lancamento["data"]).days) <= JANELA_DIAS
            ),
            default=None,
        )
        if candidato and candidato[0] <= 10.0 and candidato[1] <= 1:
            _, _, id_extrato = candidato
            resultado["diferenca_valor"].append(
                (id_ledger, id_extrato, round(abs(pendentes_extrato[id_extrato]["valor"] - lancamento["valor"]), 2))
            )
            del pendentes_extrato[id_extrato]
            del pendentes_ledger[id_ledger]

    resultado["so_no_ledger"] = list(pendentes_ledger.values())
    resultado["so_no_extrato"] = list(pendentes_extrato.values())
    return resultado


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    ledger, extrato = gerar_lancamentos()
    resultado = conciliar(ledger, extrato)

    print("=== RESULTADO DA CONCILIACAO ===")
    total = len(ledger) + len(extrato)
    pareado = len(resultado["conciliados"]) + len(resultado["diferenca_valor"])
    print(f"- conciliados (valor exato) : {len(resultado['conciliados'])}")
    print(
        f"- diferenca de valor/tarifa : {len(resultado['diferenca_valor'])} (ex.: {resultado['diferenca_valor'][:3]})"
    )
    print(f"- apenas no LEDGER          : {len(resultado['so_no_ledger'])}")
    print(f"- apenas no EXTRATO         : {len(resultado['so_no_extrato'])} (tarifas/duplicatas esperadas aqui)")

    taxa_auto = len(resultado["conciliados"]) / max(total / 2, 1)
    print(f"\nTaxa de conciliacao automatica: {taxa_auto:.1%}")

    pendencias = pd.DataFrame(
        [{"origem": "ledger", **item} for item in resultado["so_no_ledger"]]
        + [{"origem": "extrato", **item} for item in resultado["so_no_extrato"]]
    )
    caminho = "outputs/conciliacao_pendencias.csv"
    pendencias.to_csv(caminho, index=False)
    print(f"Pendencias salvas em {caminho}")
