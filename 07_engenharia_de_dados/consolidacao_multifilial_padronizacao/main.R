# Consolida as filiais: padroniza, valida, deduplica e agrega por semana

dir.create("outputs", showWarnings = FALSE)

UFS_VALIDAS <- c("SP", "RJ", "MG")

ler_filial <- function(caminho) {
  df <- read.csv(caminho, stringsAsFactors = FALSE)
  df$fonte_arquivo <- basename(caminho)
  df
}

arquivos <- list.files("fontes", pattern = "\\.csv$", full.names = TRUE)
stopifnot(length(arquivos) == 3)   # gate: sem as 3 fontes, para aqui

bruto <- do.call(rbind, lapply(arquivos, ler_filial))
cat(sprintf("Bruto: %d registros de %d arquivos\n", nrow(bruto), length(arquivos)))

# --- padronizacao ------------------------------------------------------------
limpo <- bruto
limpo$estado <- toupper(trimws(gsub("[.\\-]", "", limpo$estado)))
limpo$data_venda <- as.Date(limpo$data_venda)
limpo$valor <- as.numeric(limpo$valor)

# rejeita linhas com UF fora do padrao ou valores invalidos
validos <- limpo$estado %in% UFS_VALIDAS & !is.na(limpo$data_venda) &
  limpo$valor > 0 & !is.na(limpo$valor)
rejeitados <- sum(!validos)
consolidado <- limpo[validos, ]

cat(sprintf("Validos: %d | rejeitados na padronizacao: %d\n",
            nrow(consolidado), rejeitados))

# --- dedup por chave composta -------------------------------------------------
antes_dedup <- nrow(consolidado)
consolidado <- consolidado[!duplicated(consolidado[, c("pedido", "data_venda")]), ]
cat(sprintf("Dedup por (pedido, data): %d duplicatas removidas\n",
            antes_dedup - nrow(consolidado)))

# gates de qualidade antes de seguir
stopifnot(nrow(consolidado) > 1000)
stopifnot(all(consolidado$estado %in% UFS_VALIDAS))

# --- agregacao semanal --------------------------------------------------------
consolidado$semana <- format(consolidado$data_venda, "%G-W%V")
semanal <- aggregate(valor ~ semana + estado,
                     data = consolidado, FUN = function(v) round(sum(v), 2))

cat("\n=== RECEITA SEMANAL POR ESTADO (ultimas 6 semanas) ===\n")
pivot <- reshape(semanal, idvar = "semana", timevar = "estado", direction = "wide")
names(pivot) <- sub("valor_", "", names(pivot))
print(tail(pivot[order(pivot$semana), ], 6), row.names = FALSE)

write.csv(semanal, "outputs/vendas_semanais_consolidadas.csv", row.names = FALSE)
write.csv(consolidado, "outputs/consolidado_padronizado.csv", row.names = FALSE)
cat("\nCSVs salvos em outputs/\n")
