# PCA via eigen(): variancia explicada, loadings e reconstrucao

dir.create("outputs", showWarnings = FALSE)
set.seed(700)

gerar_base_correlacionada <- function(n = 900) {
  fator_tamanho <- rnorm(n)          # latente 1: tamanho da conta
  fator_engajamento <- rnorm(n)      # latente 2: engajamento

  data.frame(
    renda = round(5000 + 1800 * fator_tamanho + rnorm(n, 0, 400), 2),
    gastos = round(3200 + 1400 * fator_tamanho + rnorm(n, 0, 350), 2),
    logins_mes = pmax(0, round(8 + 5 * fator_engajamento + rnorm(n, 0, 2))),
    cliques_email = pmax(0, round(4 + 3 * fator_engajamento + rnorm(n, 0, 1.6))),
    tickets_suporte = pmax(0, round(1.5 - 0.8 * fator_engajamento + rnorm(n, 0, 1)))
  )
}

base <- gerar_base_correlacionada()
matriz_centralizada <- scale(as.matrix(base), center = TRUE, scale = FALSE)

# --- PCA manual ---------------------------------------------------------------
covariancia <- cov(matriz_centralizada)
decomposicao <- eigen(covariancia)

variancias <- decomposicao$values
componentes <- decomposicao$vectors

variancia_total <- sum(variancias)
variancia_explicada <- cumsum(variancias) / variancia_total

cat("=== VARIANCIA EXPLICADA ACUMULADA ===\n")
for (i in seq_along(variancias)) {
  cat(sprintf("- PC%d: %.1f%% (acumulado %.1f%%)\n",
              i, variancias[i] / variancia_total * 100,
              variancia_explicada[i] * 100))
}

componentes_necessarios <- which(variancia_explicada >= 0.9)[1]
cat(sprintf("\nComponentes para explicar 90%%: %d\n", componentes_necessarios))

loadings_pc1 <- componentes[, 1]
nomes_ordenados <- names(base)[order(abs(loadings_pc1), decreasing = TRUE)]
cat(sprintf("\nPC1 e dominado por: %s (loading %.2f)\n",
            nomes_ordenados[1], loadings_pc1[which.max(abs(loadings_pc1))]))

# --- scores e reconstrucao ----------------------------------------------------
scores <- matriz_centralizada %*% componentes

reconstruir_com_k <- function(k) {
  aproximacao_scores <- scores[, seq_len(k), drop = FALSE]
  aproximacao_scores %*% t(componentes[, seq_len(k), drop = FALSE])
}

cat("\n=== ERRO DE RECONSTRUCAO (RMSE) ===\n")
for (k in c(1, 2, 3, 5)) {
  rmse <- sqrt(mean((matriz_centralizada - reconstruir_com_k(k))^2))
  cat(sprintf("- %d componente(s): RMSE %.1f\n", k, rmse))
}

# --- graficos -----------------------------------------------------------------
png("outputs/pca_eigen.png", width = 1100, height = 450, res = 110)
par(mfrow = c(1, 2), mar = c(4.5, 4.2, 3, 1))

plot(seq_along(variancias), variancia_explicada * 100,
     type = "b", pch = 19, col = "#7c3aed",
     xlab = "componente", ylab = "variancia acumulada (%)",
     main = "Scree plot — variancia acumulada")
abline(h = 90, lty = 2, col = "gray40")

plot(scores[, 1], scores[, 2], pch = 19, cex = 0.55,
     col = rgb(37, 99, 235, 45, maxColorValue = 255),
     xlab = sprintf("PC1 (%.0f%%)", variancias[1] / variancia_total * 100),
     ylab = sprintf("PC2 (%.0f%%)", variancias[2] / variancia_total * 100),
     main = "Projeção nos 2 primeiros componentes")
grid()

dev.off()
cat("\nPainel salvo em outputs/pca_eigen.png\n")
