"""Painel do SAC: SLA de resposta, resolucao no primeiro contato e CSAT."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CANAIS = {
    # canal: (peso volume, sla primeira resposta em min, media de satisfacao)
    "telefone": {"peso": 0.35, "sla_min": 15, "csat_base": 4.3},
    "chat": {"peso": 0.40, "sla_min": 5, "csat_base": 4.1},
    "email": {"peso": 0.25, "sla_min": 240, "csat_base": 3.6},
}

DIAS = 60
SEED = 130


def gerar_atendimentos(n: int = 4_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    canal = rng.choice(list(CANAIS), n, p=[c["peso"] for c in CANAIS.values()])
    dia = rng.integers(0, DIAS, n)

    sla_alvo = pd.Series(canal).map({c: v["sla_min"] for c, v in CANAIS.items()}).to_numpy()
    # resposta real: lognormal centrada perto do SLA, com violacoes frequentes no email
    fator = pd.Series(canal).map({"telefone": 0.9, "chat": 1.2, "email": 1.6}).to_numpy()
    tempo_resposta = np.clip(rng.lognormal(np.log(0.8 * sla_alvo * fator), 0.7), 0.5, None).round(1)
    dentro_sla = tempo_resposta <= sla_alvo

    csat_base = pd.Series(canal).map({c: v["csat_base"] for c, v in CANAIS.items()}).to_numpy()
    bonus_rapido = np.where(dentro_sla, 0.25, -0.45)
    csat = np.clip(rng.normal(csat_base + bonus_rapido, 0.55), 1, 5).round(1)

    return pd.DataFrame(
        {
            "dia": dia,
            "canal": canal,
            "tempo_resposta_min": tempo_resposta,
            "dentro_sla": dentro_sla,
            "resolvido_1o_contato": rng.random(n) < (0.72 + 0.08 * dentro_sla),
            "csat": csat,
        }
    )


if __name__ == "__main__":
    import pathlib

    pathlib.Path("outputs").mkdir(exist_ok=True)

    base = gerar_atendimentos()

    print("=== DESEMPENHO POR CANAL ===")
    por_canal = (
        base.groupby("canal")
        .agg(
            atendimentos=("canal", "count"),
            sla_pct=("dentro_sla", lambda s: s.mean() * 100),
            fcr_pct=("resolvido_1o_contato", lambda s: s.mean() * 100),
            csat_medio=("csat", "mean"),
        )
        .round(1)
    )
    for nome, cfg in CANAIS.items():
        por_canal.loc[nome, "sla_meta_min"] = cfg["sla_min"]
    print(por_canal.sort_values("atendimentos", ascending=False).to_string())

    semanal = base.assign(semana=base["dia"] // 7).groupby(["semana", "canal"]).size().unstack()
    # backlog: chega X por semana e a equipe tem capacidade fixa de resolucao
    CAPACIDADE_SEMANAL = 950
    volume_semanal = semanal.sum(axis=1)
    acumulado = 0
    backlog_vals = []
    for volume in volume_semanal:
        acumulado = max(0.0, acumulado + volume - CAPACIDADE_SEMANAL)
        backlog_vals.append(int(acumulado))
    backlog = pd.Series(backlog_vals, index=volume_semanal.index)

    print("\n=== BACKLOG ESTIMADO POR SEMANA ===")
    print(backlog.round(0).astype(int).to_string())

    pior_csat = por_canal["csat_medio"].idxmin()
    pior_sla = por_canal["sla_pct"].idxmin()
    print(
        f"\nPontos de atencao: CSAT mais baixo em '{pior_csat}' | "
        f"SLA mais violado em '{pior_sla}' ({por_canal.loc[pior_sla, 'sla_pct']}%)"
    )

    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.3))
    semanal.plot(ax=eixos[0], marker="o")
    eixos[0].set_title("Volume semanal por canal")
    eixos[1].scatter(
        por_canal["sla_pct"], por_canal["csat_medio"], s=por_canal["atendimentos"], alpha=0.7, color="#2563eb"
    )
    for canal_nome, linha in por_canal.iterrows():
        eixos[1].annotate(canal_nome, (linha["sla_pct"], linha["csat_medio"]), fontsize=9)
    eixos[1].set_title("SLA x CSAT (bolha = volume)")
    backlog.plot.bar(ax=eixos[2], color="#dc2626", alpha=0.85)
    eixos[2].set_title("Backlog estimado por semana")
    plt.tight_layout()
    plt.savefig("outputs/painel_sac.png", dpi=120)

    por_canal.reset_index().to_csv("outputs/sac_consolidado.csv", index=False)
    print("\nCSV e painel salvos em outputs/")
