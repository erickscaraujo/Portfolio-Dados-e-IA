# Lakehouse Medallion

Arquitetura bronze → silver → gold implementada sobre arquivos.

## Destaques
- **Bronze**: ingestão fiel com sujeira realista (duplicatas + tipos quebrados)
- **Silver**: tipagem, dedup por id mantendo a última chegada, contrato mínimo
- **Gold**: agregado diário pronto para BI
- `_manifest.json` por camada (arquivos, linhas, timestamp) para rastreabilidade

## Stack
pandas, numpy, stdlib (json)

## Como rodar
```bash
python main.py   # constrói outputs/lakehouse/{bronze,silver,gold}
```
