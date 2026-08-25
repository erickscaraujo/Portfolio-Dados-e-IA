# Threshold otimizado pelo custo do negocio, nao pelo default 0.5

dir.create("outputs", showWarnings = FALSE)
set.seed(690)

CUSTO_FALSO_NEGATIVO <- 500   # fraude que passou
CUSTO_FALSO_POSITIVO <- 50    # transacao boa bloqueada

gerar_transacoes <- function(n = 8000) {
  valor_log <- rnorm(n, 5.5, 1.1)
  hora_fora_pico <- runif(n) < 0.25
  cliente_novo <- runif(n) < 0.2

  logit <- -4.6 + 0.9 * valor_log + 1.6 * hora_fora_pico + 1.1 * cliente_novo
  fraudulenta <- runif(n) < 1 / (1 + exp(-logit))

  data.frame(
    log_valor = round(valor_log, 3),
    hora_fora_pico = as.integer(hora_fora_pico),
    cliente_novo = as.integer(cliente_novo),
    fraudulenta = as.integer(fraudulenta)
  )
}

transacoes <- gerar_transacoes()
corte <- floor(0.7 * nrow(transacoes))
treino <- transacoes[seq_len(corte), ]
teste <- transacoes[(corte + 1):nrow(transacoes), ]

modelo <- glm(fraudulenta ~ ., data = treino, family = binomial)
teste$probabilidade <- predict(modelo, teste, type = "response")

cat("Fraudes no holdout:", sum(teste$fraudulenta),
    sprintf("(%.1f%%)\n", mean(teste$fraudulenta) * 100))

# --- varredura de threshold ---------------------------------------------------
grade_thresholds <- seq(0.05, 0.95, by = 0.05)

avaliar_threshold <- function(threshold) {
  alertas <- teste$probabilidade >= threshold
  falsos_negativos <- sum(teste$fraudulenta == 1 & !alertas)
  falsos_positivos <- sum(teste$fraudulenta == 0 & alertas)

  custo_total <- falsos_negativos * CUSTO_FALSO_NEGATIVO +
    falsos_positivos * CUSTO_FALSO_POSITIVO

  data.frame(
    threshold = threshold,
    falsos_negativos = falsos_negativos,
    falsos_positivos = falsos_positivos,
    custo_total_usd = custo_total
  )
}

varredura <- do.call(rbind, lapply(grade_thresholds, avaliar_threshold))

otimo <- varredura[which.min(varredura$custo_total_usd), ]
padrao <- varredura[abs(varredura$threshold - 0.5) < 0.001, ]

cat("\n=== CUSTO TOTAL POR THRESHOLD ===\n")
print(transform(varredura, custo_total_usd = format(custo_total_usd, big.mark = ".")),
      row.names = FALSE)

economia <- padrao$custo_total_usd - otimo$custo_total_usd
cat(sprintf("\nThreshold otimo: %.2f | custo USD %s\n",
            otimo$threshold, format(otimo$custo_total_usd, big.mark = ".")))
cat(sprintf("Economia vs o default 0.50: USD %s (%.0f%% menos custo)\n",
            format(economia, big.mark = "."),
            economia / padrao$custo_total_usd * 100))

# --- grafico ------------------------------------------------------------------
png("outputs/threshold_custo.png", width = 900, height = 450, res = 110)
plot(varredura$threshold, varredura$custo_total_usd,
     type = "b", pch = 19, col = "#2563eb", cex = 0.7,
     xlab = "threshold de decisao", ylab = "custo total (USD)",
     main = sprintf("Custo minimo no threshold %.2f", otimo$threshold))
abline(v = otimo$threshold, lty = 2, col = "#dc2626")
abline(v = 0.5, lty = 3, col = "gray40")
legend("topright", legend = c("otimo", "default 0.5"),
       lty = c(2, 3), col = c("#dc2626", "gray40"), bty = "n")
grid()
dev.off()
cat("Curva salva em outputs/threshold_custo.png\n")
