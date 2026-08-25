"""Visualizacao do funil em HTML puro: barras centralizadas com taxas entre etapas."""

from html import escape

CORES_ETAPAS = ["#1d4ed8", "#2563eb", "#3b82f6", "#60a5fa"]


def montar_html(etapas: list[dict], por_dispositivo: dict[str, list[dict]]) -> str:
    linhas_funil = []
    maior_valor = etapas[0]["usuarios"]
    for i, etapa in enumerate(etapas):
        largura = max(12, int(etapa["usuarios"] / maior_valor * 640))
        taxa = "" if i == 0 else f"{etapa['usuarios'] / etapas[i - 1]['usuarios']:.0%} da etapa anterior"
        linhas_funil.append(f"""
    <div class="linha-funil">
      <span class="rotulo">{escape(etapa["etapa"])}</span>
      <div class="barra" style="width:{largura}px;background:{CORES_ETAPAS[i % len(CORES_ETAPAS)]}">
        {etapa["usuarios"]:,}
      </div>
      <span class="taxa">{taxa}</span>
    </div>""")

    blocos_dispositivo = []
    for dispositivo, passos in por_dispositivo.items():
        celulas = "".join(f"<td>{passo['taxa']:.0%}</td>" for passo in passos)
        blocos_dispositivo.append(f"<tr><th>{escape(dispositivo)}</th>{celulas}</tr>")

    cabecalho = "".join(
        f"<th>{escape(p['de'])} &rarr; {escape(p['para'])}</th>" for p in next(iter(por_dispositivo.values()))
    )

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head><meta charset="utf-8"><title>Funil de Conversao</title>
<style>
 body {{ font-family:'Segoe UI',sans-serif; margin:26px; color:#0f172a }}
 .linha-funil {{ display:flex; align-items:center; gap:14px; margin:8px 0 }}
 .rotulo {{ width:150px; font-size:.9rem; font-weight:600 }}
 .barra {{ color:white; padding:8px 12px; border-radius:8px;
          display:flex; justify-content:center; font-weight:600; min-width:90px }}
 .taxa {{ color:#64748b; font-size:.85rem }}
 table {{ border-collapse:collapse; margin-top:30px }}
 th, td {{ border:1px solid #e2e8f0; padding:7px 14px; font-size:.85rem }}
 th {{ background:#f8fafc }}
</style></head>
<body>
<h1>Funil de Conversao — E-commerce</h1>
{"".join(linhas_funil)}
<h2>Taxas entre etapas por dispositivo</h2>
<table><tr><th>Dispositivo</th>{cabecalho}</tr>{"".join(blocos_dispositivo)}</table>
</body></html>"""


def salvar(html: str, caminho: str = "outputs/funil_conversao.html") -> str:
    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write(html)
    return caminho
