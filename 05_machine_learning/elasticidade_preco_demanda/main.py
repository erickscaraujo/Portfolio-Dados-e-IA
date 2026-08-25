"""Elasticidade-preco da demanda via regressao log-log + preco otimo de receita."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

ELASTICIDADE_VERDADEIRA = -1.4
PRECO_ATUAL = 48.0
SEED = 70


def gerar_historico(n: int = 260) -> pd.DataFrame:
    """Semanas de preco praticado e quantidade vendida (com feriados e promocoes)."""
    rng = np.random.default_rng(SEED)
    preco = np.clip(rng.normal(PRECO_ATUAL, 6.5, n), 28, None).round(2)
    # curva de demanda real em log-log com elasticidade conhecida
    log_quantidade = (
        np.log(12_000)
        + ELASTICIDADE_VERDADEIRA * np.log(preco / PRECO_ATUAL)
        - 0.02 * np.arange(n)  # tendencia suave de queda
        + rng.normal(0, 0.06, n)
    )
    return pd.DataFrame(
        {
            "preco": preco,
            "quantidade": np.exp(log_quantidade).round(),
        }
    )


def estimar_elasticidade(df: pd.DataFrame) -> tuple[float, float]:
    modelo = LinearRegression()
    modelo.fit(np.log(df[["preco"]]), np.log(df["quantidade"]))
    return float(modelo.coef_[0]), float(modelo.intercept_)


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    historico = gerar_historico()
    elasticidade, intercepto = estimar_elasticidade(historico)

    print("=== ELASTICIDADE-PRECO ESTIMADA ===")
    print(f"coeficiente: {elasticidade:.3f} (verdadeiro: {ELASTICIDADE_VERDADEIRA})")
    if abs(elasticidade) > 1:
        leitura = "demanda ELASTICA: queda de preco aumenta a receita"
        direcao = "abaixo"
    else:
        leitura = "demanda INELASTICA: aumento de preco aumenta a receita"
        direcao = "acima"
    print(f"leitura: {leitura}")
    print(f"interpretacao: +1% no preco -> {elasticidade:+.2f}% na quantidade vendida")

    grade = np.linspace(28, 80, 200)
    quantidade_prevista = np.exp(intercepto) * (grade / PRECO_ATUAL) ** elasticidade
    receita_prevista = grade * quantidade_prevista

    preco_otimo = float(grade[np.argmax(receita_prevista)])
    receita_atual_estimada = PRECO_ATUAL * np.exp(intercepto) * (PRECO_ATUAL / PRECO_ATUAL) ** elasticidade
    ganho = receita_prevista.max() / receita_atual_estimada - 1

    print("\n=== OTIMIZACAO DE RECEITA ===")
    print(f"preco atual     : R$ {PRECO_ATUAL:.2f}")
    print(f"preco otimo     : R$ {preco_otimo:.2f} ({direcao} do atual)")
    print(f"ganho estimado  : {ganho:+.1%}")

    fig, eixos = plt.subplots(1, 2, figsize=(13.5, 4.5))
    eixos[0].scatter(historico["preco"], historico["quantidade"], s=10, alpha=0.4, color="#334155")
    eixos[0].plot(grade, quantidade_prevista, color="#dc2626", lw=2, label="modelo")
    eixos[0].set_title(f"Curva de demanda (elasticidade {elasticidade:.2f})")
    eixos[0].set_xlabel("Preco (R$)")
    eixos[0].set_ylabel("Quantidade/semana")
    eixos[0].legend()

    eixos[1].plot(grade, receita_prevista / 1e3, color="#2563eb", lw=2)
    eixos[1].axvline(preco_otimo, ls="--", color="gray", label=f"otimo R$ {preco_otimo:.0f}")
    eixos[1].axvline(PRECO_ATUAL, ls=":", color="black", label=f"atual R$ {PRECO_ATUAL:.0f}")
    eixos[1].set_title("Receita semanal por preco (R$ mil)")
    eixos[1].set_xlabel("Preco (R$)")
    eixos[1].legend()
    plt.tight_layout()
    plt.savefig("outputs/elasticidade_preco.png", dpi=120)

    print("\nGraficos salvos em outputs/elasticidade_preco.png")
