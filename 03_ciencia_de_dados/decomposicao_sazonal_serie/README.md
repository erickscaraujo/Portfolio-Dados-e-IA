# Decomposição Sazonal de Série

Tendência, índice sazonal e resíduo — sem statsmodels, na mão com pandas.

## Destaques
- Tendência via média móvel centralizada de 12 meses
- Índice sazonal por mês = média do detrended (série aditiva)
- Série ajustada sazonalmente + diagnóstico do mês mais forte
- Painel clássico 4 linhas: série, tendência, sazonal, resíduo

## Stack
pandas, numpy, matplotlib

## Como rodar
```bash
python main.py   # gera outputs/decomposicao_sazonal.png
```
