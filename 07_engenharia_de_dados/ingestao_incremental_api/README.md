# Ingestão Incremental de API

Sincronização com watermark persistido — o padrão de toda pipeline incremental.

## Destaques
- API simulada com paginação por cursor (`id > último visto`)
- Watermark em `state.json`: cada execução puxa só o delta
- Proteção contra duplicidade dentro da mesma execução
- Escrita streaming em JSONL + log de chamadas à API
- Roda 2× no mesmo comando para demonstrar idempotência

## Stack
stdlib apenas

## Como rodar
```bash
python main.py   # gera outputs/eventos.jsonl e outputs/state.json
```
