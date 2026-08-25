# Clusterização de Séries Temporais

Agrupa produtos pelo padrão de venda (tendência × sazonalidade × estabilidade), não pelo volume.

## Destaques
- Extração de features por série: slope de tendência, força sazonal semanal, CV
- K-Means com k via silhueta; clusters nomeados como padrões de negócio
- Grade visual com séries reais de cada padrão (`outputs/padroes_series.png`)
- Recomendação operacional por padrão

## Stack
pandas, numpy, scikit-learn, matplotlib

## Como rodar
```bash
python main.py
```
