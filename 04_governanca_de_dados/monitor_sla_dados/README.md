# Monitor de SLA e Frescura de Dados

Observabilidade das tabelas: está atualizada? falhou quantas vezes? precisa acordar alguém?

## Destaques
- Contrato de atualização por tabela (horária/diária) com checagem de idade (`freshness`)
- Taxa de sucesso em 7 dias + detecção de falhas consecutivas
- Regra de escalação: crítico → alerta → ok, com justificativa legível
- Relatório JSON pronto para integrar com on-call/PagerDuty

## Stack
pandas, stdlib

## Como rodar
```bash
python main.py   # imprime o status e salva outputs/alertas_sla.json
```
