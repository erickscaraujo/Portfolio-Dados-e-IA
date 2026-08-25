# Experimentação Sequencial com Guardrails

O problema de "espiar" o teste A/B antes da hora, medido em simulação.

## Destaques
- 1.500 experimentos sob H0 (sem efeito real) simulados
- Horizon fixo vs peeking a cada lote: inflação de falsos positivos quantificada
- Guardrail operacional: latência acima do teto aborta o teste automaticamente
- Recomendação: pré-registre n ou use testes sequenciais formais (SPRT/mSPRT)

## Stack
numpy, scipy

## Como rodar
```bash
python main.py
```
