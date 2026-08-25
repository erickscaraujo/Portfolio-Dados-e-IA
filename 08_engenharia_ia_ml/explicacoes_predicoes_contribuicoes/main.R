# Explicacoes por predicao: contribuicao linear de cada feature

dir.create("outputs", showWarnings = FALSE)
set.seed(750)

FEATURES <- c("renda", "divida_renda", "atrasos_12m", "score_interno")

gerar_treino <- function(n = 8000) {
  base <- data.frame(
    renda = round(rlnorm(n, 8.3, 0.45), 2),
    divida_renda = round(rbeta(n, 2, 6), 3),
    atrasos_12m = rpois(n, 0.9),
    score_interno = sample(300:900, n, replace = TRUE)
  )
  logit <- -1.9 + 5.4 * base$divida_renda + 0.4 * base$atrasos_12m -
    0.00032 * base$renda - 0.003 * (base$score_interno - 500) + rnorm(n, 0, 0.8)
  base$inadimpliu <- rbinom(n, 1, 1 / (1 + exp(-logit)))
  base
}

treino_base <- gerar_treino()
modelo <- glm(inadimpliu ~ ., data = treino_base, family = binomial)

medias_features <- colMeans(treino_base[FEATURES])
coeficientes <- coef(modelo)[FEATURES]

# --- scoring de um lote novo com explicacoes ----------------------------------
gerar_lote_novo <- function(n = 200) {
  data.frame(
    cliente_id = sprintf("N%04d", seq_len(n)),
    renda = round(rlnorm(n, 8.3, 0.5), 2),
    divida_renda = round(rbeta(n, 2, 5), 3),
    atrasos_12m = rpois(n, 1.1),
    score_interno = sample(320:880, n, replace = TRUE)
  )
}

lote <- gerar_lote_novo()
lote$probabilidade <- predict(modelo, lote, type = "response")

contribuicoes <- t(vapply(seq_len(nrow(lote)), function(i) {
  vapply(FEATURES, function(f) {
    coeficientes[[f]] * (lote[[f]][i] - medias_features[[f]])
  }, numeric(1))
}, numeric(length(FEATURES))))
colnames(contribuicoes) <- FEATURES

lote$driver_positivo <- apply(contribuicoes, 1, function(linha) {
  FEATURES[[which.max(linha)]]
})
lote$driver_negativo <- apply(contribuicoes, 1, function(linha) {
  FEATURES[[which.min(linha)]]
})

cat("=== EXEMPLOS EXPLICADOS ===\n")
for (i in c(3, 17, 88)) {
  cat(sprintf("- %s: probabilidade %.0f%%\n",
              lote$cliente_id[i], lote$probabilidade[i] * 100))
  cat(sprintf("    puxa o risco para cima : %s\n", lote$driver_positivo[i]))
  cat(sprintf("    puxa o risco para baixo: %s\n", lote$driver_negativo[i]))
}

# --- visao global -------------------------------------------------------------
frequencia_drivers <- table(c(lote$driver_positivo))
top_global <- head(sort(frequencia_drivers, decreasing = TRUE), 4)

cat("\n=== FEATURE MAIS CITADA COMO DRIVER DE RISCO ===\n")
for (feature in names(top_global)) {
  cat(sprintf("- %-13s %d predicoes (%.0f%% do lote)\n",
              feature, top_global[feature], top_global[feature] / nrow(lote) * 100))
}

write.csv(lote, "outputs/explicacoes_predicoes.csv", row.names = FALSE)
cat("\nLog de auditoria salvo em outputs/explicacoes_predicoes.csv\n")
