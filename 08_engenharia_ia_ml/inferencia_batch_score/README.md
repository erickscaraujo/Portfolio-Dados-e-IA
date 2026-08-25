# Inferência em Batch com Guardrail de Drift

Scoring de grandes lotes em chunks + comparação do score contra o baseline de treino.

## Destaques
- Processamento chunked (memória previsível para lotes de qualquer tamanho)
- Saída CSV streaming (`probabilidade,faixa_risco`) + resumo JSON por lote
- PSI entre score de hoje e quantis do treino → status estável/alerta/crítico
- Dois cenários: carteira normal vs carteira em crise (drift proposital)

## Stack
scikit-learn, joblib, numpy, stdlib

## Como rodar
```bash
python main.py   # treina se necessário e pontua outputs/scored_*.csv
```
