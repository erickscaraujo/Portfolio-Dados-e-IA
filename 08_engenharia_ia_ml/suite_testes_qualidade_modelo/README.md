# Suíte de Testes de Qualidade de Modelo

"Unit tests para modelos": portões de qualidade que bloqueiam o deploy.

## Destaques
- 5 checks: AUC global, AUC por região (fairness de slice), faixa de probabilidade, monotonicidade e estabilidade de taxa de aprovação
- Cada check devolve pass/fail com detalhe legível
- Exit code do processo reflete o gate (pronto para CI)
- Um check falha de propósito na primeira execução para demonstrar o bloqueio

## Stack
scikit-learn, pandas, numpy

## Como rodar
```bash
python main.py   # roda a suíte; exit code 0 só se tudo passar
```
