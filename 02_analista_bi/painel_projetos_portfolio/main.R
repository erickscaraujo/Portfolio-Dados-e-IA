# Portfolio de projetos: conclusao, orcamento e semaforo de risco

dir.create("outputs", showWarnings = FALSE)
set.seed(620)

gerar_projetos <- function(n = 14) {
  data.frame(
    projeto = sprintf("PRJ-%02d", seq_len(n)),
    area = sample(c("Dados", "Infra", "Produto", "Marketing"), n, replace = TRUE),
    conclusao_pct = round(runif(n, 15, 98)),
    orcamento = round(runif(n, 80, 900) * 1000, 2),
    gasto = NA,
    dias_para_prazo = sample(-20:120, n, replace = TRUE)
  )
}

portfolio <- gerar_projetos()

# gasto acompanha a conclusao com desvios: uns estouram, outros economizam
portfolio$gasto <- round(
  portfolio$orcamento * (portfolio$conclusao_pct / 100) *
    runif(nrow(portfolio), 0.75, 1.45), 2
)

# --- indicadores -------------------------------------------------------------
portfolio$consumo_pct <- round(portfolio$gasto / portfolio$orcamento * 100, 1)
# defasagem: quanto o consumo correu a frente da entrega
portfolio$defasagem_pp <- portfolio$consumo_pct - portfolio$conclusao_pct

score_risco <- function(consumo_pct, defasagem_pp, dias_para_prazo) {
  risco_estouro <- pmax(0, consumo_pct - 100)
  risco_atraso <- ifelse(dias_para_prazo < 0 & defasagem_pp > -5,
                         abs(dias_para_prazo), 0)
  round(risco_estouro * 1.2 + pmax(0, defasagem_pp) * 0.8 + risco_atraso * 1.5, 1)
}

portfolio$risco_score <- score_risco(portfolio$consumo_pct,
                                     portfolio$defasagem_pp,
                                     portfolio$dias_para_prazo)

portfolio$semáforo <- cut(portfolio$risco_score,
                          breaks = c(-Inf, 10, 40, Inf),
                          labels = c("verde", "amarelo", "vermelho"))

cat("=== PORTFOLIO ORDENADO POR RISCO ===\n")
ordenado <- portfolio[order(-portfolio$risco_score),
                      c("projeto", "area", "conclusao_pct", "consumo_pct",
                        "defasagem_pp", "dias_para_prazo", "risco_score")]
print(ordenado, row.names = FALSE)

resumo_semaforo <- table(portfolio$semáforo)
cat("\n=== SEMAFORO ===\n")
for (cor in names(resumo_semaforo)) {
  cat(sprintf("- %-9s %d projeto(s)\n", cor, resumo_semaforo[cor]))
}

criticos <- portfolio[portfolio$semáforo == "vermelho", ]
if (nrow(criticos) > 0) {
  cat("\nAcao imediata nos vermelhos:\n")
  for (i in seq_len(nrow(criticos))) {
    linha <- criticos[i, ]
    motivo <- ifelse(linha$defasagem_pp > 15,
                     "gastou muito antes de entregar",
                     ifelse(linha$dias_para_prazo < 0,
                            "prazo vencido com entrega incompleta",
                            "desvio combinado custo/prazo"))
    cat(sprintf("- %s (%s): %s\n", linha$projeto, linha$area, motivo))
  }
}

# --- grafico -----------------------------------------------------------------
cores_semaforo <- c(verde = "#16a34a", amarelo = "#f59e0b", vermelho = "#dc2626")

png("outputs/portfolio_projetos.png", width = 950, height = 620, res = 110)
plot(portfolio$conclusao_pct, portfolio$consumo_pct,
     col = cores_semaforo[as.character(portfolio$semáforo)],
     pch = 19, cex = 1.4,
     xlab = "conclusao (%)", ylab = "consumo do orcamento (%)",
     main = "Portfolio de projetos — acima da diagonal = gastando demais")
abline(0, 1, lty = 2, col = "gray50")
text(portfolio$conclusao_pct, portfolio$consumo_pct + 3,
     labels = portfolio$projeto, cex = 0.62)
legend("topleft", legend = names(cores_semaforo),
       col = cores_semaforo, pch = 19, bty = "n")
grid()
dev.off()

write.csv(portfolio, "outputs/portfolio_riscos.csv", row.names = FALSE)
cat("\nCSV e grafico salvos em outputs/\n")
