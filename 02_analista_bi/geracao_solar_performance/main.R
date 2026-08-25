# Geracao solar fotovoltaica: performance ratio e impacto de nuvens

dir.create("outputs", showWarnings = FALSE)
set.seed(630)

CAPACIDADE_KWP <- 8.5
TARIFA_KWH <- 0.85

gerar_dias <- function(dias = 120) {
  datas <- seq(as.Date("2024-09-01"), by = "day", length.out = dias)

  # verao (dez-fev) tem mais irradiacao no hemisferio sul
  irradiacao_base <- 4.6 + 1.1 * cos(2 * pi * (as.integer(format(datas, "%m")) - 12) / 12)
  nublado <- runif(dias) < 0.28

  data.frame(
    data = datas,
    irradiacao_h = round(pmax(0.4, irradiacao_base * ifelse(nublado, 0.45, 1) *
                                rnorm(dias, 1, 0.08)), 2),
    nublado = nublado
  )
}

dias_solares <- gerar_dias()

# geracao esperada = irradiacao x capacidade x eficiencia do sistema (~0.78)
dias_solares$geracao_kwh <- round(
  dias_solares$irradiacao_h * CAPACIDADE_KWP * 0.78 * rnorm(nrow(dias_solares), 1, 0.05),
  1
)
dias_solares$performance_ratio <- round(
  dias_solares$geracao_kwh / (dias_solares$irradiacao_h * CAPACIDADE_KWP), 3
)
dias_solares$economia_rs <- round(dias_solares$geracao_kwh * TARIFA_KWH, 2)

# --- resumo ------------------------------------------------------------------
cat("=== RESUMO DO PERIODO ===\n")
cat(sprintf("- geracao total      : %.0f kWh\n", sum(dias_solares$geracao_kwh)))
cat(sprintf("- economia acumulada : R$ %s\n",
            format(round(sum(dias_solares$economia_rs)), big.mark = ".")))

pr_medio <- mean(dias_solares$performance_ratio)
cat(sprintf("- performance ratio medio: %.1f%% (referencia saudavel: >75%%)\n",
            pr_medio * 100))

if (pr_medio < 0.75) {
  cat("ATENCAO: PR abaixo da referencia — vale inspecionar sujeira nos paineis ou sombreamento.\n")
}

cat("\n=== DIAS NUBLADOS X LIMPOS ===\n")
pr_por_condicao <- tapply(dias_solares$performance_ratio,
                          dias_solares$nublado, mean)
names(pr_por_condicao) <- c("limpo", "nublado")
print(round(pr_por_condicao, 3))
queda_nublado <- 1 - pr_por_condicao["nublado"] / pr_por_condicao["limpo"]
cat(sprintf("Queda de performance em dia nublado: %.0f%%\n", queda_nublado * 100))

pior_dia <- dias_solares[which.min(dias_solares$performance_ratio), ]
cat(sprintf("\nPior dia: %s (PR %.0f%%, irradiacao de apenas %.1f h)\n",
            pior_dia$data, pior_dia$performance_ratio * 100,
            pior_dia$irradiacao_h))

# --- grafico -----------------------------------------------------------------
png("outputs/solar_geracao.png", width = 1100, height = 450, res = 110)
par(mfrow = c(1, 2), mar = c(4.5, 4.2, 3, 1))

plot(dias_solares$data, dias_solares$geracao_kwh,
     type = "h", col = ifelse(dias_solares$nublado, "#94a3b8", "#f59e0b"),
     xlab = "", ylab = "kWh", main = "Geracao diaria (laranja = limpo)")
abline(h = mean(dias_solares$geracao_kwh), lty = 2)

boxplot(performance_ratio ~ nublado, data = dias_solares,
        names = c("dia limpo", "dia nublado"), col = c("#f59e0b", "#94a3b8"),
        main = "Performance ratio por condicao", ylab = "PR")

dev.off()
cat("Painel salvo em outputs/solar_geracao.png\n")
