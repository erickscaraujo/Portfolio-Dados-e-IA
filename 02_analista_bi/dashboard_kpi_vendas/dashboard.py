"""Construcao do dashboard HTML puro (cards KPI, tabela mensal e barras SVG inline)."""

from html import escape


def _card(titulo: str, valor: str, detalhe: str, positivo: bool) -> str:
    cor = "#16a34a" if positivo else "#dc2626"
    return f"""
    <div class="card">
      <h3>{escape(titulo)}</h3>
      <p class="valor">{valor}</p>
      <p class="delta" style="color:{cor}">{detalhe}</p>
    </div>"""


def _barra_svg(pct: float, largura_max: int = 220) -> str:
    w = max(2, int(largura_max * min(pct / 100, 1.15)))
    cor = "#16a34a" if pct >= 100 else ("#f59e0b" if pct >= 85 else "#dc2626")
    return f'<svg width="{largura_max}" height="14"><rect width="{w}" height="14" rx="3" fill="{cor}"/></svg>'


def montar_html(kpis: dict, mensal: list[dict]) -> str:
    cards = "".join(
        [
            _card(
                "Faturamento acumulado",
                kpis["faturamento"],
                f"{kpis['vs_meta']} da meta",
                kpis["meta_atingida"],
            ),
            _card(
                "Ticket médio",
                kpis["ticket_medio"],
                f"{kpis['ticket_delta']} vs ano anterior",
                kpis["ticket_ok"],
            ),
            _card(
                "Pedidos",
                kpis["pedidos"],
                f"{kpis['pedidos_delta']} vs ano anterior",
                kpis["pedidos_ok"],
            ),
            _card("Margem bruta", kpis["margem"], "meta interna: 38%", kpis["margem_ok"]),
        ]
    )

    linhas = []
    for m in mensal:
        linhas.append(f"""
      <tr>
        <td>{escape(m["mes"])}</td><td>{m["receita"]}</td><td>{m["meta"]}</td>
        <td>{m["atingido"]}</td><td>{_barra_svg(m["pct"])}</td><td>{m["crescimento"]}</td>
      </tr>""")

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Dashboard Comercial — KPIs</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background:#f1f5f9; margin:24px; color:#0f172a }}
  h1 {{ font-weight:600 }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px }}
  .card {{ background:white; border-radius:12px; padding:18px; box-shadow:0 1px 4px rgba(0,0,0,.08) }}
  .card h3 {{ margin:0; font-size:.85rem; color:#64748b; font-weight:500 }}
  .valor {{ font-size:1.7rem; font-weight:700; margin:6px 0 2px }}
  .delta {{ margin:0; font-size:.85rem; font-weight:600 }}
  table {{ border-collapse:collapse; width:100%; background:white; border-radius:12px;
          overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08); margin-top:28px }}
  th {{ background:#0f172a; color:white; text-align:left; padding:10px 14px; font-size:.8rem }}
  td {{ padding:9px 14px; border-top:1px solid #e2e8f0; font-size:.88rem }}
</style>
</head>
<body>
<h1>Dashboard Comercial — Visão Anual</h1>
<div class="grid">{cards}</div>
<table>
  <tr><th>Mês</th><th>Receita</th><th>Meta</th><th>Atingido</th><th>Progresso</th><th>Cresc. MoM</th></tr>
  {"".join(linhas)}
</table>
</body>
</html>"""


def salvar_dashboard(html: str, caminho: str = "outputs/dashboard.html") -> str:
    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write(html)
    return caminho
