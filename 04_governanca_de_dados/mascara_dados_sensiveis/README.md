# Máscara de Dados Sensíveis (LGPD)

Anonimização de PII para bases que precisam sair do ambiente restrito.

## Destaques
- Detecção por regex de CPF, e-mail e telefone — inclusive em texto livre
- Estratégias distintas: hash SHA-256 determinístico (pseudonimização) vs máscara parcial
- Relatório de auditoria com contagem do que foi tratado
- Checagem final automatizada de vazamento na base entregue

## Stack
pandas, stdlib (re, hashlib)

## Como rodar
```bash
python main.py   # gera outputs/clientes_anonimizados.csv
```
