# Busca Semântica em Documentos

Mini motor de busca FAQ: recuperação por similaridade, 100% local.

## Destaques
- TF-IDF com bigramas + cosseno entre consulta e documentos
- Métrica Hits@2 sobre consultas reescritas com vocabulário diferente do corpus
- Ranking com scores e trechos — pronto para virar API ou RAG baseline

## Stack
scikit-learn

## Como rodar
```bash
python main.py
```
