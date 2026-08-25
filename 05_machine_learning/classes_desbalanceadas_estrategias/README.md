# Classes Desbalanceadas — Estratégias Comparadas

Fraude rara: o que realmente ajuda quando 97% da base é "não".

## Destaques
- Baseline vs `class_weight="balanced"` vs oversampling manual vs ajuste de threshold
- Oversampling do minority implementado na mão (sem SMOTE externo)
- Threshold otimizado por F1 em vez do default 0.5
- PR-AUC (a métrica honesta para desbalanceamento) + curvas PR

## Stack
numpy, scikit-learn, matplotlib

## Como rodar
```bash
python main.py
```
