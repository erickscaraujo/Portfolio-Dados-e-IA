# Emprestimos da biblioteca: sazonalidade, generos e atrasos de devolucao

dir.create("outputs", showWarnings = FALSE)
set.seed(410)

GENEROS <- c("Romance", "Tecnico", "Ficcao", "Infantil", "Historia")
TEMPO_POSSE <- c(Romance = 9, Tecnico = 16, Ficcao = 8, Infantil = 6, Historia = 12)

gerar_emprestimos <- function(n = 2400) {
  mes <- sample(1:12, n, replace = TRUE, prob = c(
    0.11, 0.09, 0.10, 0.08, 0.07, 0.06,
    0.05, 0.05, 0.08, 0.09, 0.10, 0.12
  ))
  genero <- sample(GENEROS, n, replace = TRUE, prob = c(0.26, 0.18, 0.24, 0.20, 0.12))

  data.frame(
    mes = mes,
    genero = genero,
    dias_posse = pmax(1, rpois(n, TEMPO_POSSE[genero])),
    devolvido_no_prazo = runif(n) < 0.78
  )
}

emprestimos <- gerar_emprestimos()

# --- visao mensal -----------------------------------------------------------
tabela_mensal <- table(emprestimos$mes)
mensal <- data.frame(
  mes = as.integer(names(tabela_mensal)),
  emprestimos = as.integer(tabela_mensal)
)
rotulos_mes <- month.name
mensal$rotulo <- rotulos_mes[mensal$mes]

cat("=== EMPRESTIMOS POR MES ===\n")
print(mensal[, c("rotulo", "emprestimos")])

pico <- mensal[which.max(mensal$emprestimos), ]
vale <- mensal[which.min(mensal$emprestimos), ]
cat(sprintf("\nPicou em %s (%d) e secou em %s (%d)\n",
            pico$rotulo, pico$emprestimos, vale$rotulo, vale$emprestimos))

# --- generos ----------------------------------------------------------------
total_por_genero <- table(emprestimos$genero)
dias_por_genero <- tapply(emprestimos$dias_posse, emprestimos$genero, mean)

cat("\n=== GENEROS ===\n")
resumo_genero <- data.frame(
  genero = names(total_por_genero),
  total = as.integer(total_por_genero),
  dias_medios = round(as.numeric(dias_por_genero), 1)
)
resumo_genero <- resumo_genero[order(-resumo_genero$total), ]
print(resumo_genero, row.names = FALSE)

# --- atrasos ----------------------------------------------------------------
atrasados <- emprestimos[!emprestimos$devolvido_no_prazo, ]
taxa_atraso <- nrow(atrasados) / nrow(emprestimos)
piores_genero <- prop.table(table(atrasados$genero)) * 100

cat("\n=== ATRASOS ===\n")
cat(sprintf("Taxa de atraso geral: %.1f%%\n", taxa_atraso * 100))
cat("Distribuicao dos atrasos por genero (%):\n")
print(round(as.table(piores_genero), 1))

# --- grafico ----------------------------------------------------------------
png("outputs/biblioteca_emprestimos.png", width = 1100, height = 440, res = 110)
par(mfrow = c(1, 2))

barplot(mensal$emprestimos, names.arg = substr(mensal$rotulo, 1, 3),
        col = "#2563eb", border = NA,
        main = "Emprestimos por mes", ylab = "quantidade")

barplot(resumo_genero$total, names.arg = resumo_genero$genero,
        col = "#7c3aed", border = NA, horiz = TRUE, las = 1,
        main = "Top generos", xlab = "emprestimos no ano")

dev.off()
cat("\nPainel salvo em outputs/biblioteca_emprestimos.png\n")
