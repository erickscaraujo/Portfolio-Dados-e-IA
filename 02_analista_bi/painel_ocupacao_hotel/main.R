# Hotel: ocupacao, ADR, RevPAR e cancelamentos por canal

dir.create("outputs", showWarnings = FALSE)
set.seed(430)

QUARTOS <- 120
MESES <- 18
CANAIS <- c("direto", "OTA", "corporativo")

gerar_ocupacao <- function() {
  periodo <- seq(as.Date("2024-01-01"), by = "month", length.out = MESES)
  mes_num <- as.integer(format(periodo, "%m"))

  # alta temporada dez-fev e julho; baixa em fev/mar pos ferias
  fator_ocupacao <- c(0.92, 0.88, 0.62, 0.58, 0.66, 0.72,
                      0.90, 0.74, 0.70, 0.76, 0.80, 0.95)[mes_num]

  data.frame(
    mes = format(periodo, "%Y-%m"),
    ocupacao = pmin(0.98, fator_ocupacao * rnorm(MESES, 1, 0.04)),
    adr = round(pmax(180, (260 + 90 * (fator_ocupacao - 0.6)) * rnorm(MESES, 1, 0.05)), 2),
    cancelamento_pct = round(rnorm(MESES, 11, 2.5), 1),
    canal = sample(CANAIS, MESES, replace = TRUE, prob = c(0.35, 0.45, 0.20))
  )
}

hotel <- gerar_ocupacao()
hotel$revpar <- round(hotel$ocupacao * hotel$adr, 2)

cat("=== OCUPACAO / ADR / REVPAR POR MES ===\n")
print(hotel[, c("mes", "ocupacao", "adr", "revpar", "cancelamento_pct")], row.names = FALSE)

melhor_mes <- hotel[which.max(hotel$revpar), ]
media_revpar <- mean(hotel$revpar)
cat(sprintf("\nMelhor mes: %s (RevPAR R$ %.2f) | media do periodo: R$ %.2f\n",
            melhor_mes$mes, melhor_mes$revpar, media_revpar))

# --- cancelamentos por canal -------------------------------------------------
cancel_canal <- aggregate(cancelamento_pct ~ canal, data = hotel, FUN = mean)
cancel_canal$cancelamento_pct <- round(cancel_canal$cancelamento_pct, 1)
cancel_canal <- cancel_canal[order(-cancel_canal$cancelamento_pct), ]

cat("\n=== CANCELAMENTO MEDIO POR CANAL (%) ===\n")
print(cancel_canal, row.names = FALSE)

pior_canal <- cancel_canal[1, ]
cat(sprintf("Canal '%s' cancela mais; negociar penalidade ou pre-pagamento.\n",
            pior_canal$canal))

# --- resumo por canal (receita aproximada) -----------------------------------
hotel$receita_estimada <- QUARTOS * 30 * hotel$ocupacao * hotel$adr * (1 - hotel$cancelamento_pct / 100)
receita_canal <- tapply(hotel$receita_estimada, hotel$canal, sum)
cat("\n=== RECEITA ESTIMADA POR CANAL (R$ mil) ===\n")
print(round(receita_canal / 1000, 1))

# --- grafico -----------------------------------------------------------------
png("outputs/hotel_ocupacao.png", width = 1150, height = 460, res = 110)
par(mfrow = c(1, 2), mar = c(5, 4.2, 3, 1))

plot(hotel$ocupacao, type = "b", col = "#2563eb", pch = 19,
     xlab = "", ylab = "ocupacao", xaxt = "n",
     main = paste("Ocupacao mensal |", QUARTOS, "quartos"))
axis(1, at = seq_len(MESES), labels = substr(hotel$mes, 1, 7), las = 2, cex.axis = 0.65)

barplot(t(cbind(adr = hotel$adr, revpar = hotel$revpar)),
        beside = TRUE, col = c("#94a3b8", "#059669"), border = NA,
        names.arg = substr(hotel$mes, 1, 7), las = 2, cex.names = 0.6,
        main = "ADR x RevPAR (R$)", legend.text = c("ADR", "RevPAR"),
        args.legend = list(x = "topleft", bty = "n", cex = 0.8))

dev.off()

write.csv(hotel, "outputs/hotel_resumo.csv", row.names = FALSE)
cat("\nPainel e CSV salvos em outputs/\n")
