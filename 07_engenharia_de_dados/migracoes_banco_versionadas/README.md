# Migrações de Banco Versionadas

Schema evolui como código: migrações numeradas, aplicadas uma única vez.

## Destaques
- Tabela `schema_migrations` controla o que já rodou
- Migrações aplicadas em ordem, cada uma em transação própria
- Re-executar o runner é seguro (idempotência demonstrada)
- Rollback da última migração com SQL `down` correspondente
- Verificação de integridade ao final

## Stack
sqlite3, stdlib

## Como rodar
```bash
python main.py   # cria outputs/app_migracoes.sqlite
```
