# Drift Multivariado via Classificador de Domínio

Treino × produção como classificação binária: AUC alto = distribuição mudou.

## Destaques
- Técnica moderna (estilo Alibi Detect): modelo distingue treino de produção?
- AUC ~0.5 = mundos idênticos; AUC crescente = drift multivariado
- Varredura da magnitude do drift com curva AUC × shift
- KS por feature para atribuir o drift às variáveis culpadas

## Stack
numpy, scikit-learn, scipy, matplotlib

## Como rodar
```bash
python main.py   # gera outputs/drift_multivariado.png
```
