# Gateway de Inferência — Batching e Rate Limit

Infra de serving simulada: proteção contra picos e eficiência de GPU.

## Destaques
- Token bucket limitando a 500 rps; excesso vira HTTP 429 contabilizado
- Micro-batching: janela de 8ms / lote máx 32 → menos chamadas ao modelo
- Latências p50/p95/p99 comparadas com e sem batching
- Trade-off visível: batching economiza compute ao custo de pequena espera

## Stack
numpy, stdlib

## Como rodar
```bash
python main.py
```
