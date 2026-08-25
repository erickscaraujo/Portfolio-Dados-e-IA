"""Geracao da base sintetica de vendas de varejo."""

import numpy as np
import pandas as pd

LOJAS = {"Centro": 0.30, "Shopping": 0.35, "Online": 0.25, "Bairro": 0.10}

# preco base e custo por categoria mantêm margens plausíveis por segmento
CATEGORIAS = {
    "Eletronicos": {"preco": 850.0, "margem_custo": 0.72},
    "Vestuario": {"preco": 120.0, "margem_custo": 0.45},
    "Alimentos": {"preco": 28.0, "margem_custo": 0.75},
    "Casa e Decoracao": {"preco": 260.0, "margem_custo": 0.60},
    "Beleza": {"preco": 75.0, "margem_custo": 0.50},
}

PRODUTOS_POR_CATEGORIA = {
    "Eletronicos": ["Fone Bluetooth", "Smartwatch", "Carregador Turbo", "Caixa de Som"],
    "Vestuario": ["Camiseta Premium", "Calca Jeans", "Tenis Esportivo", "Casaco"],
    "Alimentos": ["Cafe Especial", "Chocolate Fino", "Azeite", "Castanhas"],
    "Casa e Decoracao": ["Luminaria", "Jogo de Toalhas", "Quadro Decorativo", "Difusor"],
    "Beleza": ["Perfume", "Kit Skincare", "Secador", "Maquiagem"],
}


def gerar_vendas(qtd_pedidos: int = 9000, seed: int = 42) -> pd.DataFrame:
    """Gera pedidos individuais ao longo de 18 meses com sazonalidade leve."""
    rng = np.random.default_rng(seed)
    datas = pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 546, qtd_pedidos), unit="D")

    lojas = rng.choice(list(LOJAS), size=qtd_pedidos, p=list(LOJAS.values()))
    categorias = rng.choice(
        list(CATEGORIAS),
        size=qtd_pedidos,
        p=[0.22, 0.28, 0.25, 0.15, 0.10],
    )

    produtos = [rng.choice(PRODUTOS_POR_CATEGORIA[c]) for c in categorias]
    precos_base = np.array([CATEGORIAS[c]["preco"] for c in categorias])
    # preco varia +/-20% em torno da media da categoria
    preco_unitario = np.round(precos_base * rng.normal(1.0, 0.12, qtd_pedidos), 2)
    custos = np.round(preco_unitario * np.array([CATEGORIAS[c]["margem_custo"] for c in categorias]), 2)

    # novembro/dezembro vende mais (black friday + natal)
    fator_sazonal = np.where(datas.month.isin([11, 12]), rng.integers(2, 5, qtd_pedidos), 1)
    quantidade = np.clip(rng.poisson(1.4, qtd_pedidos) + 1, 1, None) * fator_sazonal

    df = pd.DataFrame(
        {
            "id_pedido": [f"PED{i:06d}" for i in range(qtd_pedidos)],
            "data": datas,
            "loja": lojas,
            "categoria": categorias,
            "produto": produtos,
            "quantidade": quantidade,
            "preco_unitario": preco_unitario,
            "custo_unitario": custos,
        }
    )
    return df.sort_values("data").reset_index(drop=True)
