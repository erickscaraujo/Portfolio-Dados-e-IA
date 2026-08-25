# Política de Classificação de Dados

Cada coluna recebe um nível de sensibilidade e um conjunto de regras de tratamento.

## Destaques
- 4 níveis: público → interno → confidencial → restrito
- Regras por nome da coluna **e** conteúdo (regex detecta e-mail no dado)
- Tratamento associado: exibir/mascarar/bloquear, compartilhamento externo, criptografia
- Manifesto JSON consumível por pipelines e catálogos

## Stack
pandas, stdlib (re, json)

## Como rodar
```bash
python main.py   # gera outputs/manifesto_classificacao.json
```
