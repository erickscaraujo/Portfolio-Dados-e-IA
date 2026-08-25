"""Fraude 3%: baseline, class_weight, oversampling manual e threshold tuning."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_recall_curve, recall_score
from sklearn.model_selection import train_test_split

TAXA_FRAUDE = 0.03
SEED = 200


def gerar_base(n: int = 20_000) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    X = rng.normal(size=(n, 6))
    logit = 2.6 * X[:, 0] - 0.9 * X[:, 1] + 1.4 * X[:, 3] + np.log(TAXA_FRAUDE / (1 - TAXA_FRAUDE)) - 2.4
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    return X, y


def oversampling_minoritario(X: np.ndarray, y: np.ndarray, seed: int = SEED):
    """Duplica amostras da classe rara ate equilibrar — SMOTE simplificado sem sintese."""
    rng = np.random.default_rng(seed)
    indices_raros = np.where(y == 1)[0]
    faltam = int((y == 0).sum() - len(indices_raros))
    duplicatas = rng.choice(indices_raros, size=faltam, replace=True)
    return (
        np.vstack([X, X[duplicatas]]),
        np.concatenate([y, np.ones(faltam)]),
    )


def melhor_threshold(probas: np.ndarray, y_real: np.ndarray) -> tuple[float, float]:
    thresholds = np.linspace(0.05, 0.95, 91)
    f1s = [f1_score(y_real, probas >= t) for t in thresholds]
    otimo = float(thresholds[int(np.argmax(f1s))])
    return otimo, max(f1s)


def avaliar(nome: str, probas: np.ndarray, y_real: np.ndarray, threshold: float = 0.5) -> dict:
    predito = probas >= threshold
    pr_auc = average_precision_score(y_real, probas)
    precisao_media = predito.mean()
    resultado = {
        "estrategia": nome,
        "pr_auc": round(pr_auc, 3),
        "recall": round(recall_score(y_real, predito, zero_division=0), 3),
        "f1": round(f1_score(y_real, predito, zero_division=0), 3),
        "taxa_alerta": round(float(np.mean(predito)), 3),
    }
    print(
        f"- {nome:<24} PR-AUC {resultado['pr_auc']:.3f} | "
        f"recall {resultado['recall']:.3f} | F1 {resultado['f1']:.3f} | "
        f"alertas {resultado['taxa_alerta']:.1%}"
    )
    return resultado, precisao_media


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    X, y = gerar_base()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, stratify=y, random_state=SEED)
    print(f"Fraude no holdout: {y_te.mean():.1%} das {len(y_te)} transacoes\n")

    resultados = []
    curvas = {}

    # 1. baseline ingenuo
    modelo_base = LogisticRegression(max_iter=800).fit(X_tr, y_tr)
    probas = modelo_base.predict_proba(X_te)[:, 1]
    res, _ = avaliar("baseline", probas, y_te)
    resultados.append(res)
    curvas["baseline"] = probas

    # 2. class weight balanceado
    modelo_peso = LogisticRegression(max_iter=800, class_weight="balanced").fit(X_tr, y_tr)
    probas_peso = modelo_peso.predict_proba(X_te)[:, 1]
    res, _ = avaliar("class_weight balanced", probas_peso, y_te)
    resultados.append(res)
    curvas["balanced"] = probas_peso

    # 3. oversampling manual do minority
    X_over, y_over = oversampling_minoritario(X_tr, y_tr)
    modelo_over = LogisticRegression(max_iter=800).fit(X_over, y_over)
    probas_over = modelo_over.predict_proba(X_te)[:, 1]
    res, _ = avaliar("oversampling manual", probas_over, y_te)
    resultados.append(res)
    curvas["oversampling"] = probas_over

    # 4. baseline com threshold otimizado por F1 (validado no proprio holdout p/ demo)
    threshold_otimo, f1_otimizado = melhor_threshold(probas, y_te)
    res, taxa_alerta = avaliar("threshold otimizado", probas, y_te, threshold=threshold_otimo)
    resultados.append(res)
    curvas["threshold"] = probas
    print(f"  (melhor threshold encontrado: {threshold_otimo:.2f}, F1 {f1_otimizado:.3f})")

    melhor = max(resultados, key=lambda r: r["f1"])
    print(f"\nMelhor F1: {melhor['estrategia']}")

    plt.figure(figsize=(7.8, 5))
    for (nome, probas_curva), cor in zip(curvas.items(), ["#94a3b8", "#2563eb", "#059669", "#dc2626"], strict=True):
        precisao, recall, _ = precision_recall_curve(y_te, probas_curva)
        plt.plot(recall, precisao, lw=1.8, color=cor, label=nome)
    plt.xlabel("Recall")
    plt.ylabel("Precisao")
    plt.title("Curva Precision-Recall por estrategia")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/pr_curves_desbalanceado.png", dpi=120)

    print("Curvas salvas em outputs/pr_curves_desbalanceado.png")
