# FinOps de Inferência — Custo por Predição

Quanto cada endpoint custa e quando o orçamento estoura.

## Destaques
- Contabilidade por endpoint: chamadas × custo unitário (GPU-s)
- Projeção de fechamento do mês pelo ritmo atual (run-rate)
- Alerta de orçamento por endpoint (>40% do total dispara revisão)
- Recomendações de otimização: batching, cache, modelo destilado

## Stack
pandas

## Como rodar
```bash
python main.py   # imprime o painel e salva outputs/finops_inferencia.csv
```
