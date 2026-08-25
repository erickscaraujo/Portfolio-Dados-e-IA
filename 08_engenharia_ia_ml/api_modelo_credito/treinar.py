"""Treino do modelo de risco de credito com artefatos versionados para a API."""

import json
import pathlib
from datetime import datetime

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SEED = 8
FEATURES_NUMERICAS = [
    "renda",
    "idade",
    "tempo_emprego_anos",
    "divida_sobre_renda",
    "score_serasa",
    "atrasos_12m",
]

CAMINHO_MODELO = "outputs/modelo_credito.joblib"
CAMINHO_METADATA = "outputs/metadata_modelo.json"


def gerar_base(n: int = 6_000, seed: int = SEED) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    renda = rng.lognormal(8.3, 0.5, n)
    idade = rng.integers(21, 70, n)
    tempo_emprego = np.clip(rng.normal(8, 6, n), 0, idade - 18).round(1)
    divida_renda = rng.beta(2, 6, n).round(3)
    score_serasa = rng.integers(280, 900, n)
    atrasos = rng.poisson(0.9, n)

    # inadimplencia cresce com endividamento, atrasos e cai com renda/score
    logit = (
        -1.6
        + 5.5 * divida_renda
        + 0.45 * atrasos
        - 0.00035 * renda
        - 0.006 * (score_serasa - 500)
        + rng.normal(0, 0.9, n)
    )
    y = rng.binomial(1, 1 / (1 + np.exp(-logit)))
    X = np.column_stack([renda, idade, tempo_emprego, divida_renda, score_serasa, atrasos])
    return X, y


def main() -> None:
    pathlib.Path("outputs").mkdir(exist_ok=True)

    X, y = gerar_base()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)

    pipeline = Pipeline(
        [
            ("escala", StandardScaler()),
            ("modelo", RandomForestClassifier(300, max_depth=10, random_state=SEED, n_jobs=-1)),
        ]
    )
    pipeline.fit(X_tr, y_tr)

    auc = roc_auc_score(y_te, pipeline.predict_proba(X_te)[:, 1])
    print(f"AUC holdout: {auc:.3f}")

    metadata = {
        "versao": "1.0.0",
        "treinado_em": datetime.now().isoformat(timespec="seconds"),
        "features": FEATURES_NUMERICAS,
        "metrica_auc": round(float(auc), 4),
        "algoritmo": "RandomForestClassifier(300, max_depth=10)",
        "observacoes": "Dados sinteticos; substituir por base real antes de uso em producao.",
    }
    joblib.dump(pipeline, CAMINHO_MODELO)
    with open(CAMINHO_METADATA, "w", encoding="utf-8") as arq:
        json.dump(metadata, arq, ensure_ascii=False, indent=2)

    print(f"Modelo salvo em {CAMINHO_MODELO}")
    print(f"Metadata salva em {CAMINHO_METADATA}")


if __name__ == "__main__":
    main()
