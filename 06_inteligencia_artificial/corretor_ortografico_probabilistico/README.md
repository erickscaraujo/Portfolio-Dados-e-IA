# Corretor Ortográfico Probabilístico

O clássico corretor estilo Norvig: distância de edição + frequência de palavras.

## Destaques
- Candidatos a distância 1 e 2 de edição (inserção, remoção, troca, transposição)
- Prior de linguagem aprendido do próprio corpus
- Regra de decisão: maior frequência vence; empate vai para menor distância
- Avaliação contra typos plantados

## Stack
stdlib apenas (collections, re)

## Como rodar
```bash
python main.py
```
