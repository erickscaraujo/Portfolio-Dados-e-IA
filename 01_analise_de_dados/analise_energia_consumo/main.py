"""Consumo de energia por setor, curva de carga horaria e comparacao tarifaria."""

import matplotlib

matplotlib.use("Agg")

# tarifa branca (R$/kWh) e o convencional unico para referencia
import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TARIFA_PONTA = 1.18
TARIFA_FORA_PONTA = 0.62
TARIFA_CONVENCIONAL = 0.78
HORAS_PONTA = range(18, 21)

SETORES = {
    "Residencial": {"base": 0.9, "pico_noite": 2.2},
    "Comercial": {"base": 1.6, "pico_noite": 0.5},  # pico no horario comercial
    "Industrial": {"base": 3.4, "pico_noite": 1.1},  # opera quase contínuo
}

SEED = 26


def gerar_consumo_horario(dias: int = 365) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    horas = pd.date_range("2024-01-01", periods=dias * 24, freq="h")

    registros = []
    for setor, cfg in SETORES.items():
        hora_dia = horas.hour.to_numpy()
        # perfil diário: base + elevação no fim da tarde/noite (residencial) ou dia útil (comercial)
        forma = np.where(
            (hora_dia >= 18) & (hora_dia <= 22),
            cfg["pico_noite"],
            np.where((hora_dia >= 8) & (hora_dia <= 17), (cfg["base"] + cfg["pico_noite"]) / 2, cfg["base"] * 0.7),
        )
        # verao: ar-condicionado empurra o consumo em dez-fev
        fator_estacao = 1 + 0.25 * np.isin(horas.month.to_numpy(), [12, 1, 2])
        consumo = forma * fator_estacao * rng.normal(1, 0.08, len(horas))

        registros.append(pd.DataFrame({"setor": setor, "data": horas, "kwh": np.clip(consumo, 0.05, None)}))

    return pd.concat(registros, ignore_index=True)


def custo_mensal(consumo_setor: pd.DataFrame, tarifa_branca: bool) -> pd.Series:
    df = consumo_setor.copy()
    if tarifa_branca:
        hora = df["data"].dt.hour
        df["tarifa"] = np.where(hora.isin(HORAS_PONTA), TARIFA_PONTA, TARIFA_FORA_PONTA)
    else:
        df["tarifa"] = TARIFA_CONVENCIONAL
    df["custo"] = df["kwh"] * df["tarifa"]
    return df.groupby(df["data"].dt.to_period("M").astype(str))["custo"].sum().round(2)


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    consumo = gerar_consumo_horario()

    print("=== PERFIL MEDIO POR HORA DO DIA (kWh) ===")
    perfil = consumo.groupby(["setor", consumo["data"].dt.hour])["kwh"].mean().unstack(0).round(2)
    print(perfil.iloc[::3].to_string())

    print("\n=== CONSUMO MENSAL POR SETOR (MWh) ===")
    mensal = (
        consumo.groupby([consumo["data"].dt.to_period("M").astype(str), "setor"])["kwh"]
        .sum()
        .unstack()
        .div(1000)
        .round(1)
    )
    print(mensal.to_string())

    residencial = consumo[consumo["setor"] == "Residencial"]
    custo_convencional = custo_mensal(residencial, tarifa_branca=False)
    custo_branca = custo_mensal(residencial, tarifa_branca=True)
    economia = (custo_convencional - custo_branca).mean()
    economia_pct = economia / custo_convencional.mean()
    print(
        f"\nTarifa branca x convencional (Residencial): economia media de R$ {economia:,.2f}/mes ({economia_pct:.1%})"
    )

    fig, eixos = plt.subplots(1, 2, figsize=(14, 4.4))
    perfil.plot(ax=eixos[0])
    eixos[0].set_title("Curva de carga media por hora")
    eixos[0].set_xlabel("Hora do dia")
    eixos[0].axvspan(18, 20, color="#fbbf24", alpha=0.25)
    mensal.plot.area(ax=eixos[1], stacked=True, alpha=0.85)
    eixos[1].set_title("Consumo mensal (MWh)")
    plt.tight_layout()
    plt.savefig("outputs/energia_consumo.png", dpi=120)

    print("Painel salvo em outputs/energia_consumo.png")
