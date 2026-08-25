# Algoritmo Genético — Alocação de Turnos

Evolução de escalas de trabalho: seleção, crossover e mutação até minimizar conflitos.

## Destaques
- População de 60 cronogramas, 40 funcionários × 14 dias
- Fitness: penaliza conflito de folgas, sobrecarga semanal e cobertura mínima quebrada
- Elitismo (top 5), torneio para seleção, mutação de troca
- Curva de evolução do melhor fitness por geração

## Stack
R base (sem pacotes externos)

## Como rodar
```r
Rscript main.R   # gera outputs/genetico_turnos.png
```
