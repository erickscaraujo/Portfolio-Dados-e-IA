# Linhagem em Nível de Coluna

Impacto com granularidade de coluna: "quem consome `raw.clientes.cpf`?"

## Destaques
- Arestas coluna → coluna com a transformação que as gerou
- BFS downstream/upstream por coluna (não só por tabela)
- Árvore ASCII agrupada por tabela destino
- Consultas de impacto e origem para análise de mudança de schema

## Stack
stdlib apenas (collections)

## Como rodar
```bash
python main.py
```
