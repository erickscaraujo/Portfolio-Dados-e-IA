# Diálogo com Slots — Reserva de Viagem

State tracking multi-turno: preenche, corrige, confirma.

## Destaques
- Máquina de estados com slots obrigatórios (origem, destino, data)
- Extração de entidades via regex + lista de cidades; datas relativas ("amanhã")
- Correções aceitas a qualquer momento ("na verdade para Recife")
- Confirmação explícita antes de "finalizar" a reserva

## Stack
stdlib apenas (re, datetime)

## Como rodar
```bash
python main.py
```
