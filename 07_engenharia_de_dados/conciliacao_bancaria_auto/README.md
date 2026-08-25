# Conciliação Bancária Automática

Extrato × contabilidade: casar lançamentos com tolerância e isolar divergências.

## Destaques
- Matching em duas fases: valor exato → janela de ±3 dias
- Tratamento de duplicatas (cada lançamento casa no máximo uma vez)
- Classificação: conciliado, diferença de valor, só no extrato, só no ledger
- Relatório de pendências + taxa de conciliação automática

## Stack
pandas, stdlib

## Como rodar
```bash
python main.py   # salva outputs/conciliacao_pendencias.csv
```
