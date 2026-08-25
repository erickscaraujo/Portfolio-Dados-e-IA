# RAG com Respostas Citadas

Retrieval-Augmented Generation sem LLM: busca + resposta montada com citação da fonte.

## Destaques
- Base de conhecimento dividida em chunks com título
- TF-IDF + cosseno para recuperar os trechos mais relevantes
- Compositor extrai a sentença mais sobreposta à pergunta dentro do chunk
- Citação obrigatória da fonte e fallback honesto abaixo do limiar de similaridade

## Stack
scikit-learn, numpy

## Como rodar
```bash
python main.py
```
