"""Lakehouse medallion: bronze (raw) -> silver (confiavel) -> gold (consumo)."""

import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RAIZ_LAKE = Path("outputs/lakehouse")
SEED = 40


def _manifest(pasta: Path, arquivos: list[str], linhas: int) -> None:
    pasta.joinpath("_manifest.json").write_text(
        json.dumps(
            {
                "gerado_em": datetime.now().isoformat(timespec="seconds"),
                "arquivos": arquivos,
                "linhas": linhas,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def camada_bronze(n_eventos: int = 4_000) -> pd.DataFrame:
    """Ingestao fiel da fonte: nada de limpeza aqui, so capturar como veio."""
    rng = np.random.default_rng(SEED)
    eventos = pd.DataFrame(
        {
            "id": range(1, n_eventos + 1),
            "ts": (
                pd.Timestamp("2025-03-01") + pd.to_timedelta(rng.integers(0, 86_400 * 30, n_eventos), unit="s")
            ).astype(str),
            "cliente": rng.integers(1, 500, n_eventos),
            "evento": rng.choice(["view", "cart", "buy"], n_eventos, p=[0.6, 0.25, 0.15]),
            "valor": np.round(rng.uniform(0, 900, n_eventos), 2),
        }
    )
    # sujeira tipica de raw: duplicatas de envio e tipos inconsistentes em 2% das linhas
    ruidos = eventos.sample(80, random_state=SEED).assign(valor=lambda d: d["valor"].astype(str))
    bruto = pd.concat([eventos, ruidos], ignore_index=True)

    pasta = RAIZ_LAKE / "bronze"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / "eventos_2025_03.json"
    destino.write_text(bruto.to_json(orient="records", lines=False), encoding="utf-8")

    _manifest(pasta, [destino.name], len(bruto))
    logger.info("bronze: %d eventos brutos gravados", len(bruto))
    return bruto


def camada_silver(bruto: pd.DataFrame) -> pd.DataFrame:
    """Contrato minimo: tipos corretos, dedup por id e remocao de lixo."""
    prata = bruto.copy()
    prata["valor"] = pd.to_numeric(prata["valor"], errors="coerce")
    prata["ts"] = pd.to_datetime(prata["ts"], errors="coerce")

    antes = len(prata)
    prata = (
        prata.dropna(subset=["ts"])
        .sort_values("id")
        .drop_duplicates(subset="id", keep="last")  # mantem a ultima chegada
        .query("valor >= 0 or evento != 'buy'")
        .reset_index(drop=True)
    )

    pasta = RAIZ_LAKE / "silver"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / "eventos_confiveis.csv"
    prata.to_csv(destino, index=False)

    _manifest(pasta, [destino.name], len(prata))
    logger.info("silver: %d -> %d registros confiaveis", antes, len(prata))
    return prata


def camada_gold(prata: pd.DataFrame) -> pd.DataFrame:
    """Modelo de consumo pronto para BI: receita diaria por evento."""
    ouro = (
        prata.assign(dia=prata["ts"].dt.date.astype(str))
        .groupby(["dia", "evento"], as_index=False)["valor"]
        .sum()
        .rename(columns={"valor": "receita_total"})
        .round(2)
    )
    pasta = RAIZ_LAKE / "gold"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / "receita_diaria.csv"
    ouro.to_csv(destino, index=False)

    _manifest(pasta, [destino.name], len(ouro))
    logger.info("gold: %d agregados diarios para consumo", len(ouro))
    return ouro


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s | %(message)s")

    bruto = camada_bronze()
    confiavel = camada_silver(bruto)
    receita = camada_gold(confiavel)

    print("\n=== GOLD: RECEITA DIARIA (amostra) ===")
    print(receita.head(6).to_string(index=False))

    print("\nEstrutura do lake:")
    for arquivo in sorted(RAIZ_LAKE.rglob("*")):
        if arquivo.is_file():
            print(f" - {arquivo.relative_to(RAIZ_LAKE)}")
