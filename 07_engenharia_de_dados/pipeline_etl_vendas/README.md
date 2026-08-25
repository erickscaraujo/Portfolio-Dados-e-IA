# Pipeline ETL — Vendas

ETL batch de ponta a ponta: CSV + JSON → limpeza → data warehouse SQLite.

## Destaques
- Extração idempotente (gera fontes brutas com sujeira realista na 1ª execução)
- Transformação com validação de e-mail, padronização de UF, dedup e join por integridade
- Carga full-refresh em SQLite (`dim_cliente` + `fato_pedido` com FK)
- Logging estruturado com tempos por etapa e CLI via argparse

## Stack
pandas, sqlite3, argparse, logging

## Como rodar
```bash
python pipeline.py                 # usa outputs/dw_vendas.sqlite
python pipeline.py --dw outro.sqlite
```
