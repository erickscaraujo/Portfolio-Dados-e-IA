# Relatório de Frotas — Veículos

Custo por km, consumo e utilização da frota com alertas operacionais.

## Destaques
- 30 veículos: km rodado, litros, manutenção e dias parados
- Consumo (km/l) e custo/km por veículo contra metas
- Alerta: custo/km acima de R$ 1,20 ou consumo abaixo de 8 km/l
- Ranking dos piores custos + painel

## Stack
R base (sem pacotes externos)

## Como rodar
```r
Rscript main.R   # gera outputs/frota_veiculos.png + frota_alertas.csv
```
