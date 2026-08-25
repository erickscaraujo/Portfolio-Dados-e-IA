"""Orquestra treino (se necessario) e a pontuacao em batch com checagem de drift."""

import json
import pathlib
from pathlib import Path

import joblib
import numpy as np
from pontuacao import pontuar_lote
from sklearn.ensemble import GradientBoostingClassifier

CAMINHO_MODELO = Path("outputs/modelo_batch.joblib")
CAMINHO_BASELINE = Path("outputs/baseline_scores.json")
SEED = 5


def treinar_e_salvar_baseline() -> None:
    rng = np.random.default_rng(SEED)
    n = 12_000
    renda = rng.lognormal(8.2, 0.5, n)
    divida = rng.beta(2, 6, n)
    atrasos = rng.poisson(0.9, n)

    logit = -1.6 + 5.2 * divida + 0.42 * atrasos - 0.00032 * renda + rng.normal(0, 0.8, n)
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    X = np.column_stack([renda / 10_000, divida, atrasos])

    modelo = GradientBoostingClassifier(random_state=SEED)
    modelo.fit(X, y)

    # baseline do score em treino: quantis servem de bins estaveis para o PSI futuro
    probabilidades_treino = modelo.predict_proba(X)[:, 1]
    quantis = np.quantile(probabilidades_treino, np.linspace(0, 1, 11)).tolist()

    CAMINHO_MODELO.parent.mkdir(exist_ok=True)
    joblib.dump(modelo, CAMINHO_MODELO)
    CAMINHO_BASELINE.write_text(json.dumps({"quantis": quantis}), encoding="utf-8")
    print("modelo treinado e baseline salvo")


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    if not CAMINHO_MODELO.exists():
        print("Primeira execucao: treinando modelo...")
        treinar_e_salvar_baseline()
    else:
        print("Reaproveitando modelo existente.")

    modelo = joblib.load(CAMINHO_MODELO)
    baseline = json.loads(CAMINHO_BASELINE.read_text(encoding="utf-8"))

    cenarios = {
        "carteira_normal": {"total": 20_000, "drift_renda": 1.0},
        "carteira_crise": {"total": 15_000, "drift_renda": 1.45},
    }
    for nome, config in cenarios.items():
        saida = f"outputs/scored_{nome}.csv"
        resumo = pontuar_lote(modelo, config["total"], saida, baseline, drift_renda=config["drift_renda"])
        print(f"\n=== {nome} ===")
        for chave, valor in resumo.items():
            print(f"- {chave}: {valor}")
