# Previsão de Churn — Telecom

Modelo supervisionado de retenção com pipeline reprodutível.

## Destaques
- `ColumnTransformer` + `Pipeline` (escala numérica, one-hot categórico)
- Validação cruzada estratificada e holdout com AUC/precisão/recall/F1
- Matriz de confusão legível e fatores que mais explicam o churn
- Modelo serializado (`joblib`) com exemplo de scoring de cliente novo
- Curva ROC comparando os modelos

## Stack
pandas, numpy, scikit-learn, joblib, matplotlib

## Como rodar
```bash
python main.py
```
