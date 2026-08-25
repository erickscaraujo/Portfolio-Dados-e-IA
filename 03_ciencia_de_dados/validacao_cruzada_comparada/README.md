# Validação Cruzada Comparada

K-fold embaralhado pode mentir em dados temporais — demonstração com números.

## Destaques
- Mesmo modelo, três estratégias: KFold shuffle, KFold ordenado e TimeSeriesSplit
- Dados com regime temporal (tendência + mudança de nível) que punem vazamento
- Gap de MAE entre estratégias quantificado e explicado
- Recomendação prática por tipo de dado

## Stack
pandas, numpy, scikit-learn

## Como rodar
```bash
python main.py
```
