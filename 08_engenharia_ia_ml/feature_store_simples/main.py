"""Feature store minimalista: uma unica funcao alimenta treino e serving."""

import pathlib
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

CAMINHO_STORE = "outputs/online_store.db"
TTL_SEGUNDOS = 60


def calcular_features(transacoes: pd.DataFrame, data_referencia: datetime) -> pd.DataFrame:
    """Fonte unica de verdade: treino e online chamam ESTA funcao (consistencia)."""
    janela = transacoes[transacoes["data"] <= pd.Timestamp(data_referencia)]
    return (
        janela.groupby("cliente_id")
        .apply(
            lambda g: pd.Series(
                {
                    "recencia_dias": (data_referencia - g["data"].max().to_pydatetime()).days,
                    "frequencia_90d": int((g["data"] >= pd.Timestamp(data_referencia) - timedelta(days=90)).sum()),
                    "valor_medio": round(float(g["valor"].mean()), 2),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )


def gerar_transacoes(n_clientes: int = 300, seed: int = 61) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    linhas = []
    for cliente in range(1, n_clientes + 1):
        n_compras = int(rng.integers(2, 15))
        dias = rng.integers(1, 200, n_compras)
        for dia in dias:
            linhas.append(
                {
                    "cliente_id": cliente,
                    "data": datetime(2025, 6, 30) - timedelta(days=int(dia)),
                    "valor": round(float(rng.lognormal(5, 0.8)), 2),
                }
            )
    return pd.DataFrame(linhas)


def publicar_online(transacoes: pd.DataFrame, data_referencia: datetime) -> None:
    """Job offline empurra as features calculadas para o lookup de baixa latencia."""
    pathlib.Path(CAMINHO_STORE).parent.mkdir(parents=True, exist_ok=True)
    features = calcular_features(transacoes, data_referencia)

    with closing(sqlite3.connect(CAMINHO_STORE)) as con:
        con.execute("DROP TABLE IF EXISTS features")
        con.execute(
            """CREATE TABLE features (
                   cliente_id INTEGER PRIMARY KEY,
                   recencia_dias INTEGER, frequencia_90d INTEGER,
                   valor_medio REAL, publicado_em TEXT)"""
        )
        agora = datetime.now().isoformat(timespec="seconds")
        con.executemany(
            "INSERT INTO features VALUES (?, ?, ?, ?, ?)",
            [
                (int(r.cliente_id), int(r.recencia_dias), int(r.frequencia_90d), float(r.valor_medio), agora)
                for r in features.itertuples(index=False)
            ],
        )
        con.commit()
    print(f"online store publicado com {len(features)} clientes")


_cache: dict[int, tuple[float, dict]] = {}


def servir_features(cliente_id: int) -> dict:
    """Caminho online: leitura do store com cache TTL curto."""
    agora = time.monotonic()
    if cliente_id in _cache and agora - _cache[cliente_id][0] < TTL_SEGUNDOS:
        return {**_cache[cliente_id][1], "origem": "cache"}

    with closing(sqlite3.connect(CAMINHO_STORE)) as con:
        linha = con.execute(
            "SELECT recencia_dias, frequencia_90d, valor_medio FROM features WHERE cliente_id = ?",
            (cliente_id,),
        ).fetchone()

    if linha is None:
        raise KeyError(f"cliente {cliente_id} sem features publicadas")

    features = {"recencia_dias": linha[0], "frequencia_90d": linha[1], "valor_medio": linha[2]}
    _cache[cliente_id] = (agora, features)
    return {**features, "origem": "store"}


if __name__ == "__main__":
    data_ref = datetime(2025, 6, 30)
    transacoes = gerar_transacoes()

    # consistencia treino x serving: mesma funcao, mesmo resultado
    offline = calcular_features(transacoes, data_ref).set_index("cliente_id")
    publicar_online(transacoes, data_ref)

    divergencias = 0
    for cliente in [7, 42, 128, 299]:
        servido = servir_features(cliente)
        origem = servido.pop("origem")
        igual = all(abs(servido[chave] - offline.loc[cliente, chave]) < 1e-9 for chave in servido)
        divergencias += not igual
        status = "consistente" if igual else "DIVERGENTE"
        print(f"cliente {cliente:>3}: {servido} [{origem}] -> {status}")

    # segunda chamada deve bater no cache
    repetido = servir_features(7)
    print(f"\nsegunda leitura do cliente 7: origem={repetido['origem']} (cache TTL={TTL_SEGUNDOS}s)")

    if divergencias == 0:
        print("Treino e serving consistentes por construcao.")
