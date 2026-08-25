# Antes x depois do mesmo grupo: t pareado, Wilcoxon e Cohen's d

dir.create("outputs", showWarnings = FALSE)
set.seed(460)

gerar_scores <- function(n = 90) {
  # score 0-100; treinamento ajuda mais quem partiu de baixo (efeito regressao realista)
  antes <- pmin(95, pmax(20, rnorm(n, 55, 14)))
  ganho <- rnorm(n, 7, 6) + pmax(0, 60 - antes) * 0.15
  depois <- pmin(100, pmax(0, antes + ganho))

  data.frame(funcionario = sprintf("F%03d", seq_len(n)),
             antes = round(antes, 1),
             depois = round(depois, 1))
}

scores <- gerar_scores()
scores$diferenca <- scores$depois - scores$antes

cat("=== RESUMO ===\n")
cat(sprintf("- media antes : %.1f\n- media depois: %.1f\n- ganho medio : %.1f\n",
            mean(scores$antes), mean(scores$depois), mean(scores$diferenca)))

# --- normalidade das diferencas ---------------------------------------------
shapiro_teste <- shapiro.test(scores$diferenca)
cat(sprintf("\nShapiro nas diferencas: W=%.3f | p=%.4f -> %s\n",
            shapiro_teste$statistic, shapiro_teste$p.value,
            ifelse(shapiro_teste$p.value > 0.05,
                   "diferenças ~normais", "desvio da normalidade")))

# --- testes -----------------------------------------------------------------
t_teste <- t.test(scores$depois, scores$antes, paired = TRUE)
wilcox_teste <- wilcox.test(scores$depois, scores$antes, paired = TRUE)

cat("\n=== T PAREADO ===\n")
print(t_teste)

cat("\n=== WILCOXON PAREADO (nao-parametrico de apoio) ===\n")
cat(sprintf("V=%.0f | p=%.4g\n", wilcox_teste$statistic, wilcox_teste$p.value))

# --- tamanho do efeito: Cohen's d pareado -----------------------------------
d_cohen <- mean(scores$diferenca) / sd(scores$diferenca)
rotulo_d <- ifelse(abs(d_cohen) < 0.5, "pequeno",
                   ifelse(abs(d_cohen) < 0.8, "medio", "grande"))

# IC 95% do ganho medio via bootstrap
set.seed(461)
boot_medias <- replicate(5000, {
  amostra <- sample(scores$diferenca, nrow(scores), replace = TRUE)
  mean(amostra)
})
ic <- quantile(boot_medias, c(0.025, 0.975))

cat("\n=== TAMANHO DO EFEITO ===\n")
cat(sprintf("Cohen's d = %.2f (%s)\n", d_cohen, rotulo_d))
cat(sprintf("IC 95%% bootstrap do ganho medio: [%.1f, %.1f]\n", ic[1], ic[2]))

# --- veredito ---------------------------------------------------------------
if (t_teste$p.value < 0.05 && ic[1] > 0) {
  veredito <- sprintf("TREINAMENTO EFETIVO: ganho de %.1f pontos com IC inteiramente positivo.",
                      mean(scores$diferenca))
} else if (t_teste$p.value >= 0.05) {
  veredito <- "SEM EVIDENCIA de melhora atribuivel ao treinamento."
} else {
  veredito <- "Resultado misto: significativo, mas o IC cruza o zero. Coletar mais dados."
}
cat(sprintf("\nVEREDICTO: %s\n", veredito))

# --- grafico ----------------------------------------------------------------
png("outputs/treinamento_pareado.png", width = 900, height = 440, res = 110)
par(mfrow = c(1, 2), mar = c(4.5, 4.2, 3, 1))

boxplot(scores$antes, scores$depois, names = c("antes", "depois"),
        col = c("#94a3b8", "#16a34a"), border = "#334155",
        main = "Scores antes x depois", ylab = "score")

hist(scores$diferenca, breaks = 18, col = "#2563eb", border = "white",
     main = "Distribuição das diferenças", xlab = "depois - antes")
abline(v = mean(scores$diferenca), lwd = 2.5)
abline(v = 0, lty = 2)

dev.off()
cat("Gráfico salvo em outputs/treinamento_pareado.png\n")
