# SLO 99.9%: error budget semanal e burn rate acumulado

dir.create("outputs", showWarnings = FALSE)
set.seed(760)

SLO_DISPONIBILIDADE <- 0.999
MINUTOS_POR_SEMANA <- 7 * 24 * 60

gerar_semanas <- function(semanas = 16) {
  # incidentes com duração pesada: maioria pequena, alguns grandes
  n_incidentes <- rpois(semanas, lambda = 0.8)
  downtime_min <- mapply(function(k) {
    if (k == 0) {
      return(0)
    }
    sum(rexp(k, rate = 1 / 25))
  }, n_incidentes)

  data.frame(
    semana = sprintf("S%02d", seq_len(semanas)),
    incidentes = n_incidentes,
    downtime_min = round(pmin(downtime_min, MINUTOS_POR_SEMANA * (1 - SLO_DISPONIBILIDADE) * 3), 1)
  )
}

semanas <- gerar_semanas()
semanas$minutos_no_mes <- MINUTOS_POR_SEMANA
semanas$error_budget_min <- MINUTOS_POR_SEMANA * (1 - SLO_DISPONIBILIDADE)
semanas$disponibilidade_pct <- round(
  (MINUTOS_POR_SEMANA - semanas$downtime_min) / MINUTOS_POR_SEMANA * 100, 3
)
# burn rate da semana: quanto do orcamento semanal foi queimado
semanas$burn_rate <- round(semanas$downtime_min / semanas$error_budget_min, 2)
semanas$burn_acumulado_pct <- round(cumsum(semanas$downtime_min) /
                                      cumsum(semanas$error_budget_min) * 100, 1)

cat("=== DISPONIBILIDADE E ERROR BUDGET POR SEMANA ===\n")
print(semanas[, c("semana", "incidentes", "downtime_min", "disponibilidade_pct",
                  "burn_rate", "burn_acumulado_pct")], row.names = FALSE)

semanas_sla_ok <- sum(semanas$disponibilidade_pct >= SLO_DISPONIBILIDADE * 100)
cat(sprintf("\nSemanas dentro do SLO (%.1f%%): %d de %d\n",
            SLO_DISPONIBILIDADE * 100, semanas_sla_ok, nrow(semanas)))

estourou_idx <- which(semanas$burn_acumulado_pct > 100)[1]
if (!is.na(estourou_idx)) {
  cat(sprintf("\nORCAMENTO DE ERRO EXAURIDO na semana %s!\n",
              semanas$semana[estourou_idx]))
  cat("Politica sugerida: congelar deploys de features e priorizar confiabilidade.\n")
} else {
  restante <- 100 - max(semanas$burn_acumulado_pct)
  cat(sprintf("\nOrcamento restante no fim do trimestre: %.1f%%\n", restante))
}

png("outputs/slo_error_budget.png", width = 1100, height = 450, res = 110)
par(mfrow = c(1, 2), mar = c(4.5, 4.2, 3, 1))

barplot(semanas$disponibilidade_pct, names.arg = semanas$semana,
        col = ifelse(semanas$disponibilidade_pct >= SLO_DISPONIBILIDADE * 100,
                     "#16a34a", "#dc2626"), border = NA,
        ylim = c(99.5, 100), las = 2, cex.names = 0.65,
        main = "Disponibilidade semanal (%)")

plot(seq_len(nrow(semanas)), semanas$burn_acumulado_pct,
     type = "b", pch = 19, col = "#dc2626",
     xlab = "semana", ylab = "error budget consumido (%)",
     main = "Burn rate acumulado do trimestre")
abline(h = 100, lty = 2, col = "gray40")

dev.off()
cat("\nPainel salvo em outputs/slo_error_budget.png\n")
