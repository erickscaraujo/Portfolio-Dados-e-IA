# Versionamento de Dataset — Snapshot com Diff

Snapshots de uma base com hash de conteúdo e diff linha a linha entre versões.

## Destaques
- Hash SHA-1 por registro (chave + campos) para detectar mudança silenciosa
- Diff v1 → v2: adicionados, removidos e ALTERADOS (com campo que mudou)
- Manifest JSON por snapshot (hash do arquivo inteiro + contagens)
- Reprodutibilidade: mesma base gera o mesmo hash sempre

## Stack
R base

## Como rodar
```r
Rscript main.R   # cria outputs/snapshots/ e outputs/diff_v1_v2.csv
```
