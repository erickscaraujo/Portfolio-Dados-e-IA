"""Funil de conversao do e-commerce: onde os clientes desistem?"""

import pathlib

import numpy as np
import pandas as pd
from funil import montar_html, salvar

ETAPAS = ["visita", "carrinho", "checkout", "compra"]
TAXAS_BASE = {"visita": 1.00, "carrinho": 0.34, "checkout": 0.62, "compra": 0.71}
MULTIPLICADOR_DISPOSITIVO = {"desktop": 1.10, "mobile": 0.92}

SESSOES_POR_DIA = 900
DIAS = 60
SEED = 21


def simular_sessoes() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    dispositivo = rng.choice(list(MULTIPLICADOR_DISPOSITIVO), DIAS * SESSOES_POR_DIA)

    df = pd.DataFrame({"dispositivo": dispositivo})
    df["visita"] = True  # todo o funil parte da sessao aberta
    prob_acumulada = pd.Series(1.0, index=df.index)
    for etapa in ETAPAS[1:]:
        mult = df["dispositivo"].map(MULTIPLICADOR_DISPOSITIVO)
        prob_acumulada *= TAXAS_BASE[etapa] * mult
        df[etapa] = rng.random(len(df)) < prob_acumulada
    return df


def contagens(df: pd.DataFrame) -> list[dict]:
    return [{"etapa": etapa, "usuarios": int(df[etapa].sum())} for etapa in ETAPAS]


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    sessoes = simular_sessoes()

    print("=== FUNIL GERAL ===")
    etapas_geral = contagens(sessoes)
    for i, etapa in enumerate(etapas_geral):
        taxa = "-" if i == 0 else f"{etapa['usuarios'] / etapas_geral[i - 1]['usuarios']:.1%}"
        print(f"- {etapa['etapa']:<9} {etapa['usuarios']:>7,}  (step: {taxa})")

    queda_maior = max(
        range(1, len(ETAPAS)),
        key=lambda i: 1 - etapas_geral[i]["usuarios"] / etapas_geral[i - 1]["usuarios"],
    )
    print(
        f"\nMaior vazamento: {ETAPAS[queda_maior - 1]} -> {ETAPAS[queda_maior]} "
        f"({etapas_geral[queda_maior]['usuarios'] / etapas_geral[queda_maior - 1]['usuarios']:.0%} avancam)"
    )

    conversao_por_dispositivo = {}
    for dispositivo in MULTIPLICADOR_DISPOSITIVO:
        grupo = sessoes[sessoes["dispositivo"] == dispositivo]
        contagens_grupo = [int(grupo[etapa].sum()) for etapa in ETAPAS]
        passos = [
            {"de": ETAPAS[i], "para": ETAPAS[i + 1], "taxa": contagens_grupo[i + 1] / contagens_grupo[i]}
            for i in range(len(ETAPAS) - 1)
        ]
        conversao_por_dispositivo[dispositivo] = passos
        print(f"- {dispositivo}: checkout->compra {passos[2]['taxa']:.0%}")

    caminho = salvar(montar_html(etapas_geral, conversao_por_dispositivo))
    print(f"\nHTML salvo em {caminho}")
