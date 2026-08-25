# Consolidação Multi-Filial

Três filiais, três CSVs, um padrão único — com validação e deduplicação.

## Destaques
- Leitura das 3 fontes regionais com nomes/UFs inconsistentes
- Padronização (UF maiúscula, datas ISO), dedup por chave composta
- `stopifnot()` como gate: pipeline falha cedo se a regra quebrar
- Agregação semanal + CSV consolidado

## Stack
R base

## Como rodar
```r
Rscript gerar_fontes.R && Rscript main.R
```
