# Otimização de Índices em SQLite

Antes/depois com EXPLAIN QUERY PLAN: full scan vs índice, com números reais.

## Destaques
- Tabela com 500 mil pedidos carregada via executemany streaming
- 3 consultas típicas medidas antes e depois de criar índices
- `EXPLAIN QUERY PLAN` mostrando SCAN → SEARCH USING INDEX
- Speedup por consulta + custo de escrita dos índices medido

## Stack
sqlite3, stdlib

## Como rodar
```bash
python main.py   # cria outputs/benchmark_indices.sqlite
```
