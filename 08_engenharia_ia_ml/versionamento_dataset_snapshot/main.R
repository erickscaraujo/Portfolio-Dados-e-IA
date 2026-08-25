# Snapshots de dataset com hash por registro e diff entre versoes

dir.create("outputs/snapshots", recursive = TRUE, showWarnings = FALSE)
set.seed(530)

hash_registro <- function(chave, campos) {
  digesto <- paste(c(as.character(chave), as.character(campos)), collapse = "|")
  substr(digest(digesto), 1, 12)
}

# FNV-1a simplificado com modulo 2^24 (mantem aritmetica exata em doubles)
digest <- function(texto) {
  modulo <- 2^24
  h <- 0
  for (b in charToRaw(texto)) {
    h <- (h * 16777619 + as.integer(b)) %% modulo
  }
  sprintf("%06x", h)
}

gerar_base <- function(n = 500, mutar = FALSE, seed = 540) {
  ids <- sprintf("CLI%04d", seq_len(n))
  saldos <- round(runif(n, 100, 20000) * (if (mutar) 1 else 1), 2)
  status <- sample(c("ativo", "suspenso"), n, replace = TRUE, prob = c(0.85, 0.15))

  if (mutar) {
    set.seed(seed + 1)
    mudar <- sample(seq_len(n), 40)
    saldos[mudar] <- round(saldos[mudar] * runif(40, 0.7, 1.4), 2)
    suspender <- sample(setdiff(seq_len(n), mudar), 15)
    status[suspender] <- "suspenso"
    removidos <- head(mudar, 10)
    return(list(
      data = data.frame(cliente_id = ids[-removidos], saldo = saldos[-removidos],
                        status = status[-removidos], stringsAsFactors = FALSE),
      removidos = ids[removidos]
    ))
  }

  list(data = data.frame(cliente_id = ids, saldo = saldos,
                         status = status, stringsAsFactors = FALSE))
}

base_v1 <- gerar_base(n = 500)$data
mutacao <- gerar_base(n = 500, mutar = TRUE)
base_v2 <- mutacao$data

# --- snapshot com hashes -----------------------------------------------------
snapshot <- function(df) {
  df$registro_hash <- mapply(
    function(id, saldo, st) hash_registro(id, c(saldo, st)),
    df$cliente_id, df$saldo, df$status
  )
  df
}

v1 <- snapshot(base_v1)
v2 <- snapshot(base_v2)

cat("=== SNAPSHOTS ===\n")
cat(sprintf("- v1: %d registros | v2: %d registros\n", nrow(v1), nrow(v2)))

# --- diff --------------------------------------------------------------------
chaves_v1 <- v1$cliente_id
chaves_v2 <- v2$cliente_id

adicionados <- setdiff(chaves_v2, chaves_v1)
removidos <- setdiff(chaves_v1, chaves_v2)
comuns <- intersect(chaves_v1, chaves_v2)

hash_v1 <- v1$registro_hash[match(comuns, v1$cliente_id)]
hash_v2 <- v2$registro_hash[match(comuns, v2$cliente_id)]
alterados <- comuns[hash_v1 != hash_v2]

cat(sprintf("\n=== DIFF v1 -> v2 ===\n"))
cat(sprintf("- adicionados : %d\n- removidos   : %d (%s...)\n",
            length(adicionados), length(removidos),
            paste(head(removidos, 3), collapse = ", ")))
cat(sprintf("- alterados   : %d\n", length(alterados)))

if (length(alterados) > 0) {
  comparacao <- merge(
    v1[v1$cliente_id %in% alterados, c("cliente_id", "saldo")],
    v2[v2$cliente_id %in% alterados, c("cliente_id", "saldo")],
    by = "cliente_id", suffixes = c("_v1", "_v2")
  )
  comparacao$diferenca <- round(comparacao$saldo_v2 - comparacao$saldo_v1, 2)
  cat("\nTop 5 maiores variacoes de saldo:\n")
  print(head(comparacao[order(-abs(comparacao$diferenca)), ], 5), row.names = FALSE)

  write.csv(comparacao, "outputs/diff_v1_v2.csv", row.names = FALSE)
}

# --- manifest ----------------------------------------------------------------
manifesto <- lapply(list(v1 = v1, v2 = v2), function(df) {
  list(
    linhas = nrow(df),
    hash_arquivo = hash_registro("manifesto", paste(sort(df$registro_hash),
                                                    collapse = ""))
  )
})
json_linhas <- sprintf(
  '{"v1": {"linhas": %d, "hash": "%s"}, "v2": {"linhas": %d, "hash": "%s"}}',
  nrow(v1), manifesto$v1$hash_arquivo, nrow(v2), manifesto$v2$hash_arquivo
)
writeLines(json_linhas, "outputs/snapshots/manifest.json")

write.csv(v2, "outputs/snapshots/base_v2.csv", row.names = FALSE)
cat("\nSnapshots salvos em outputs/snapshots/ (manifest + base_v2)\n")
