# Reconciliação de Bases — Mesmo Cadastro, Sistemas Diferentes

CRM × ERP: quem diverge, em qual campo e por quanto.

## Destaques
- Join por chave comum entre dois sistemas
- Comparação campo a campo: saldo (tolerância 1%) e status categórico
- Classificação: idêntico, diferença aceitável, divergência crítica
- CSV das divergências críticas para correção manual

## Stack
R base

## Como rodar
```r
Rscript main.R   # gera outputs/divergencias_criticas.csv
```
