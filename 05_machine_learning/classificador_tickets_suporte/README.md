# Classificador de Tickets de Suporte

Roteamento automático de tickets em 4 filas com interpretação das decisões.

## Destaques
- Base sintética por templates com vocabulário característico por fila
- TF-IDF + Regressão Logística multiclasse com holdout estratificado
- Relatório de classificação, matriz de confusão e exemplos mal roteados
- Palavras-chave que mais definem cada fila (pesos do modelo)

## Stack
scikit-learn

## Como rodar
```bash
python main.py
```
