# Busca A* — Caminho em Grade com Obstáculos

A* clássico: heurística de Manhattan, vizinhança 4-direções, caminho ótimo.

## Destaques
- Grade 20×20 com obstáculos fixos + parede no meio (força desvio)
- Open set com prioridade f = g + h; reconstrução do caminho pelos pais
- Comparação do custo encontrado contra o custo teórico sem obstáculos
- Mapa ASCII mostrando início, alvo, muros e o traçado

## Stack
R base (sem pacotes externos)

## Como rodar
```r
Rscript main.R
```
