# Validador de Contrato de Schema

Data contracts: a fonte mudou o schema e o pipeline precisa saber antes de quebrar.

## Destaques
- Contrato declarativo: tipos, não nulas, domínios e chave primária
- Severidades distintas — quebra (bloqueia) vs aviso (coluna nova)
- Simulação realista: v2 chega com coluna renomeada, tipo trocado e nulos
- Gate de deploy + relatório JSON por versão

## Stack
pandas, stdlib (json, dataclasses)

## Como rodar
```bash
python main.py   # valida v1 e v2, salva outputs/contrato_v*.json
```
