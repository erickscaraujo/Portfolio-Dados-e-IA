# Orquestrador de Batch

Mini-Airflow caseiro: DAG topológico com retries, isolamento de falhas e status por tarefa.

## Destaques
- Ordenação topológica (Kahn) com detecção de ciclos
- Retry configurável por tarefa com backoff crescente
- Dependentes são automaticamente ignorados quando um pai falha
- Tarefa `validar` falha 2× de propósito para demonstrar a recuperação
- Exit code do processo reflete o resultado do batch (útil para CI/cron)

## Stack
stdlib apenas

## Como rodar
```bash
python main.py   # gera outputs/carga_batch.json
```
