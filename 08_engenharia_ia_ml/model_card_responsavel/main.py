"""Gera o model card do modelo de credito junto com o treino."""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

SEED = 260
VERSAO = "1.2.0"
TETO_AMPLITUDE_APROVACAO_PP = 8.0


def gerar_base(n: int = 12_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    regiao = rng.choice(["norte", "sul", "centro"], n, p=[0.35, 0.4, 0.25])
    renda = rng.lognormal(8.3, 0.5, n)
    divida_renda = rng.beta(2, 6, n)
    score_interno = rng.integers(300, 900, n)

    logit = (
        -1.9
        + 5.6 * divida_renda
        - 0.00033 * renda
        - 0.005 * (score_interno - 500)
        # representatividade desigual: norte tem menos historico e sinal mais ruidoso
        + np.where(regiao == "norte", rng.normal(-0.5, 1.0, n), rng.normal(0.1, 0.55, n))
    )
    return pd.DataFrame(
        {
            "regiao": regiao,
            "renda": renda.round(2),
            "divida_renda": divida_renda.round(3),
            "score_interno": score_interno,
            "inadimpliu": (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int),
        }
    )


def avaliar_por_grupo(teste: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for grupo, sub in teste.groupby("regiao"):
        auc = roc_auc_score(sub["inadimpliu"], sub["probabilidade"])
        taxa_aprovacao = (sub["probabilidade"] < 0.40).mean()
        linhas.append(
            {
                "grupo": grupo,
                "n": len(sub),
                "auc": round(float(auc), 3),
                "aprovacao_pct": round(taxa_aprovacao * 100, 1),
            }
        )
    return pd.DataFrame(linhas)


def montar_card(metricas_global: dict, por_grupo: pd.DataFrame) -> str:
    amplitude = float(por_grupo["aprovacao_pct"].max() - por_grupo["aprovacao_pct"].min())
    aviso_grupos = (
        f"- **Atencao**: diferenca de aprovacao entre grupos de {amplitude:.1f}pp "
        f"(teto interno {TETO_AMPLITUDE_APROVACAO_PP:.0f}pp). Monitorar fairness em producao."
        if amplitude > TETO_AMPLITUDE_APROVACAO_PP
        else f"- Diferenca de aprovacao entre grupos dentro do teto ({amplitude:.1f}pp)."
    )

    tabela_grupos = por_grupo.to_markdown(index=False)

    return f"""# Model Card — Risco de Crédito v{VERSAO}

**Treinado em:** {datetime.now().isoformat(timespec="seconds")} | **Seed:** {SEED}

## Uso pretendido
- Pré-análise de concessão; saída é probabilidade de inadimplência em 12 meses.
- **Não usar** para decisão final automática sem política humana definida.

## Dados de treino
- Base sintética com {metricas_global["n_treino"]:,} registros; features: renda, dívida/renda, score interno.
- Representatividade desigual por região (menos histórico no norte).

## Métricas globais (holdout)
- AUC: **{metricas_global["auc"]:.3f}**

## Avaliação por grupo
{tabela_grupos}

## Limitações e riscos
{aviso_grupos}
- Dados sintéticos: substituir por base real antes de qualquer uso real.
- Calibração não verificada nesta versão — ver projeto `calibracao_probabilidades`.

## Pipeline de retreino
Rodar `python main.py`; artefato e card são regerados juntos.
"""


def main() -> None:
    pathlib = Path("outputs")
    pathlib.mkdir(exist_ok=True)

    base = gerar_base()
    features = ["renda", "divida_renda", "score_interno"]
    treino, teste = train_test_split(base, test_size=0.3, random_state=SEED, stratify=base["regiao"])

    modelo = GradientBoostingClassifier(random_state=SEED)
    modelo.fit(treino[features], treino["inadimpliu"])
    teste = teste.assign(probabilidade=modelo.predict_proba(teste[features])[:, 1])

    metricas_global = {
        "auc": float(roc_auc_score(teste["inadimpliu"], teste["probabilidade"])),
        "n_treino": len(treino),
    }
    por_grupo = avaliar_por_grupo(teste)

    print("=== MÉTRICAS ===")
    print(f"AUC global : {metricas_global['auc']:.3f}")
    print(por_grupo.to_string(index=False))

    card = montar_card(metricas_global, por_grupo)
    caminho = Path("outputs/model_card.md")
    caminho.write_text(card, encoding="utf-8")

    print(f"\nModel card salvo em {caminho}")
    print("\n--- preview ---")
    print("\n".join(card.splitlines()[:12]))


if __name__ == "__main__":
    main()
