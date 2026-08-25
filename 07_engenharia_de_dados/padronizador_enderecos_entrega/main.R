# Padronizacao de enderecos para entrega e deduplicacao

dir.create("outputs", showWarnings = FALSE)
set.seed(740)

ENDERECOS_CRUS <- c(
  "r. das flores, 123 - apto 42", "Rua das Flores, 123 ap 42",
  "AV  PAULISTA 1500 cj 101", "Avenida Paulista, nº 1000",
  "trav. sao jorge 88", "TRAVESSA SAO JORGE, 88",
  "rod. anchieta km 15", "Rodovia Anchieta km quinze",
  "r sete de setembro, 456/302", "Rua Sete de Setembro 456 ap 302",
  "av brasil 22 - bl b", "Av. BRASIL, 22 Bloco B"
)

MAPA_TIPO_LOGRADOURO <- c(
  "r." = "R.", "rua" = "R.", "av" = "Av.", "avenida" = "Av.",
  "trav." = "Trav.", "travessa" = "Trav.",
  "rod." = "Rod.", "rodovia" = "Rod."
)


normalizar_endereco <- function(endereco) {
  texto <- tolower(trimws(endereco))

  # separadores visuais viram espaco antes do mapeamento
  texto <- gsub("[.,;#]+", " ", texto)
  texto <- trimws(gsub("\\s+", " ", texto))

  # padroniza o tipo de logradouro pela primeira palavra
  primeira_palavra <- sub(" .*$", "", texto)
  if (primeira_palavra %in% names(MAPA_TIPO_LOGRADOURO)) {
    texto <- paste(MAPA_TIPO_LOGRADOURO[primeira_palavra], sub("^\\S+ ", "", texto))
  }

  # caixa titulo em cada palavra, preservando conectivos minusculos
  palavras <- strsplit(texto, " ")[[1]]
  conectivos <- c("de", "da", "do", "das", "dos", "e")
  capitalizado <- ifelse(palavras %in% conectivos,
                         palavras,
                         paste0(toupper(substring(palavras, 1, 1)),
                                substring(palavras, 2)))
  paste(capitalizado, collapse = " ")
}


chave_dedup <- function(endereco_padronizado) {
  chave <- tolower(gsub("[^a-z0-9]", "", endereco_padronizado))
  # numeros finais (numero/apto) entram na chave para nao fundir residencias
  chave
}

enderecos_padronizados <- vapply(ENDERECOS_CRUS, normalizar_endereco, character(1))
chaves <- vapply(enderecos_padronizados, chave_dedup, character(1))

resultado <- data.frame(
  original = ENDERECOS_CRUS,
  padronizado = unname(enderecos_padronizados),
  stringsAsFactors = FALSE
)

cat("=== ANTES X DEPOIS ===\n")
for (i in seq_len(nrow(resultado))) {
  cat(sprintf("- (%s)\n  -> %s\n",
              resultado$original[i], resultado$padronizado[i]))
}

duplicatas_visuais <- sum(duplicated(chaves))
cat(sprintf("\nEnderecos: %d | chaves unicas apos padronizar: %d | duplicatas visuais: %d\n",
            length(chaves), length(unique(chaves)), duplicatas_visuais))

if (duplicatas_visuais > 0) {
  chaves_repetidas <- unique(chaves[duplicated(chaves)])
  for (chave in chaves_repetidas) {
    indices <- which(chaves == chave)
    cat(sprintf("\nMesmo local detectado:\n"))
    for (i in indices) {
      cat(sprintf("   * %s\n", resultado$original[i]))
    }
  }
}

write.csv(data.frame(original = ENDERECOS_CRUS,
                     padronizado = unname(enderecos_padronizados),
                     chave_dedup = unname(chaves)),
          "outputs/enderecos_padronizados.csv", row.names = FALSE)
cat("\nCSV salvo em outputs/enderecos_padronizados.csv\n")
