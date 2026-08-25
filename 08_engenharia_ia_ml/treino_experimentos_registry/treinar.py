"""Grid de hiperparametros com cada combinacao registrada como um run rastreavel."""

import pathlib

import joblib
import numpy as np
from registro import melhor_run, registrar_run
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

EXPERIMENTO = "churn_grid"
SEED = 3


def gerar_base(n: int = 3_500, seed: int = SEED):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 6))
    logit = 2.2 * X[:, 0] - 1.4 * X[:, 1] + 0.8 * X[:, 2] * X[:, 3] + rng.normal(0, 1.2, n)
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    return X, y


GRID = [
    {"n_estimators": 120, "max_depth": 6},
    {"n_estimators": 120, "max_depth": None},
    {"n_estimators": 300, "max_depth": 6},
    {"n_estimators": 300, "max_depth": 12},
]


def main() -> int:
    pathlib.Path("outputs/modelos").mkdir(parents=True, exist_ok=True)

    X, y = gerar_base()

    print(f"=== EXPERIMENTO '{EXPERIMENTO}': {len(GRID)} runs ===")
    for params in GRID:
        modelo = make_pipeline(
            StandardScaler(),
            RandomForestClassifier(random_state=SEED, n_jobs=-1, **params),
        )
        auc_cv = cross_val_score(modelo, X, y, cv=5, scoring="roc_auc").mean()
        modelo.fit(X, y)

        caminho_modelo = pathlib.Path("outputs/modelos") / (
            f"rf_{params['n_estimators']}_{params['max_depth'] or 'inf'}.joblib"
        )
        joblib.dump(modelo, caminho_modelo)

        run_id = registrar_run(
            experimento=EXPERIMENTO,
            params=params,
            metricas={"auc_cv": round(float(auc_cv), 4)},
            artefato=caminho_modelo,
        )
        print(f"- run {run_id} | {params} | AUC-CV {auc_cv:.4f}")

    vencedor = melhor_run(EXPERIMENTO, "auc_cv")
    print("\n=== MELHOR RUN (do registro, nao da memoria) ===")
    print(f"run_id   : {vencedor['run_id']}")
    print(f"params   : {vencedor['params']}")
    print(f"metrica  : AUC-CV {vencedor['metricas']['auc_cv']}")
    print(f"artefato : {vencedor['artefato']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
