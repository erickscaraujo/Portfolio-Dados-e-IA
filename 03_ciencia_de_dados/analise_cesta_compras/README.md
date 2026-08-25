# Análise de Cesta de Compras

Regras de associação estilo Apriori implementadas do zero.

## Destaques
- Suporte, confiança e lift calculados manualmente sobre cupons
- Filtros configuráveis (min_suporte, min_confianca, min_lift)
- Combos plantados no gerador servem de ground truth — o script reporta quantos foram redescobertos

## Stack
stdlib apenas (collections, itertools)

## Como rodar
```bash
python main.py
```
