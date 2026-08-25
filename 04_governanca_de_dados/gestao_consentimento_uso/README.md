# Gestão de Consentimentos (LGPD)

Quem autorizou o quê, até quando — e campanhas que precisam respeitar isso.

## Destaques
- Consents por finalidade (marketing, compartilhamento) com validade de 12 meses
- Filtro de público-alvo da campanha respeitando consentimento vigente
- Propagação de opt-out: revogação vale para todas as listas
- Trilha de auditoria JSON com decisão por cliente

## Stack
pandas, stdlib

## Como rodar
```bash
python main.py   # salva outputs/auditoria_consentimentos.json
```
