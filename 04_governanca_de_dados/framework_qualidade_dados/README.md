# Framework de Qualidade de Dados

Motor declarativo de regras de qualidade aplicado a um cenário com defeitos plantados.

## Destaques
- 7 tipos de regra: nulos, unicidade, intervalo, regex, domínio, data passada e integridade referencial
- Scores por dimensão (completude, unicidade, validade, consistência)
- Relatório JSON para integração com pipelines

## Stack
pandas

## Como rodar
```bash
python main.py   # imprime o relatório e salva outputs/relatorio_qualidade.json
```

## Estender
Adicione uma `Regra` à lista em `main.py` — ou um novo `case` no `motor_qualidade.py`.
