"""FinOps de inferencia: custo por predicao, projecao do mes e alertas de orcamento."""

import pathlib

import pandas as pd

DIA_DO_MES = 20
DIAS_NO_MES = 30
ORCAMENTO_MENSAL_USD = 2_000.0
ALERTA_PARTICIPACAO = 0.25

# endpoint: (chamadas/dia, custo por 1.000 predicoes em USD)
ENDPOINTS = {
    "predizer_credito": {"volume_diario": 42_000, "custo_por_mil": 0.55},
    "score_fraude_cartao": {"volume_diario": 130_000, "custo_por_mil": 0.18},
    "recomendacao_home": {"volume_diario": 310_000, "custo_por_mil": 0.06},
    "ocr_documentos": {"volume_diario": 2_400, "custo_por_mil": 6.40},
}


def contabilizar() -> pd.DataFrame:
    linhas = []
    for nome, cfg in ENDPOINTS.items():
        custo_dia = cfg["volume_diario"] / 1000 * cfg["custo_por_mil"]
        custo_mes_atual = custo_dia * DIA_DO_MES
        projecao_mes = custo_dia * DIAS_NO_MES

        linhas.append(
            {
                "endpoint": nome,
                "volume_diario": cfg["volume_diario"],
                "custo_por_mil_usd": cfg["custo_por_mil"],
                "custo_dia_usd": round(custo_dia, 2),
                "mes_atual_usd": round(custo_mes_atual, 2),
                "projecao_mes_usd": round(projecao_mes, 2),
            }
        )
    return pd.DataFrame(linhas)


OTIMIZACOES = {
    "recomendacao_home": "ativar cache de respostas (top-N estavel) e batch de 32",
    "score_fraude_cartao": "mover para modelo destilado; manter pesado so p/ casos duvidosos",
    "predizer_credito": "batching na janela noturna, onde a latencia nao e critica",
    "ocr_documentos": "paginar: OCR so da pagina com campos obrigatorios",
}


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    painel = contabilizar()
    projecao_total = painel["projecao_mes_usd"].sum()
    painel["participacao_projecao"] = (painel["projecao_mes_usd"] / projecao_total * 100).round(1)

    print(f"=== FINOPS DE INFERENCIA — dia {DIA_DO_MES}/{DIAS_NO_MES} ===")
    print(painel.to_string(index=False))

    print(f"\nProjecao total do mes : USD {projecao_total:,.2f}")
    print(f"Orcamento aprovado    : USD {ORCAMENTO_MENSAL_USD:,.2f}")

    if projecao_total > ORCAMENTO_MENSAL_USD:
        estouro = projecao_total - ORCAMENTO_MENSAL_USD
        print(f"SITUACAO: ESTOURO projetado de USD {estouro:,.2f}")
    else:
        folga = ORCAMENTO_MENSAL_USD - projecao_total
        print(f"SITUACAO: dentro do orcamento (folga de USD {folga:,.2f})")

    suspeitos = painel[painel["participacao_projecao"] > ALERTA_PARTICIPACAO * 100]
    if not suspeitos.empty:
        for _, linha in suspeitos.iterrows():
            print(f"\n[REVISAO] {linha['endpoint']} concentra {linha['participacao_projecao']}% da conta.")
            print(f"  Otimizacao sugerida: {OTIMIZACOES[linha['endpoint']]}")

    caminho = "outputs/finops_inferencia.csv"
    painel.to_csv(caminho, index=False)
    print(f"\nPainel salvo em {caminho}")
