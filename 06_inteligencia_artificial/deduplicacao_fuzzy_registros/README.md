# Deduplicação Fuzzy de Cadastros

Encontra "a mesma pessoa escrita de jeitos diferentes" sem bibliotecas pagas.

## Destaques
- Normalização + `SequenceMatcher` para similaridade de nomes
- Blocking por inicial evita comparação quadrática na base inteira
- Confirmação por e-mail **ou** dígitos do telefone (reduz falsos positivos)
- Union-find transforma pares em clusters prontos para consolidação
- Caso-armadilha Rafael × Rafaella para discutir revisão humana

## Stack
stdlib apenas (difflib)

## Como rodar
```bash
python main.py
```
