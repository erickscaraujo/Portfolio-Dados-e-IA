# Detecção de Plágio — MinHash + Jaccard

Similaridade entre documentos em escala: shingles, MinHash e pares candidatos.

## Destaques
- k-shingles de 3 palavras por documento
- Jaccard exato para ground truth × MinHash com 64 permutações
- Erro médio da aproximação reportado; pares >0.3 marcados como suspeitos
- 100% stdlib (re, hashlib)

## Stack
stdlib apenas

## Como rodar
```bash
python main.py
```
