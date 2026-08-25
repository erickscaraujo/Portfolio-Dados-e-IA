# Cliente de API Respeitoso — Backoff e Retry-After

O lado cliente do rate limit: token bucket + backoff exponencial com jitter.

## Destaques
- API simulada que devolve 429 quando ultrapassada (com header Retry-After)
- Cliente ingênuo falha em massa; cliente educado usa bucket local + backoff + jitter
- Métricas: sucesso, falhas 429 e tempo total das duas estratégias
- Padrão pronto para copiar em qualquer wrapper de HTTP

## Stack
stdlib apenas (random, time)

## Como rodar
```bash
python main.py
```
