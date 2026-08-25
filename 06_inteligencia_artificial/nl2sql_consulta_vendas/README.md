# NL2SQL — Perguntas em Português sobre Vendas

Tradutor pergunta → SQL → resultado, sem depender de LLM ou API externa.

## Destaques
- Parser rule-based: agregação (total/média/quantidade), agrupamento (categoria/cidade/mês) e filtros (categoria, cidade, ano)
- SQL gerado é executado num SQLite criado na hora
- Resposta honesta quando a pergunta foge do vocabulário suportado
- Base sólida para depois plugar um LLM com guardrails

## Stack
pandas, numpy, sqlite3

## Como rodar
```bash
python main.py   # cria outputs/vendas.db e responde as perguntas demo
```
