# Chatbot de Intenções

NLU de atendimento bancário rodando 100% local, sem APIs pagas.

## Destaques
- TF-IDF de char n-grams (tolera erros de digitação) + Regressão Logística
- Fallback automático quando a confiança fica abaixo do limiar
- Holdout estratificado para medir generalização
- Loop de conversa interativo no terminal

## Stack
scikit-learn

## Como rodar
```bash
python main.py
```
Experimente: "quero ver meu saldo", "falar com atendente", "blablabla" (dispara o fallback).
