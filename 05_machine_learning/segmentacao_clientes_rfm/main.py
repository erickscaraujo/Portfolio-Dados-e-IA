"""Segmentacao RFM com K-Means: escolha do k, perfis de negocio e personas."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

SEED = 10


def gerar_clientes(n: int = 1_500, seed: int = SEED) -> pd.DataFrame:
    """Quatro grupos naturais: VIP, fieis, novos e hibernando."""
    rng = np.random.default_rng(seed)
    grupos = [
        # (peso, recencia media, frequencia media, ticket medio)
        (0.15, 8, 12, 450),
        (0.30, 20, 10, 95),
        (0.35, 15, 2, 60),
        (0.20, 150, 4, 130),
    ]
    pedacos = []
    for peso, rec, freq, ticket in grupos:
        k = int(n * peso)
        pedacos.append(
            pd.DataFrame(
                {
                    "recencia_dias": np.clip(rng.normal(rec, rec * 0.5, k), 1, None).round(),
                    "frequencia_12m": rng.poisson(freq, k),
                    "ticket_medio": np.clip(rng.normal(ticket, ticket * 0.25, k), 15, None).round(2),
                }
            )
        )
    df = pd.concat(pedacos, ignore_index=True)
    df["cliente"] = [f"C{i:04d}" for i in range(len(df))]
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def avaliar_k(matriz: np.ndarray) -> tuple[int, dict]:
    inercias, silhuetas = {}, {}
    for k in range(2, 9):
        km = KMeans(n_clusters=k, n_init="auto", random_state=SEED).fit(matriz)
        inercias[k] = km.inertia_
        silhuetas[k] = silhouette_score(matriz, km.labels_)
    melhor_k = max(silhuetas, key=silhuetas.get)
    print("k | inercia   | silhueta")
    for k in sorted(inercias):
        marca = "  <- escolhido" if k == melhor_k else ""
        print(f"{k} | {inercias[k]:>9,.0f} | {silhuetas[k]:.3f}{marca}")
    return melhor_k, {"inercias": inercias, "silhuetas": silhuetas}


def nomear_personas(perfil: pd.DataFrame) -> dict[int, str]:
    """Rotulos por comparacao entre centroides em escala original.

    VIP = melhor combinacao de frequencia e ticket; Hibernando = pior recencia;
    entre os demais, quem compra mais vezes vira "Fieis" e o resto "Promissores".
    """
    padronizado = (perfil - perfil.mean()) / (perfil.std() + 1e-9)
    score_compra = padronizado["frequencia_12m"] + padronizado["ticket_medio"]

    rotulos: dict[int, str] = {}
    rotulos[score_compra.idxmax()] = "Clientes VIP"

    restantes = [i for i in perfil.index if i not in rotulos]
    hibernando = max(restantes, key=lambda i: perfil.loc[i, "recencia_dias"])
    rotulos[hibernando] = "Hibernando"

    for i in restantes:
        if i != hibernando:
            # frequencia acima da media dos centroides separa fieis de promissores
            rotulos[i] = "Fieis" if padronizado.loc[i, "frequencia_12m"] > 0 else "Promissores"
    return rotulos


RECOMENDACOES = {
    "Clientes VIP": "programa de exclusividade e early access",
    "Fieis": "cross-sell e cashback progressivo",
    "Promissores": "onboarding com cupom na segunda compra",
    "Hibernando": "campanha de reativacao com oferta agressiva",
}


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    clientes = gerar_clientes()
    features = ["recencia_dias", "frequencia_12m", "ticket_medio"]
    scaler = StandardScaler()
    matriz = scaler.fit_transform(clientes[features])

    print("=== ESCOLHA DO K ===")
    melhor_k, _ = avaliar_k(matriz)

    modelo = KMeans(n_clusters=melhor_k, n_init="auto", random_state=SEED)
    clientes["cluster"] = modelo.fit_predict(matriz)

    # centroides na escala original para leitura de negocio
    centroides = pd.DataFrame(scaler.inverse_transform(modelo.cluster_centers_), columns=features)
    rotulos = nomear_personas(centroides)
    clientes["persona"] = clientes["cluster"].map(rotulos)
    centroides["persona"] = centroides.index.map(rotulos)

    print(f"\n=== PERFIL DOS CLUSTERS (k={melhor_k}) ===")
    contagem = clientes["persona"].value_counts().rename_axis("persona").reset_index(name="clientes")
    print(contagem.to_string(index=False))
    print("\nMedias por persona:")
    print(centroides.set_index("persona").to_string(float_format=lambda x: f"{x:,.1f}"))

    print("\nAcao recomendada por segmento:")
    for persona, acao in RECOMENDACOES.items():
        qtd = (clientes["persona"] == persona).sum()
        if qtd:
            print(f"- {persona}: {acao}")

    reducao = PCA(n_components=2, random_state=SEED)
    coordenadas = reducao.fit_transform(matriz)
    plt.figure(figsize=(8, 5.5))
    for cluster_id, grupo in clientes.groupby("cluster"):
        plt.scatter(
            coordenadas[grupo.index, 0],
            coordenadas[grupo.index, 1],
            s=12,
            alpha=0.65,
            label=f"{rotulos[cluster_id]} ({len(grupo)})",
        )
    plt.title(f"Segmentacao RFM — K-Means (k={melhor_k}), projecao PCA")
    plt.xlabel("Componente 1")
    plt.ylabel("Componente 2")
    plt.legend(markerscale=1.8)
    plt.tight_layout()
    plt.savefig("outputs/segmentos_pca.png", dpi=120)

    clientes.to_csv("outputs/segmentos.csv", index=False)
    print("\nArtefatos salvos: outputs/segmentos.csv e outputs/segmentos_pca.png")
