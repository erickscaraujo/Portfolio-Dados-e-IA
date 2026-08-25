"""Demonstracao do catalogo + linhagem sobre um mini data warehouse de vendas."""

import pathlib

import numpy as np
import pandas as pd
from catalogo import Catalogo
from linhagem import Linhagem


def montar_camada_raw(seed: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    vendas = pd.DataFrame(
        {
            "pedido_id": range(1000),
            "cliente_id": rng.integers(1, 300, 1000),
            "valor": rng.lognormal(6, 0.7, 1000).round(2),
            "data": pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, 1000), unit="D"),
        }
    )
    clientes = pd.DataFrame(
        {
            "cliente_id": range(1, 320),
            "nome": [f"Cliente {i}" for i in range(1, 320)],
            "regiao": rng.choice(["Norte", "Sul", "Leste", "Oeste"], 319),
        }
    )
    return vendas, clientes


def main() -> None:
    pathlib.Path("outputs").mkdir(exist_ok=True)
    catalogo = Catalogo()
    grafo = Linhagem()

    vendas, clientes = montar_camada_raw()
    catalogo.registrar(vendas, "raw_vendas", "sistema_pdv")
    catalogo.registrar(clientes, "raw_clientes", "crm")

    # camada staging: juncao e tipagem
    stg = vendas.merge(clientes, on="cliente_id", how="inner")
    stg["mes"] = stg["data"].dt.to_period("M").astype(str)
    catalogo.registrar(stg, "stg_vendas_completa", "pipeline_diario")
    grafo.adicionar("raw_vendas", "stg_vendas_completa", "join + derivacao mes")
    grafo.adicionar("raw_clientes", "stg_vendas_completa", "join")

    # camada fato e agregado para o BI
    fato = stg[["pedido_id", "cliente_id", "valor", "regiao", "mes"]]
    agg = fato.groupby(["mes", "regiao"], as_index=False)["valor"].sum().rename(columns={"valor": "receita"})
    catalogo.registrar(fato, "ft_vendas", "pipeline_diario")
    catalogo.registrar(agg, "agg_dashboard_bi", "job_noturno")
    grafo.adicionar("stg_vendas_completa", "ft_vendas", "selecao de colunas")
    grafo.adicionar("ft_vendas", "agg_dashboard_bi", "group by mes/regiao")

    print("=== CATALOGO ===")
    print(catalogo.resumo())

    print("\n" + grafo.mostrar_arvore("raw_vendas", direcao=1))
    print("\nImpacto de alterar raw_vendas:", ", ".join(grafo.downstream("raw_vendas")))
    print("Fontes do dashboard BI :", ", ".join(grafo.upstream("agg_dashboard_bi")))

    meta = catalogo.buscar("stg_vendas_completa")
    if meta:
        print(f"\nPerfil de stg_vendas_completa -> linhas: {meta.linhas}, esquema: {list(meta.esquema)}")

    catalogo.salvar("outputs/catalogo.json")
    print("\nCatalogo persistido em outputs/catalogo.json")


if __name__ == "__main__":
    main()
