# Curvas de Aprendizado — Diagnóstico de Overfit/Underfit

Mais dado resolve? O gráfico responde antes de você gastar tempo rotulando.

## Destaques
- Curvas manuais: treino/validação por tamanho de amostra (50 → 4.000)
- RandomForest não regularizado (overfit clássico) × LinearRegression (underfit)
- Diagnóstico automático pela largura do gap treino×validação
- Recomendação de ação para cada diagnóstico

## Stack
numpy, scikit-learn, matplotlib

## Como rodar
```bash
python main.py   # gera outputs/aprendizado_diagnostico.png
```
