# ANOVA de Dois Fatores com Interação

Fertilizante × irrigação: o efeito de um depende do nível do outro?

## Destaques
- `aov(produtividade ~ fertilizante * irrigacao)` com tabela F completa
- Interação plantada: fertilizante só funciona COM irrigação
- `interaction.plot()` evidenciando linhas não paralelas
- Tukey HSD pós-hoc sobre o fator significativo

## Stack
R base

## Como rodar
```r
Rscript main.R
```
