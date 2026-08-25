# Fila de Prioridade com Aging

Scheduler de jobs: prioridade importa, mas ninguém morre de fome na fila.

## Destaques
- `heapq` com prioridade dinâmica: aging +1 por segundo de espera
- Comparação FIFO × prioridade pura × prioridade com aging
- Métricas: espera p50/p95/max por classe de job (alta/média/baixa)
- Anti-starvation demonstrado: max wait limitado mesmo com fila cheia de urgentes

## Stack
heapq, stdlib

## Como rodar
```bash
python main.py
```
