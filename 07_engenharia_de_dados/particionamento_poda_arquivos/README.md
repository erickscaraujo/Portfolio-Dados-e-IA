# Particionamento e Poda de Arquivos

O conceito de partition pruning do Spark, demonstrado em CSVs.

## Destaques
- Lake particionado por `data=YYYY-MM-DD/` (90 dias gerados)
- Consulta de um mês: leitura ingênua (90 arquivos) vs poda (30 arquivos)
- Tempo e nº de arquivos lidos comparados
- Mesma agregação, custo 3× menor só por respeitar a partição

## Stack
pandas, pathlib

## Como rodar
```bash
python main.py   # cria outputs/lake_particionado/ e mede a poda
```
