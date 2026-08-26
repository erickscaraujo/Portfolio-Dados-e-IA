"""Previsao de churn em telecom: pipeline completo de classificacao com comparativo de modelos."""

import matplotlib

matplotlib.use("Agg")

import pathlib

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import RocCurveDisplay, confusion_matrix, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
NUMERICAS = ["meses_contrato", "fatura_mensal", "chamados_suporte", "uso_gb_mes"]
CATEGORICAS = ["plano", "tipo_pagamento"]


def gerar_clientes(n: int = 4_000, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    plano = rng.choice(["Basico", "Medio", "Premium"], n, p=[0.45, 0.35, 0.20])
    meses_contrato = rng.gamma(2.2, 11, n).clip(1, 72).round()

    # fatura cresce com o plano + ruido individual
    base_plano = pd.Series(plano).map({"Basico": 55, "Medio": 90, "Premium": 140}).to_numpy()
    fatura_mensal = (base_plano * rng.normal(1, 0.12, n)).round(2)

    chamados_suporte = rng.poisson(0.8, n)
    uso_gb_mes = rng.lognormal(3.2, 0.6, n).round(1)

    # probabilidade de saida sobe com reclamacoes e contratos curtos
    logit = (
        -1.6 + 0.38 * chamados_suporte - 0.055 * meses_contrato + 0.008 * (fatura_mensal - 90) + rng.normal(0, 0.7, n)
    )
    churn = rng.binomial(1, 1 / (1 + np.exp(-logit)))

    return pd.DataFrame(
        {
            "plano": plano,
            "tipo_pagamento": rng.choice(["cartao", "boleto", "debito"], n),
            "meses_contrato": meses_contrato.astype(int),
            "fatura_mensal": fatura_mensal,
            "chamados_suporte": chamados_suporte,
            "uso_gb_mes": uso_gb_mes,
            "churn": churn,
        }
    )


def construir_pipeline(modelo) -> Pipeline:
    pre_processamento = ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERICAS),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS),
        ]
    )
    return Pipeline([("prep", pre_processamento), ("modelo", modelo)])


def avaliar(nome: str, pipeline: Pipeline, X_tr, y_tr, X_te, y_te) -> tuple[float, Pipeline]:
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    auc_cv = cross_val_score(pipeline, X_tr, y_tr, cv=cv, scoring="roc_auc").mean()
    pipeline.fit(X_tr, y_tr)
    probas = pipeline.predict_proba(X_te)[:, 1]
    preditos = pipeline.predict(X_te)
    auc = roc_auc_score(y_te, probas)
    precisao, recall, f1, _ = precision_recall_fscore_support(y_te, preditos, average="binary")
    print(f"\n--- {nome} ---")
    print(f"AUC CV(5 folds): {auc_cv:.3f} | AUC holdout: {auc:.3f}")
    print(f"Precisao: {precisao:.3f} | Recall: {recall:.3f} | F1: {f1:.3f}")
    return auc, pipeline


def matriz_confusao_texto(y_real, y_predito) -> str:
    vn, fp, fn, vp = confusion_matrix(y_real, y_predito).ravel()
    return f"                 Previsto fica | sai\nReal fica      {vn:>9} | {fp:>5}\nReal sai       {fn:>9} | {vp:>5}"


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_clientes()
    print("Distribuicao da variavel alvo:")
    print(base["churn"].value_counts(normalize=True).rename({0: "fica", 1: "sai"}).to_string())

    X = base.drop(columns="churn")
    y = base["churn"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)

    modelos = {
        "Regressao Logistica": construir_pipeline(LogisticRegression(max_iter=1200, class_weight="balanced")),
        "Random Forest": construir_pipeline(
            RandomForestClassifier(250, max_depth=10, random_state=SEED, class_weight="balanced", n_jobs=-1)
        ),
    }
    avaliacoes = {nome: avaliar(nome, pipe, X_tr, y_tr, X_te, y_te) for nome, pipe in modelos.items()}

    melhor_nome, (melhor_auc, melhor_pipeline) = max(avaliacoes.items(), key=lambda item: item[1][0])
    print(f"\n=== MELHOR MODELO: {melhor_nome} (AUC {melhor_auc:.3f}) ===")
    print(matriz_confusao_texto(y_te, melhor_pipeline.predict(X_te)))

    if "Random Forest" in melhor_nome:
        nomes_features = melhor_pipeline.named_steps["prep"].get_feature_names_out()
        importancias = pd.Series(melhor_pipeline.named_steps["modelo"].feature_importances_, index=nomes_features)
        print("\nFatores mais associados ao churn:")
        print(importancias.nlargest(5).to_string(float_format=lambda x: f"{x:.3f}"))

    joblib.dump(melhor_pipeline, "outputs/modelo_churn.joblib")
    print("\nModelo salvo em outputs/modelo_churn.joblib")

    cliente_novo = pd.DataFrame(
        [
            {
                "plano": "Basico",
                "tipo_pagamento": "boleto",
                "meses_contrato": 3,
                "fatura_mensal": 95.0,
                "chamados_suporte": 4,
                "uso_gb_mes": 12.5,
            }
        ]
    )
    risco = melhor_pipeline.predict_proba(cliente_novo)[0, 1]
    print(f"Exemplo de scoring: novo cliente tem {risco:.1%} de risco estimado de churn")

    # curva ROC para o relatorio final

    fig, ax = plt.subplots(figsize=(6, 5))
    for nome, (_, pipe) in avaliacoes.items():
        RocCurveDisplay.from_estimator(pipe, X_te, y_te, name=nome, ax=ax)
    ax.set_title("Curva ROC — modelos de churn")
    plt.tight_layout()
    plt.savefig("outputs/roc_churn.png", dpi=120)
    print("Grafico ROC salvo em outputs/roc_churn.png")
