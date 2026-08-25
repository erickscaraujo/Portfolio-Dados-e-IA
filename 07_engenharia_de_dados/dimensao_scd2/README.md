# Dimensão SCD Tipo 2

Histórico versionado de clientes em SQLite — a técnica clássica de modelagem dimensional.

## Destaques
- `valido_de` / `valido_ate` + flag `is_current` por versão
- Versiona apenas quando atributos monitorados mudam (carga idempotente)
- Consultas point-in-time: "como o cliente estava naquele dia?"
- Checagem de integridade: exatamente 1 versão vigente por cliente
- 3 cargas mensais simulando o fluxo real do DW

## Stack
sqlite3, stdlib

## Como rodar
```bash
python main.py   # cria outputs/dw_dimensoes.sqlite
```
