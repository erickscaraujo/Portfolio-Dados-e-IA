# Conversão Segura de Tipos

CSV sujo: números com vírgula, datas em dois formatos, códigos com zero à esquerda.

## Destaques
- Conversores defensivos que devolvem NA + motivo quando falham
- Relatório por coluna: taxa de sucesso, exemplos de falha
- Formato brasileiro "1.234,56" tratado corretamente
- Base convertida salva só com as colunas que passaram no mínimo aceitável

## Stack
R base

## Como rodar
```r
Rscript main.R   # gera outputs/relatorio_conversoes.csv
```
