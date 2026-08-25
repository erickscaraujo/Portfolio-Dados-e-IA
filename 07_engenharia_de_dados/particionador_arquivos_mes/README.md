# Particionador de Arquivos por Mês

Write-side do particionamento: um CSV grande vira 12 arquivos + manifest.

## Destaques
- Leitura única de `vendas_ano.csv` (~6 mil linhas)
- Split por mês em `particionado/mes=YYYY-MM/vendas.csv`
- Manifest com linhas por partição (índice de consulta)
- Verificação: soma das partições = total da fonte

## Stack
R base

## Como rodar
```r
Rscript gerar_fonte.R && Rscript main.R
```
