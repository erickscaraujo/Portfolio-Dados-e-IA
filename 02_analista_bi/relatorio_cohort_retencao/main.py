"""Cohort de retencao: quando os clientes adquiridos voltam a comprar?"""

import pathlib

import numpy as np
import pandas as pd
from cohort import montar_html, salvar

MESES_HISTORICO = 12
SEED = 17


def gerar_pedidos(n_clientes: int = 900) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    registros = []

    for cliente in range(n_clientes):
        mes_aquisicao = int(rng.integers(0, MESES_HISTORICO))
        # primeira compra marca o cohort
        registros.append((cliente, mes_aquisicao))

        # probabilidade de recompra cai com o offset e varia por cliente (lealdade latente)
        lealdade = rng.beta(1.5, 3.0)
        for offset in range(1, MESES_HISTORICO - mes_aquisicao):
            if rng.random() < lealdade * np.exp(-0.35 * offset):
                registros.append((cliente, mes_aquisicao + offset))

    return pd.DataFrame(registros, columns=["cliente", "mes_absoluto"])


def construir_matriz(pedidos: pd.DataFrame) -> tuple[dict[str, list[float | None]], list[str]]:
    primeiro = pedidos.groupby("cliente")["mes_absoluto"].min().rename("cohort")
    base = pedidos.merge(primeiro, on="cliente")
    base["offset"] = base["mes_absoluto"] - base["cohort"]
    base["comprou"] = 1

    unicos = base[["cliente", "cohort", "offset"]].drop_duplicates()
    matriz = unicos.pivot_table(index="cohort", columns="offset", values="cliente", aggfunc="count")

    tamanho_cohort = unicos.groupby("cohort")["cliente"].nunique()
    rotulos = [(pd.Period("2024-01", freq="M") + i).strftime("%b/%y") for i in sorted(matriz.index)]

    coortes: dict[str, list[float | None]] = {}
    for i, (cohort, linha) in enumerate(matriz.iterrows()):
        total = int(tamanho_cohort.loc[cohort])
        valores: list[float | None] = []
        for offset in range(MESES_HISTORICO):
            if offset in linha.index and not np.isnan(linha.get(offset)):
                valores.append(round(linha[offset] / total * 100, 1))
            elif offset <= MESES_HISTORICO - 1 - i:
                # mes ja ocorreu mas ninguem comprou -> retencao zero real
                valores.append(0.0)
            else:
                valores.append(None)  # futuro: ainda nao observado
        coortes[rotulos[i]] = valores
    return coortes, rotulos


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    pedidos = gerar_pedidos()
    coortes, meses_offset = construir_matriz(pedidos)

    caminho = salvar(montar_html(coortes, meses_offset))

    print("=== MATRIZ DE RETENCAO (%) ===")
    larguras = max(len(c) for c in coortes)
    print(f"{'cohort':<{larguras}}", *[f"{m:>7}" for m in meses_offset])
    for nome, valores in coortes.items():
        celulas = ["-" if v is None else f"{v:>6.1f}" for v in valores]
        print(f"{nome:<{larguras}}", *[f"{c:>7}" for c in celulas])

    offsets_validos = [[valores[i] for valores in coortes.values() if valores[i] is not None] for i in range(1, 5)]
    print("\nRetencao media por offset:")
    for offset, valores in enumerate(offsets_validos, start=1):
        if valores:
            print(f"M+{offset}: {np.mean(valores):.1f}%")

    print(f"\nHTML salvo em {caminho}")
