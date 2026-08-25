# Regressao polinomial: o ponto exato do overfitting

dir.create("outputs", showWarnings = FALSE)
set.seed(650)

f_verdadeira <- function(x) 60 + 28 * sin(0.22 * x) - 0.15 * x

gerar_amostra <- function(n, seed) {
  set.seed(seed)
  x <- runif(n, 0, 100)
  data.frame(x = x, y = f_verdadeira(x) + rnorm(n, 0, 7))
}

treino <- gerar_amostra(30, 660)
teste <- gerar_amostra(200, 661)   # teste limpo e maior: mede generalizacao real

graus <- 1:11
rmse_treino <- numeric(length(graus))
rmse_teste <- numeric(length(graus))
modelos <- list()

for (i in seq_along(graus)) {
  grau <- graus[i]
  modelo <- lm(y ~ poly(x, grau, raw = TRUE), data = treino)
  modelos[[i]] <- modelo

  rmse_treino[i] <- sqrt(mean((predict(modelo, treino) - treino$y)^2))
  rmse_teste[i] <- sqrt(mean((predict(modelo, teste) - teste$y)^2))
}

cat("=== RMSE POR GRAU DO POLINOMIO ===\n")
tabela_graus <- data.frame(
  grau = graus,
  rmse_treino = round(rmse_treino, 2),
  rmse_teste = round(rmse_teste, 2),
  gap = round(rmse_teste - rmse_treino, 2)
)
print(tabela_graus, row.names = FALSE)

melhor_grau <- graus[which.min(rmse_teste)]
cat(sprintf("\nMelhor grau pelo RMSE de teste: %d (%.2f)\n",
            melhor_grau, min(rmse_teste)))
cat(sprintf("Grau 9 em diante: treino quase perfeito (%.3f) mas teste explode (%.1f) - overfitting classico\n",
            rmse_treino[9], rmse_teste[9]))

# --- grafico -----------------------------------------------------------------
grade_x <- seq(0, 100, length.out = 300)

cores_graus <- c("1" = "#94a3b8", "3" = "#059669", "9" = "#dc2626")

png("outputs/polinomial_overfitting.png", width = 1100, height = 470, res = 110)
par(mfrow = c(1, 2), mar = c(4.5, 4.2, 3, 1))

plot(graus, rmse_treino, type = "b", pch = 19, col = "#2563eb", ylim = range(c(rmse_treino, rmse_teste)),
     xlab = "grau do polinomio", ylab = "RMSE", main = "Treino cai sempre; teste tem fundo do poco")
lines(graus, rmse_teste, type = "b", pch = 17, col = "#dc2626")
abline(v = melhor_grau, lty = 2, col = "gray40")
legend("topright", legend = c("treino", "teste"), col = c("#2563eb", "#dc2626"),
       pch = c(19, 17), bty = "n")

plot(treino$x, treino$y, pch = 19, cex = 0.8, col = "#334155",
     xlab = "x", ylab = "y",
     main = sprintf("Ajustes: graus 1, 3 (otimo=%d) e 9", melhor_grau))
curva_y <- function(modelo) predict(modelo, data.frame(x = grade_x))
for (grau in c(1, 3, 9)) {
  indice <- which(graus == grau)
  lines(grade_x, curva_y(modelos[[indice]]), col = cores_graus[as.character(grau)], lwd = 2)
}
curve(f_verdadeira, add = TRUE, lty = 3, lwd = 1.5)
legend("bottomleft", legend = paste("grau", c(1, 3, 9)),
       col = cores_graus[c("1", "3", "9")], lwd = 2, bty = "n")

dev.off()
cat("\nGraficos salvos em outputs/polinomial_overfitting.png\n")
