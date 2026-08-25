# Regressão Polinomial — O Ponto do Overfitting

Graus 1 a 11 no mesmo dataset: onde o modelo para de generalizar.

## Destaques
- Curva verdadeira senoidal + ruído; treino pequeno (30 pts) e teste limpo
- RMSE de treino cai sempre; RMSE de teste tem mínimo claro (~grau 3-4)
- Tabela completa por grau + escolha automática do melhor
- Sobreposição dos ajustes grau 1/3/9 sobre os dados

## Stack
R base

## Como rodar
```r
Rscript main.R   # gera outputs/polinomial_overfitting.png
```
