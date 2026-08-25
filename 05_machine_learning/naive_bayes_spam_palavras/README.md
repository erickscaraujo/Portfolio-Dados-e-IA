# Naive Bayes de Spam — Implementado do Zero

Multinomial Naive Bayes com suavização de Laplace, palavra a palavra.

## Destaques
- Frequências por classe + prior P(spam) aprendidos do corpus
- Laplace smoothing evita probabilidade zero em palavra nova
- Log-probabilidades para não underflow
- Precisão/recall/F1 e as palavras mais "spammy" do vocabulário

## Stack
R base (sem pacotes externos)

## Como rodar
```r
Rscript main.R
```
