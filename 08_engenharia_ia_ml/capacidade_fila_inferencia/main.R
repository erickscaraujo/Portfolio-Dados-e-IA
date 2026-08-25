# Capacidade de inferencia: simulacao de fila M/M/1 x formula analitica

dir.create("outputs", showWarnings = FALSE)
set.seed(520)

TAXA_CHEGADA <- 80      # requisicoes por segundo
TAXA_SERVICO <- 100     # req/s por replica
N_REQUISICOES <- 20000

simular_fila <- function(lambda, mu, n = N_REQUISICOES) {
  chegadas <- cumsum(rexp(n, rate = lambda))
  servicos <- rexp(n, rate = mu)

  inicio_servico <- numeric(n)
  fim_servico <- numeric(n)

  for (i in seq_len(n)) {
    # servico so comeca quando o request chega E o servidor esta livre
    inicio_servico[i] <- max(chegadas[i], if (i == 1) 0 else fim_servico[i - 1])
    fim_servico[i] <- inicio_servico[i] + servicos[i]
  }

  esperas <- inicio_servico - chegadas
  list(espera_media = mean(esperas), p95 = quantile(esperas, 0.95))
}

espera_analitica <- function(lambda, mu) 1 / (mu - lambda)

cat("=== SIMULACAO X TEORIA (uma replica) ===\n")
resultado <- simular_fila(TAXA_CHEGADA, TAXA_SERVICO)
teoria <- espera_analitica(TAXA_CHEGADA, TAXA_SERVICO)

cat(sprintf("- espera media simulada: %.4f s\n", resultado$espera_media))
cat(sprintf("- formula W = 1/(mu-lam): %.4f s\n", teoria))
cat(sprintf("- p95 da espera         : %.4f s\n", resultado$p95))
rho <- TAXA_CHEGADA / TAXA_SERVICO
cat(sprintf("- utilizacao rho        : %.0f%%\n", rho * 100))

# --- varredura de utilizacao -------------------------------------------------
utilizacoes <- seq(0.5, 0.95, by = 0.05)
esperas_teoricas <- vapply(utilizacoes, function(u) {
  mu_fixa <- TAXA_SERVICO
  lambda_u <- u * mu_fixa
  espera_analitica(lambda_u, mu_fixa)
}, numeric(1))

cat("\n=== ESPERA TEORICA POR UTILIZACAO ===\n")
for (i in seq_along(utilizacoes)) {
  cat(sprintf("- rho=%.2f : %6.3f s%s\n",
              utilizacoes[i], esperas_teoricas[i],
              ifelse(utilizacoes[i] > 0.8, "   <- zona critica", "")))
}

# replicas necessarias para p95 < 200ms com folga
slo_p95_ms <- 200
replicas_necessarias <- ceiling(TAXA_CHEGADA / (TAXA_SERVICO * 0.75))
cat(sprintf("\nPara manter rho<=0.75 e p95<%dms: usar %d replicas.\n",
            slo_p95_ms, replicas_necessarias))

png("outputs/fila_inferencia.png", width = 900, height = 430, res = 110)
plot(utilizacoes, esperas_teoricas, type = "b", pch = 19, col = "#dc2626",
     xlab = "utilizacao (rho)", ylab = "espera media (s)",
     main = "Espera explode quando rho -> 1")
grid()
dev.off()
cat("Curva salva em outputs/fila_inferencia.png\n")
