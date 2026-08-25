"""Matriz de cohort de retencao com heatmap HTML puro."""

from html import escape


def _cor_celula(pct: float) -> str:
    # escala verde: 0% claro -> 100% saturado
    intensidade = max(0.0, min(pct, 100.0)) / 100
    return f"hsl(150, {30 + intensidade * 40:.0f}%, {92 - intensidade * 45:.0f}%)"


def montar_html(coortes: dict[str, list[float | None]], meses: list[str]) -> str:
    cabecalho = "".join(f"<th>{escape(m)}</th>" for m in meses)
    linhas = []
    for cohort, valores in coortes.items():
        celulas = []
        for valor in valores:
            if valor is None:
                celulas.append("<td class='vazio'></td>")
            else:
                celulas.append(f'<td style="background:{_cor_celula(valor)}">{valor:.0f}%</td>')
        linhas.append(f"<tr><th>{escape(cohort)}</th>{''.join(celulas)}</tr>")

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head><meta charset="utf-8"><title>Cohort de Retencao</title>
<style>
 body {{ font-family:'Segoe UI',sans-serif; margin:24px; color:#0f172a }}
 table {{ border-collapse:collapse }}
 th {{ padding:6px 10px; font-size:.78rem; color:#475569 }}
 td {{ width:64px; height:34px; text-align:center; font-size:.8rem;
      border:2px solid white; font-weight:600 }}
 td.vazio {{ background:#f1f5f9 }}
</style></head>
<body>
<h1>Retencao por cohort de aquisicao</h1>
<p>Percentual de clientes do cohort que voltaram a comprar no mes de offset.</p>
<table><tr><th>Cohort</th>{cabecalho}</tr>{"".join(linhas)}</table>
</body></html>"""


def salvar(html: str, caminho: str = "outputs/cohort_retencao.html") -> str:
    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write(html)
    return caminho
