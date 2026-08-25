"""Checa frescura e saude de execucao das tabelas contra o SLA acordado."""

import json
import pathlib
from datetime import datetime, timedelta

import pandas as pd

# SLA por tabela: frequencia esperada de atualizacao em minutos
SLAS = {
    "ft_pedidos": {"frequencia_min": 60, "dono": "time vendas"},
    "dim_clientes": {"frequencia_min": 1440, "dono": "time cadastro"},
    "agg_dashboard_bi": {"frequencia_min": 1440, "dono": "time bi"},
    "eventos_app": {"frequencia_min": 30, "dono": "plataforma"},
}

FALHA_CRITICA_CONSECUTIVA = 2


def simular_execucoes(agora: datetime) -> dict[str, list[dict]]:
    """Ultimas 10 execucoes por tabela; algumas tabelas com problemas de proposito."""
    historico: dict[str, list[dict]] = {}
    cenarios = {
        "ft_pedidos": [0] * 8 + [-2, -3],  # saudavel
        "dim_clientes": [0, -1, -1, -1],  # atrasada mas sem falha
        "agg_dashboard_bi": [0, 0, 1, -1, 1, -1],  # falhas intermitentes
        "eventos_app": [4, -1, -1, -1, -1],  # parou de atualizar
    }
    for tabela, offsets in cenarios.items():
        execucoes = []
        for offset in offsets:
            if offset < 0:
                execucoes.append({"quando": agora + timedelta(hours=offset), "status": "falha"})
            else:
                execucoes.append(
                    {
                        "quando": agora - timedelta(minutes=int(SLAS[tabela]["frequencia_min"] * (0.5 + offset))),
                        "status": "sucesso",
                    }
                )
        historico[tabela] = execucoes
    return historico


def avaliar_tabela(tabela: str, execucoes: list[dict], agora: datetime) -> dict:
    sla_min = SLAS[tabela]["frequencia_min"]
    ultimos_sucessos = [e for e in execucoes if e["status"] == "sucesso"]

    idade_minutos = None
    status_frescura = "sem sucesso recente"
    if ultimos_sucessos:
        idade_minutos = (agora - max(e["quando"] for e in ultimos_sucessos)).total_seconds() / 60
        # tolerancia de 20% sobre o SLA antes de gritar
        status_frescura = (
            "ok" if idade_minutos <= sla_min * 1.2 else "atrasada" if idade_minutos <= sla_min * 3 else "critica"
        )

    janela_7d = [e for e in execucoes if e["quando"] >= agora - timedelta(days=7)]
    taxa_sucesso = sum(e["status"] == "sucesso" for e in janela_7d) / max(len(janela_7d), 1)

    falhas_consecutivas = 0
    for evento in sorted(execucoes, key=lambda x: x["quando"], reverse=True):
        if evento["status"] != "falha":
            break
        falhas_consecutivas += 1

    if falhas_consecutivas >= FALHA_CRITICA_CONSECUTIVA or status_frescura == "critica":
        severidade = "CRITICO"
    elif status_frescura == "atrasada" or taxa_sucesso < 0.7:
        severidade = "ALERTA"
    else:
        severidade = "OK"

    return {
        "tabela": tabela,
        "dono": SLAS[tabela]["dono"],
        "idade_min": round(idade_minutos) if idade_minutos is not None else None,
        "sla_min": sla_min,
        "frescura": status_frescura,
        "taxa_sucesso_7d": round(taxa_sucesso, 2),
        "falhas_consecutivas": falhas_consecutivas,
        "severidade": severidade,
    }


def main() -> int:
    pathlib.Path("outputs").mkdir(exist_ok=True)
    agora = datetime.now()

    avaliacoes = [avaliar_tabela(tabela, execucoes, agora) for tabela, execucoes in simular_execucoes(agora).items()]
    df = pd.DataFrame(avaliacoes).set_index("tabela")

    print("=== SAUDE DAS TABELAS ===")
    print(df.to_string())

    criticos = df[df["severidade"] == "CRITICO"]
    print("\n=== ESCALACAO ON-CALL ===")
    if criticos.empty:
        print("Nenhuma tabela em estado critico. Boa noite.")
    for tabela, linha in criticos.iterrows():
        motivo = f"frescura={linha['frescura']}, falhas seguidas={linha['falhas_consecutivas']}"
        print(f"- {tabela} (dono: {linha['dono']}): {motivo}")

    caminho = "outputs/alertas_sla.json"
    with open(caminho, "w", encoding="utf-8") as arq:
        json.dump(
            {"gerado_em": agora.isoformat(timespec="seconds"), "avaliacoes": avaliacoes},
            arq,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\nRelatorio salvo em {caminho}")
    return 1 if not criticos.empty else 0


if __name__ == "__main__":
    raise SystemExit(main())
