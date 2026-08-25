# Threshold Ótimo por Custo de Negócio

0.5 não é regra: quando perder um fraud custa 10× um falso alerta.

## Destaques
- `glm(binomial)` + varredura de threshold 0.05–0.95
- Matriz de custo explícita: FN = R$ 500, FP = R$ 50
- Curva de custo total × threshold com mínimo marcado
- Comparação do custo no default vs no ótimo

## Stack
R base

## Como rodar
```r
Rscript main.R   # gera outputs/threshold_custo.png
```
