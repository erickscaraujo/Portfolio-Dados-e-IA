"""Calibracao de probabilidades: predito x observado, Brier e diagrama de confiabilidade."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.model_selection import train_test_split

SEED = 88


def gerar_base(n: int = 12_000) -> tuple[np.ndarray, np.ndarray]:
    """Logit com escala exagerada: modelo vira 'excessivamente confiante' de proposito."""
    rng = np.random.default_rng(SEED)
    X = rng.normal(size=(n, 4))
    logit_verdadeiro = 0.9 * X[:, 0] - 0.7 * X[:, 1] + 0.5 * X[:, 2]
    y = (rng.random(n) < 1 / (1 + np.exp(-logit_verdadeiro))).astype(int)

    # o modelo enxerga um logit inflado 3x -> probabilidades esticadas para os extremos
    X_modelo = X * [3.0, 3.0, 3.0, 1.0]
    return X_modelo, y


def resumo_calibracao(nome: str, probas: np.ndarray, y_real: np.ndarray, n_bins: int = 10) -> dict:
    brier = brier_score_loss(y_real, probas)
    logloss = log_loss(y_real, probas)

    bins = np.linspace(0, 1, n_bins + 1)
    faixas = np.digitize(probas, bins) - 1
    linhas = []
    for faixa in range(n_bins):
        mascara = faixas == faixa
        if mascara.sum() < 30:
            continue
        linhas.append(
            {
                "faixa": f"{bins[faixa]:.1f}-{bins[faixa + 1]:.1f}",
                "previsto": round(float(probas[mascara].mean()), 3),
                "observado": round(float(y_real[mascara].mean()), 3),
            }
        )
        # desvio medio ponderado aproxima o erro de calibracao
    desvio = float(np.mean([abs(linha["previsto"] - linha["observado"]) for linha in linhas]))

    print(f"\n--- {nome} ---")
    print(f"Brier: {brier:.4f} | log loss: {logloss:.4f} | desvio medio por faixa: {desvio:.3f}")
    return {"nome": nome, "probas": probas, "brier": brier, "bins": linhas}


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    X, y = gerar_base()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=SEED)

    base = LogisticRegression(max_iter=800)
    base.fit(X_tr, y_tr)

    platt = CalibratedClassifierCV(LogisticRegression(max_iter=800), method="sigmoid", cv=5)
    isotonic = CalibratedClassifierCV(LogisticRegression(max_iter=800), method="isotonic", cv=5)
    platt.fit(X_tr, y_tr)
    isotonic.fit(X_tr, y_tr)

    candidatos = {
        "sem calibracao": base.predict_proba(X_te)[:, 1],
        "platt sigmoid": platt.predict_proba(X_te)[:, 1],
        "isotonico": isotonic.predict_proba(X_te)[:, 1],
    }
    resultados = [resumo_calibracao(nome, probas, y_te) for nome, probas in candidatos.items()]

    melhor = min(resultados, key=lambda r: r["brier"])
    print(f"\nMelhor calibracao pelo Brier: {melhor['nome']}")

    print("\nTabela do melhor modelo (predito vs observado por faixa):")
    for linha in melhor["bins"]:
        barra = "#" * int(linha["observado"] * 20)
        print(f"- {linha['faixa']} | previsto {linha['previsto']:.2f} | observado {linha['observado']:.2f} {barra}")

    fig, eixo = plt.subplots(figsize=(6.2, 6))
    cores = ["#dc2626", "#2563eb", "#059669"]
    for (nome, dados), cor in zip([(r["nome"], r["probas"]) for r in resultados], cores, strict=True):
        fracao_positiva, media_prevista = calibration_curve(y_te, dados, n_bins=10, strategy="quantile")
        eixo.plot(media_prevista, fracao_positiva, marker="o", ms=4, lw=1.6, label=nome, color=cor)
    eixo.plot([0, 1], [0, 1], ls="--", color="gray", label="calibracao perfeita")
    eixo.set_xlabel("Probabilidade prevista")
    eixo.set_ylabel("Frequencia observada")
    eixo.set_title("Diagrama de confiabilidade")
    eixo.legend()
    plt.tight_layout()
    plt.savefig("outputs/calibracao_reliability.png", dpi=120)

    print("\nDiagrama salvo em outputs/calibracao_reliability.png")
