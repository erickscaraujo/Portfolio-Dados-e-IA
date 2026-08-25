# Particiona o CSV anual por mes e escreve o manifest

dir.create("outputs", showWarnings = FALSE)

RAIZ_PARTICOES <- "outputs/particionado"

vendas <- read.csv("fontes/vendas_ano.csv", stringsAsFactors = FALSE)
vendas$mes <- substr(vendas$data, 1, 7)

cat(sprintf("Fonte: %d linhas, %d meses\n",
            nrow(vendas), length(unique(vendas$mes))))

# --- particiona ---------------------------------------------------------------
particoes <- split(vendas, vendas$mes)
manifesto <- data.frame(particao = names(particoes), linhas = NA_integer_)

for (nome_particao in names(particoes)) {
  pasta <- file.path(RAIZ_PARTICOES, paste0("mes=", nome_particao))
  dir.create(pasta, recursive = TRUE, showWarnings = FALSE)

  particao <- particoes[[nome_particao]]
  write.csv(particao[, names(particao) != "mes"],
            file.path(pasta, "vendas.csv"), row.names = FALSE)

  manifesto[manifesto$particao == nome_particao, "linhas"] <- nrow(particao)
}

write.csv(manifesto, file.path(RAIZ_PARTICOES, "_manifest.csv"), row.names = FALSE)

cat("\n=== MANIFEST ===\n")
print(manifesto, row.names = FALSE)

# --- verificacao de integridade ----------------------------------------------
total_fonte <- sum(manifesto$linhas)
stopifnot(total_fonte == nrow(vendas))

amostra_lida <- read.csv(
  list.files(file.path(RAIZ_PARTICOES, paste0("mes=", names(particoes)[1])),
             full.names = TRUE)[1]
)
stopifnot(nrow(amostra_lida) == manifesto$linhas[1])

cat(sprintf("\nIntegridade OK: %d = soma das particoes; amostra re-lida confere.\n",
            total_fonte))
