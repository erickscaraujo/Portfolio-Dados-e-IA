# Diff de esquemas entre duas versoes de uma tabela

dir.create("outputs", showWarnings = FALSE)

# esquema = data.frame(coluna, tipo); v2 e o estado atual da fonte
schema_v1 <- data.frame(
  coluna = c("pedido_id", "cliente_id", "valor", "status", "criado_em"),
  tipo = c("character", "integer", "numeric", "character", "Date"),
  stringsAsFactors = FALSE
)

schema_v2 <- data.frame(
  coluna = c("pedido_id", "cliente_id", "valor_str", "novo_status", "data_pedido",
             "cupom"),
  tipo = c("character", "integer", "character", "character", "Date", "character"),
  stringsAsFactors = FALSE
)

# --- diff --------------------------------------------------------------------
diff_schemas <- function(antigo, novo) {
  removidas <- setdiff(antigo$coluna, novo$coluna)
  adicionadas <- setdiff(novo$coluna, antigo$coluna)
  comuns <- intersect(antigo$coluna, novo$coluna)

  mudancas_tipo <- comuns[antigo$tipo[match(comuns, antigo$coluna)] !=
                            novo$tipo[match(comuns, novo$coluna)]]

  list(
    adicionadas = adicionadas,
    removidas = removidas,
    mudancas_tipo = mudancas_tipo,
    renomeadas_provaveis = detectar_renomeacao(removidas, adicionadas, antigo, novo)
  )
}

# heuristica: coluna removida pareia com adicionada de mesmo tipo e prefixo em comum
detectar_renomeacao <- function(removidas, adicionadas, antigo, novo) {
  pares <- list()
  for (velha in removidas) {
    tipo_velho <- antigo$tipo[match(velha, antigo$coluna)]
    candidatas <- adicionadas[novo$tipo[match(adicionadas, novo$coluna)] == tipo_velho]
    if (length(candidatas) == 0) next

    scores <- vapply(candidatas, function(x) {
      nchar(common_prefix(tolower(x), tolower(velha)))
    }, numeric(1))
    melhor <- candidatas[which.max(scores)]
    if (max(scores) >= 3) pares[[length(pares) + 1]] <- c(velha, melhor)
  }
  pares
}

common_prefix <- function(a, b) {
  caracteres <- substr(rep(a, nchar(b)), 1:nchar(b), 1:nchar(b)) ==
    substr(rep(b, nchar(b)), 1:nchar(b), 1:nchar(b))
  if (!all(caracteres)) {
    return(substr(a, 1, max(which(!caracteres)[1] - 1, 0)))
  }
  a
}

resultado <- diff_schemas(schema_v1, schema_v2)

# --- relatorio ---------------------------------------------------------------
linhas <- c(
  "# Changelog de schema — pedidos",
  "",
  sprintf("_Comparado em %s_", format(Sys.time(), "%Y-%m-%d %H:%M")),
  ""
)

if (length(resultado$mudancas_tipo) > 0) {
  linhas <- c(linhas, "## Quebras (bloqueiam deploy)", "")
  for (coluna in resultado$mudancas_tipo) {
    tipo_antigo <- schema_v1$tipo[schema_v1$coluna == coluna]
    tipo_novo <- schema_v2$tipo[schema_v2$coluna == coluna]
    linhas <- c(linhas,
                sprintf("- **Tipo alterado** `%s`: %s -> %s",
                        coluna, tipo_antigo, tipo_novo))
  }
}

# renames so sao seguros se o tipo tambem casar
renomes_seguros <- list()
renomes_quebra <- list()
for (par in resultado$renomeadas_provaveis) {
  tipo_velho <- schema_v1$tipo[match(par[1], schema_v1$coluna)]
  tipo_novo <- schema_v2$tipo[match(par[2], schema_v2$coluna)]
  if (is.na(tipo_novo) || tipo_velho != tipo_novo) {
    renomes_quebra[[length(renomes_quebra) + 1]] <- par
  } else {
    renomes_seguros[[length(renomes_seguros) + 1]] <- par
  }
}

removidas_sem_par <- setdiff(resultado$removidas,
                             vapply(c(renomes_seguros, renomes_quebra), function(p) p[1], character(1)))
for (coluna in removidas_sem_par) {
  linhas <- c(linhas, "", "## Quebras (bloqueiam deploy)", "",
              sprintf("- **Coluna removida** `%s`", coluna))
}
for (par in renomes_quebra) {
  linhas <- c(linhas, sprintf("- **Rename com troca de tipo** `%s` -> `%s`", par[1], par[2]))
}

tem_quebra <- length(resultado$mudancas_tipo) > 0 || length(renomes_quebra) > 0 ||
  length(removidas_sem_par) > 0

if (length(resultado$adicionadas) + length(renomes_seguros) > 0) {
  linhas <- c(linhas, "", "## Novidades (sem quebra)", "")
  for (par in renomes_seguros) {
    linhas <- c(linhas,
                sprintf("- **Rename provável** `%s` -> `%s` (mesmo tipo)",
                        par[1], par[2]))
  }
  novas_limpas <- setdiff(resultado$adicionadas,
                          sapply(renomes_seguros, function(p) p[2]))
  for (coluna in novas_limpas) {
    linhas <- c(linhas, sprintf("- **Coluna nova** `%s`", coluna))
  }
}

linhas <- c(linhas, "", ifelse(tem_quebra,
                               "**GATE: BLOQUEADO** — ajustar contrato antes do deploy.",
                               "**GATE: LIBERADO**"))

writeLines(linhas, "outputs/changelog_schema.md")
cat(paste(linhas, collapse = "\n"))
