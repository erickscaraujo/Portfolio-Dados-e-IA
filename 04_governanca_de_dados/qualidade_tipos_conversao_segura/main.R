# Conversao segura de tipos: CSV sujo -> tipos confiaveis com auditoria

dir.create("outputs", showWarnings = FALSE)
set.seed(670)

# --- base suja de proposito --------------------------------------------------
gerar_csv_sujo <- function(n = 400) {
  valores <- vapply(seq_len(n), function(i) {
    estilo <- sample(c("br", "us", "texto", "vazio"), 1, prob = c(0.7, 0.2, 0.07, 0.03))
    numero <- runif(1, 10, 9000)
    switch(estilo,
      br = formatC(numero, format = "f", digits = 2, decimal.mark = ",", big.mark = "."),
      us = formatC(numero, format = "f", digits = 2),
      texto = paste0("R$ ", formatC(numero, format = "f", digits = 2)),
      vazio = ""
    )
  }, character(1))

  datas <- vapply(seq_len(n), function(i) {
    data_aleatoria <- as.Date("2025-01-01") + sample(0:300, 1)
    if (i %% 3 == 0) {
      format(data_aleatoria, "%d/%m/%Y")
    } else {
      format(data_aleatoria, "%Y-%m-%d")
    }
  }, character(1))

  codigos <- sprintf("%05d", sample(100:999, n, replace = TRUE))

  # coluna codigo salva SEM aspas no csv perde o zero a esquerda; simulamos isso
  codigos <- sub("^0+", "", codigos)

  suja <- data.frame(valor_txt = valores, data_txt = datas, codigo_txt = codigos,
                     stringsAsFactors = FALSE)
  write.csv(suja, "fontes_suja.csv", row.names = FALSE)
  suja
}

dir.create(".", showWarnings = FALSE)
suja <- gerar_csv_sujo()
relida <- read.csv("fontes_suja.csv", colClasses = "character")

# --- conversores defensivos ---------------------------------------------------
converter_numero <- function(texto) {
  limpo <- gsub("[^0-9,.-]", "", texto)
  limpo <- gsub("\\.", "", limpo)          # separador de milhar brasileiro
  limpo <- sub(",", "\\.", limpo)
  resultado <- suppressWarnings(as.numeric(limpo))
  list(valor = resultado, falhou = is.na(resultado))
}

converter_data <- function(texto) {
  resultado <- suppressWarnings(as.Date(texto, tryFormats = c("%Y-%m-%d", "%d/%m/%Y")))
  list(valor = resultado, falhou = is.na(resultado))
}

converter_codigo <- function(texto) {
  digitos <- gsub("\\D", "", texto)
  resultado <- ifelse(nchar(digitos) %in% 3:5, sprintf("%05s", digitos), NA_character_)
  list(valor = resultado, falhou = is.na(resultado))
}

# --- aplicacao com auditoria ---------------------------------------------------
auditar_coluna <- function(valores, conversor, nome_coluna) {
  resultado <- conversor(valores)
  falhas <- which(resultado$falhou)
  data.frame(
    coluna = nome_coluna,
    total = length(valores),
    convertidos = sum(!resultado$falhou),
    taxa_sucesso_pct = round(sum(!resultado$falhou) / length(valores) * 100, 1),
    exemplos_falha = paste(head(valores[falhas], 3), collapse = " | ")
  )
}

relatorio <- rbind(
  auditar_coluna(relida$valor_txt, converter_numero, "valor"),
  auditar_coluna(relida$data_txt, converter_data, "data"),
  auditar_coluna(relida$codigo_txt, converter_codigo, "codigo")
)

cat("=== RELATORIO DE CONVERSAO ===\n")
print(relatorio, row.names = FALSE)

numeros_convertidos <- converter_numero(relida$valor_txt)$valor
datas_convertidas <- converter_data(relida$data_txt)$valor
codigos_convertidos <- converter_codigo(relida$codigo_txt)$valor

base_limpa <- data.frame(
  valor = numeros_convertidos,
  data = datas_convertidas,
  codigo = codigos_convertidos
)
write.csv(base_limpa, "outputs/base_tipos_corrigidos.csv", row.names = FALSE)
write.csv(relatorio, "outputs/relatorio_conversoes.csv", row.names = FALSE)

cat("\nBase convertida e relatorios salvos em outputs/\n")
