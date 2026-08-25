# Registro de Experimentos (mini-MLflow)

Treino com grid de hiperparâmetros e tracking persistido — a base do MLOps.

## Destaques
- `runs.jsonl` append-only: histórico imutável de params/métricas/artefatos
- Grid de 4 combinações; cada uma gera um `run_id` rastreável
- Melhor run recuperado **do registro**, não da memória (reprodutibilidade)
- Artefatos versionados por combinação de parâmetros

## Stack
scikit-learn, joblib, stdlib

## Como rodar
```bash
python treinar.py   # treina o grid e consulta outputs/runs.jsonl
```
