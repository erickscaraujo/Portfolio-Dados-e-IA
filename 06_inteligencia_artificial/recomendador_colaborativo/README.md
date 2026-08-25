# Recomendador Colaborativo (Item-Item)

Filtragem colaborativa clássica: similaridade entre itens sobre avaliações esparsas.

## Destaques
- Matriz de preferências latentes por gênero gerando ratings sintéticos
- Similaridade cosseno item-item com centralização por média do usuário
- Predição ponderada pelos vizinhos + top-N de itens nunca avaliados
- Avaliação em holdout: RMSE e Hit@5

## Stack
numpy, stdlib

## Como rodar
```bash
python main.py
```
