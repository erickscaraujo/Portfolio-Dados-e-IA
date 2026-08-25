# Capacidade de Inferência — Fila M/M/1

Teoria de filas aplicada a serving: simulação × fórmula de Erlang.

## Destaques
- Chegadas Poisson e serviço exponencial simulados por 20 mil requisições
- Comparação: espera simulada vs fórmula analítica W = 1/(μ−λ)
- Curva de utilização ρ: acima de 0.8 a espera explode (ponto de dimensionamento)
- Recomendação de réplicas para o SLO de p95

## Stack
R base

## Como rodar
```r
Rscript main.R   # gera outputs/fila_inferencia.png
```
