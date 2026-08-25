# Explicações de Predições — Contribuições por Feature

Cada score vem com o "porquê": top drivers por predição, auditáveis.

## Destaques
- Modelo de crédito `glm` + contribuição linear por feature (coef × desvio da média)
- Top 2 fatores que empurraram cada decisão para cima ou para baixo
- Log de auditoria com explicação anexada a cada linha pontuada
- Visão global: features mais citadas como driver no lote

## Stack
R base

## Como rodar
```r
Rscript main.R   # gera outputs/explicacoes_predicoes.csv
```
