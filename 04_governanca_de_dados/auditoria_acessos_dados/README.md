# Auditoria de Acessos a Dados

Menor privilégio, contas dormentes e segregação de funções em um só relatório.

## Destaques
- Acesso a dado restrito sem justificativa formal → suspensão
- Contas sem login há 90+ dias → revogação (com severidade por sensibilidade)
- Admin desnecessário em view de leitura → rebaixamento
- Conflito de SoD detectado (escreve PII + lê folha) → separação de responsabilidades
- JSON com plano de remediação ordenado por severidade

## Stack
pandas, stdlib

## Como rodar
```bash
python main.py   # salva outputs/achados_auditoria.json
```
