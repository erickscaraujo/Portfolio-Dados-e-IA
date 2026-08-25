# Sumarização Extrativa (TextRank)

Resumo automático sem LLM: grafo de similaridade entre sentenças + PageRank.

## Destaques
- TF-IDF por sentença → matriz de cosseno → grafo
- PageRank implementado do zero com iteração de potência em numpy
- Top-k sentenças devolvidas na ordem original do texto
- Comparação contra baseline de posição (primeiras sentenças)

## Stack
scikit-learn, numpy

## Como rodar
```bash
python main.py
```
