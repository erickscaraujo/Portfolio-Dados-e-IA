# Politica de retencao: o que venceu e pode ser descartado

dir.create("outputs", showWarnings = FALSE)
set.seed(470)

HOJE <- as.Date("2025-07-01")

# helper: trimestre da data
quarter_data <- function(datas) floor((as.integer(format(datas, "%m")) - 1) / 3) + 1

# prazos legais/politica interna por categoria de dado (em meses)
RETENCAO_MESES <- c(
  logs_acesso = 6,
  pedidos_cancelados = 60,
  curriculos_reprovados = 12,
  dados_marketing_inativo = 24,
  notas_fiscais = 300
)

gerar_registros <- function() {
  linhas <- list()
  id_global <- 0

  for (categoria in names(RETENCAO_MESES)) {
    n <- switch(categoria,
      logs_acesso = 1500,
      pedidos_cancelados = 400,
      curriculos_reprovados = 220,
      dados_marketing_inativo = 600,
      notas_fiscais = 350
    )
    # criacao entre 5 anos atras e hoje
    idade_dias <- sample(0:1825, n, replace = TRUE)
    linhas[[categoria]] <- data.frame(
      registro_id = seq_len(n) + id_global,
      categoria = categoria,
      criado_em = HOJE - idade_dias,
      stringsAsFactors = FALSE
    )
    id_global <- id_global + n
  }
  do.call(rbind, linhas)
}

registros <- gerar_registros()
registros$vencimento <- registros$criado_em +
  as.numeric(RETENCAO_MESES[registros$categoria]) * 30.44
registros$situacao <- ifelse(registros$vencimento <= HOJE, "vencido", "retido")

# --- resumo -----------------------------------------------------------------
tabela_situacao <- table(registros$categoria, registros$situacao)
resumo_wide <- data.frame(
  categoria = rownames(tabela_situacao),
  vencido = as.integer(tabela_situacao[, "vencido"]),
  retido = as.integer(tabela_situacao[, "retido"]),
  stringsAsFactors = FALSE
)
resumo_wide$prazo_meses <- RETENCAO_MESES[resumo_wide$categoria]

cat("=== RETENCAO POR CATEGORIA ===\n")
print(resumo_wide[order(-resumo_wide$vencido), ], row.names = FALSE)

fila_descarte <- registros[registros$situacao == "vencido", ]
cat(sprintf("\nTotal vencido para exclusao: %d de %d registros (%.0f%%)\n",
            nrow(fila_descarte), nrow(registros),
            nrow(fila_descarte) / nrow(registros) * 100))

mais_antigo <- fila_descarte[which.min(fila_descarte$criado_em), ]
cat(sprintf("Registro mais antigo da fila: %s criado em %s\n",
            mais_antigo$categoria, mais_antigo$criado_em))

# --- agenda: descarte em lotes trimestrais ----------------------------------
fila_descarte$lote <- paste0(
  "T", format(fila_descarte$vencimento, "%Y"), "-Q",
  quarter_data(fila_descarte$vencimento)
)

agenda <- table(fila_descarte$lote)
cat("\n=== AGENDA DE DESCARTE POR LOTE ===\n")
for (lote in names(agenda)) {
  cat(sprintf("- %s : %d registros\n", lote, agenda[lote]))
}

write.csv(fila_descarte[, c("registro_id", "categoria", "criado_em", "vencimento")],
          "outputs/fila_descarte.csv", row.names = FALSE)
cat("\nFila de exclusao salva em outputs/fila_descarte.csv\n")
