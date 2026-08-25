# Descoberta e Perfilagem de Fontes

Scanner automático de pastas: inventário, perfil e chaves candidatas sem registro manual.

## Destaques
- Varre `fontes/` (CSV), perfila linhas/tipos/nulos/únicos/amostra
- Detecta chaves primárias candidatas (únicas, não nulas)
- Sugere relações FK entre arquivos (valores contidos em outra tabela)
- Saída: `inventario_fontes.json` + resumo markdown

## Stack
pandas, pathlib, stdlib

## Como rodar
```bash
python main.py   # gera outputs/inventario_fontes.json
```
