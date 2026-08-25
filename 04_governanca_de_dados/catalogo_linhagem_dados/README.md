# Catálogo e Linhagem de Dados

Catálogo técnico com estatísticas por coluna + grafo de linhagem para análise de impacto.

## Destaques
- `Catalogo`: registra tabelas (esquema, linhas, % nulos) e persiste em JSON
- `Linhagem`: DAG origem → transformação → destino com busca upstream/downstream
- Análise de impacto: "o que quebra se eu mudar a tabela X?"
- Árvore ASCII da cadeia de dependências

## Stack
pandas, stdlib

## Como rodar
```bash
python main.py   # salva outputs/catalogo.json e imprime as árvores
```
