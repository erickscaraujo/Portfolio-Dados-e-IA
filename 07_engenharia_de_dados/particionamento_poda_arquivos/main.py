"""Partition pruning: ler so as pastas necessarias em vez do lago inteiro."""

import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path("outputs/lake_particionado")
DIAS = 90
DATA_INICIO = date(2025, 4, 1)
SEED = 420


def gerar_particoes() -> None:

    rng = np.random.default_rng(SEED)
    for offset in range(DIAS):
        dia = DATA_INICIO + timedelta(days=offset)
        pasta_dia = RAIZ / f"data={dia.isoformat()}"
        if pasta_dia.exists():
            continue

        pasta_dia.mkdir(parents=True, exist_ok=True)
        n_eventos = int(rng.integers(300, 900))
        pd.DataFrame(
            {
                "evento": rng.choice(["view", "cart", "buy"], n_eventos),
                "valor": np.round(rng.uniform(0, 500, n_eventos), 2),
                "cliente_id": rng.integers(1, 800, n_eventos),
            }
        ).to_csv(pasta_dia / "vendas.csv", index=False)


def _ler_arquivos(arquivos: list[Path]) -> pd.DataFrame:
    return pd.concat((pd.read_csv(arquivo) for arquivo in arquivos), ignore_index=True)


def consulta_ingenua() -> tuple[pd.DataFrame, int, float]:
    inicio = time.perf_counter()
    arquivos = list(RAIZ.rglob("vendas.csv"))  # varre o lago inteiro
    df = _ler_arquivos(arquivos)
    return df, len(arquivos), time.perf_counter() - inicio


def consulta_com_poda(mes: str) -> tuple[pd.DataFrame, int, float]:
    """Só abre partições cujo sufixo `data=` começa com o mês pedido."""
    inicio = time.perf_counter()
    arquivos = [
        arquivo
        for pasta in RAIZ.iterdir()
        if pasta.is_dir() and f"data={mes}" in pasta.name
        for arquivo in pasta.glob("vendas.csv")
    ]
    df = _ler_arquivos(arquivos)
    return df, len(arquivos), time.perf_counter() - inicio


if __name__ == "__main__":
    print(f"Gerando {DIAS} particoes diarias (se nao existirem)...")
    gerar_particoes()

    mes_alvo = "2025-05"

    _, arquivos_sem_poda, tempo_sem = consulta_ingenua()
    resultado, arquivos_com_poda, tempo_com = consulta_com_poda(mes_alvo)

    resumo = resultado.groupby("evento")["valor"].sum().round(2)

    print("\n=== CONSULTA: receita por evento em um mes ===")
    print(resumo.to_string())

    speedup = tempo_sem / max(tempo_com, 1e-6)
    print("\n=== CUSTO DA CONSULTA ===")
    print(f"- sem poda : leu {arquivos_sem_poda:>3} arquivos em {tempo_sem * 1000:.1f} ms")
    print(f"- com poda : leu {arquivos_com_poda:>3} arquivos em {tempo_com * 1000:.1f} ms ({speedup:.1f}x)")
    print(f"- economia : {(1 - arquivos_com_poda / arquivos_sem_poda):.0%} dos arquivos ignorados")

    print("\nMesmo principio do Spark/Hive: filtre pela coluna de particao e o engine")
    print("abre apenas os diretorios relevantes.")
