# Regressao multipla de salarios com diagnostico completo

dir.create("outputs", showWarnings = FALSE)
set.seed(450)

gerar_profissionais <- function(n = 800) {
  experiencia <- pmin(runif(n, 0, 25), 25)
  educacao <- sample(c("medio", "superior", "mestrado"), n,
                     replace = TRUE, prob = c(0.35, 0.5, 0.15))
  cargo_lideranca <- sample(c(FALSE, TRUE), n, replace = TRUE, prob = c(0.75, 0.25))

  bonus_educacao <- c(medio = 0, superior = 900, mestrado = 1900)[educacao]
  salario <- 3200 + 310 * experiencia + bonus_educacao +
    ifelse(cargo_lideranca, 2600, 0) + rnorm(n, 0, 850)

  data.frame(
    salario = round(salario, 2),
    experiencia = round(experiencia, 1),
    educacao = educacao,
    lideranca = cargo_lideranca
  )
}

profissionais <- gerar_profissionais()

# --- modelo ------------------------------------------------------------------
modelo1 <- lm(salario ~ experiencia, data = profissionais)
modelo2 <- lm(salario ~ experiencia + educacao + lideranca, data = profissionais)

cat("=== MODELO 1: so experiencia ===\n")
cat(sprintf("R2 ajustado: %.3f\n", summary(modelo1)$adj.r.squared))

cat("\n=== MODELO 2: completo (summary) ===\n")
print(summary(modelo2))

comparacao <- anova(modelo1, modelo2)
cat(sprintf("\nANOVA modelos aninhados: F=%.1f | p=%.2e -> %s\n",
            comparacao$F[2], comparacao$"Pr(>F)"[2],
            "adicionar as variaveis melhora o ajuste"))

# --- interpretacao -----------------------------------------------------------
coeficientes <- coef(modelo2)
cat("\n=== LEITURA DOS COEFICIENTES ===\n")
cat(sprintf("- cada ano de experiencia: +R$ %.0f no salario\n", coeficientes["experiencia"]))
cat(sprintf("- superior vs medio     : +R$ %.0f\n",
            coeficientes["educacaosuperior"]))
cat(sprintf("- mestrado vs medio     : +R$ %.0f\n",
            coeficientes["educacaomestrado"]))
cat(sprintf("- lideranca             : +R$ %.0f\n", coeficientes["liderancaTRUE"]))

# --- diagnostico visual ------------------------------------------------------
png("outputs/regressao_diagnostico.png", width = 1000, height = 1000, res = 110)
par(mfrow = c(2, 2), mar = c(4.5, 4.5, 3, 1))
plot(modelo2, which = c(1, 2, 3, 4), pch = 16, cex = 0.6)
dev.off()

# checagem rapida de heterocedasticidade: correlacao |residuo| x ajustado
residuos_abs <- abs(residuals(modelo2))
correlacao_hetero <- cor(fitted(modelo2), residuos_abs)
cat(sprintf("\nCorrelacao fitted x |residuos|: %.3f (perto de 0 sugere variancia estavel)\n",
            correlacao_hetero))

cat("Graficos de diagnóstico salvos em outputs/regressao_diagnostico.png\n")
