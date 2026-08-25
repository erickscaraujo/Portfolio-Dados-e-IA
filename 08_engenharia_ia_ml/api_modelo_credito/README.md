# API de Modelo de Crédito (MLOps)

Ciclo completo: treino versionado → artefatos → API REST de inferência.

## Destaques
- `treinar.py` gera modelo + `metadata_modelo.json` (versão, data, features, AUC)
- FastAPI com validação de entrada via Pydantic (`gt`, `le` etc.)
- Endpoints: `POST /predizer`, `GET /saude`, `GET /informacoes`
- Falha rápida no startup se o modelo não existir

## Stack
scikit-learn, joblib, FastAPI, Pydantic, uvicorn

## Como rodar
```bash
python treinar.py
uvicorn app:app --reload --port 8000
```

## Testando a inferência
```bash
curl -X POST http://localhost:8000/predizer -H "Content-Type: application/json" -d "{\"renda\": 5200, \"idade\": 34, \"tempo_emprego_anos\": 6, \"divida_sobre_renda\": 0.25, \"score_serasa\": 640, \"atrasos_12m\": 1}"
```
