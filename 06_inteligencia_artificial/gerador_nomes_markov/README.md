# Gerador de Nomes — Cadeias de Markov

Geração de texto clássica: cadeia de Markov de caracteres treinada em nomes de produto.

## Destaques
- Modelo ordem-3 com tokens de início/fim
- Amostragem com temperatura controla criatividade × plausibilidade
- Filtra nomes muito curtos/duplicados; métrica de diversidade
- 100% offline, stdlib apenas

## Stack
stdlib (collections, random)

## Como rodar
```bash
python main.py
```
