# Trilha de Auditoria com Hash Chain

Log append-only onde qualquer edição no passado quebra a cadeia — prova de integridade.

## Destaques
- Cada registro carrega `hash = sha256(hash_anterior + payload)`
- Verificador percorre a cadeia e aponta exatamente o registro adulterado
- Demonstração: inserção legítima × tentativa de alteração retroativa
- 100% stdlib (hashlib, json)

## Stack
stdlib apenas

## Como rodar
```bash
python main.py
```
