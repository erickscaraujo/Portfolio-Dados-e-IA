# Model Card — Documentação Responsável Automática

O cartão do modelo gerado junto com o treino, incluindo métricas por grupo.

## Destaques
- Treino de modelo de crédito sintético + avaliação por região
- `model_card.md` gerado programaticamente: uso pretendido, dados, métricas, limitações
- Limitações escritas dinamicamente: amplitude de aprovação entre grupos dispara aviso
- Padrão de estrutura compatível com o que se espera de Model Cards (Google/Meta)

## Stack
scikit-learn, pandas, numpy

## Como rodar
```bash
python main.py   # treina e gera outputs/model_card.md
```
