# Diff de Esquemas — Mudanças Entre Versões

O time de origem alterou a tabela: o que exatamente mudou entre v1 e v2?

## Destaques
- Comparação estrutural: colunas novas, removidas, renomeadas (por heurística) e trocas de tipo
- Classificação quebra × seguro com justificativa
- Changelog em Markdown pronto para o PR do time origem
- Função `diff_schemas()` reutilizável

## Stack
R base

## Como rodar
```r
Rscript main.R   # gera outputs/changelog_schema.md
```
