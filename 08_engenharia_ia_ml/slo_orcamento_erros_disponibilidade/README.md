# SLO e Error Budget — Disponibilidade Semanal

99,9% de disponibilidade: quanto do orçamento de erro cada semana queimou.

## Destaques
- 16 semanas com incidentes de duração variável
- Error budget semanal = minutos permitidos pelo SLO
- Burn rate acumulado: alerta quando o orçamento some antes do trimestre
- Painel disponibilidade + burn acumulado com linha de 100%

## Stack
R base

## Como rodar
```r
Rscript main.R   # gera outputs/slo_error_budget.png
```
