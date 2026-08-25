"""Agrupa series de venda de produtos por padrao (tendencia/sazonalidade/estabilidade)."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

DIAS = 180
SEED = 8


def gerar_series(n_produtos: int = 120) -> pd.DataFrame:
    """Quatro assinaturas: crescimento, declinio, sazonal semanal e estavel."""
    rng = np.random.default_rng(SEED)
    dias = np.arange(DIAS)
    registros = []

    assinaturas = {
        "crescimento": lambda r: 30 + dias * 0.12 + r.normal(0, 5, DIAS),
        "declinio": lambda r: 60 - dias * 0.18 + r.normal(0, 6, DIAS),
        "sazonal": lambda r: 45 + 16 * ((dias % 7 >= 4).astype(float)) + r.normal(0, 4, DIAS),
        "estavel": lambda r: 40 + r.normal(0, 3, DIAS),
    }

    for produto in range(n_produtos):
        nome_padrao = list(assinaturas)[produto % len(assinaturas)]
        vendas = np.clip(assinaturas[nome_padrao](rng), 2, None).round()

        for dia, quantidade in enumerate(vendas):
            registros.append(
                {
                    "produto": f"SKU{produto:03d}",
                    "dia": dia,
                    "vendas": quantidade,
                }
            )

    return pd.DataFrame(registros)


def extrair_features(serie: pd.Series) -> dict:
    """Tres numeros resumem o comportamento da serie para o cluster."""
    inclinacao = float(np.polyfit(np.arange(len(serie)), serie.to_numpy(), 1)[0])

    # forca sazonal = quanto do desvio total os dias da semana explicam
    por_dia_semana = serie.groupby(serie.index % 7).mean()
    variancia_entre_dias = np.var(por_dia_semana.to_numpy())
    forca_sazonal = variancia_entre_dias / max(np.var(serie.to_numpy()), 1e-9)

    return {
        "inclinacao": round(inclinacao, 3),
        "forca_sazonal": round(forca_sazonal, 3),
        "cv": round(float(serie.std() / serie.mean()), 3),
    }


def nomear_cluster(inclinacao: float, forca_sazonal: float) -> str:
    if inclinacao > 0.03:
        return "Crescendo"
    if inclinacao < -0.03:
        return "Em declinio"
    if forca_sazonal > 0.15:
        return "Sazonal semanal"
    return "Estavel"


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_series()
    features = pd.DataFrame(
        [extrair_features(grupo["vendas"]) for _, grupo in base.groupby("produto")],
        index=sorted(base["produto"].unique()),
    )

    escalador = StandardScaler()
    matriz = escalador.fit_transform(features)
    silhuetas = {
        k: silhouette_score(matriz, KMeans(k, n_init="auto", random_state=SEED).fit_predict(matriz))
        for k in range(2, 7)
    }
    melhor_k = max(silhuetas, key=silhuetas.get)
    print("Silhueta por k:", {k: round(v, 3) for k, v in silhuetas.items()})

    modelo = KMeans(n_clusters=melhor_k, n_init="auto", random_state=SEED)
    features["cluster"] = modelo.fit_predict(matriz)

    # rotulo de negocio pelo comportamento da serie, nao pelo id do cluster
    centroides = pd.DataFrame(escalador.inverse_transform(modelo.cluster_centers_), columns=features.columns[:3])
    features["padrao"] = [
        nomear_cluster(features.loc[i, "inclinacao"], features.loc[i, "forca_sazonal"]) for i in features.index
    ]

    print("\n=== PRODUTOS POR PADRAO ===")
    contagem = features.groupby("padrao")["inclinacao"].count().sort_values(ascending=False)
    print(contagem.to_string())

    print("\nPerfil medio das features por padrao:")
    print(features.groupby("padrao")[["inclinacao", "forca_sazonal", "cv"]].mean().round(3).to_string())

    acoes = {
        "Crescendo": "garantir estoque e capacidade logistica",
        "Em declinio": "revisar preco, promocao ou substituicao",
        "Sazonal semanal": "planejar reposicao para fim de semana",
        "Estavel": "automatizar reposicao por ponto de pedido",
    }
    print("\nAcoes recomendadas:")
    for padrao, acao in acoes.items():
        if padrao in contagem.index:
            print(f"- {padrao}: {acao}")

    fig, eixos = plt.subplots(melhor_k, 1, figsize=(10, 2.6 * melhor_k), sharex=True)
    eixos = np.atleast_1d(eixos)
    for ax, padrao in zip(eixos, contagem.index, strict=False):
        exemplos = features[features["padrao"] == padrao].index[:3]
        for sku in exemplos:
            serie = base[base["produto"] == sku]["vendas"]
            ax.plot(serie.values, alpha=0.75, lw=1.2, label=sku)
        ax.set_title(f"Padrao: {padrao} ({contagem[padrao]} produtos)")
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig("outputs/padroes_series.png", dpi=120)
    print("\nGrade visual salva em outputs/padroes_series.png")
