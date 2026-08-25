# Feature Store Simples

O problema clássico de treino × serving resolvido por construção.

## Destaques
- `calcular_features` é a única fonte de verdade — offline e online chamam a mesma função
- Job offline publica no SQLite; caminho online lê com cache TTL
- Verificação explícita de consistência entre o que o modelo treinou e o que ele recebe em produção

## Stack
pandas, numpy, sqlite3, stdlib

## Como rodar
```bash
python main.py   # publica outputs/online_store.db e valida a consistência
```
