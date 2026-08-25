# ANOVA de dois fatores: fertilizante x irrigacao na produtividade

dir.create("outputs", showWarnings = FALSE)
set.seed(640)

gerar_lavouras <- function(n_por_celula = 25) {
  fertilizantes <- c("Nenhum", "Organico", "Quimico")
  irrigacoes <- c("sequeiro", "irrigado")

  # efeito do fertilizante so aparece com irrigacao (interacao real)
  ganhos <- matrix(
    c(0.0, 0.0, 0.0,
      4.0, 9.0, 14.0),
    nrow = 2, byrow = TRUE,
    dimnames = list(irrigacoes, fertilizantes)
  )

  linhas <- list()
  for (fert in fertilizantes) {
    for (irrig in irrigacoes) {
      produtividade <- 32 + ganhos[irrig, fert] + rnorm(n_por_celula, 0, 3.5)
      linhas[[length(linhas) + 1]] <- data.frame(
        produtividade = round(produtividade, 1),
        fertilizante = fert,
        irrigacao = irrig
      )
    }
  }
  do.call(rbind, linhas)
}

lavouras <- gerar_lavouras()

cat("=== MEDIA POR CELULA (fertilizante x irrigacao) ===\n")
medias_celula <- tapply(lavouras$produtividade,
                        list(lavouras$fertilizante, lavouras$irrigacao), mean)
print(round(medias_celula, 1))

modelo <- aov(produtividade ~ fertilizante * irrigacao, data = lavouras)
tabela_anova <- summary(modelo)[[1]]

cat("\n=== TABELA ANOVA ===\n")
print(tabela_anova)

p_interacao <- tabela_anova$"Pr(>F)"[3]
cat(sprintf("\nInteracao fertilizante:irrigacao -> p = %.2e : %s\n",
            p_interacao,
            ifelse(p_interacao < 0.05,
                   "SIGNIFICATIVA - o efeito do fertilizante depende da agua",
                   "nao significativa")))

if (p_interacao < 0.05) {
  cat("\n=== TUKEY HSD (pares de fertilizante) ===\n")
  tukey <- TukeyHSD(modelo, which = "fertilizante")
  print(round(tukey$fertilizante, 2))
}

# --- grafico de interacao ----------------------------------------------------
png("outputs/anova_interacao.png", width = 850, height = 480, res = 110)
interaction.plot(
  x.factor = lavouras$fertilizante,
  trace.factor = lavouras$irrigacao,
  response = lavouras$produtividade,
  fun = mean, type = "b", pch = c(19, 17),
  col = c("#dc2626", "#2563eb"), lwd = 2.2,
  xlab = "fertilizante", ylab = "produtividade media (sacas/ha)",
  trace.label = "irrigacao",
  main = "Linhas nao paralelas indicam interacao"
)
dev.off()
cat("\nGrafico de interacao salvo em outputs/anova_interacao.png\n")
