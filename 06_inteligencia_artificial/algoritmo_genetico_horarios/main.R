# Algoritmo genetico: escala de turnos 40 funcionarios x 14 dias

dir.create("outputs", showWarnings = FALSE)
set.seed(500)

N_FUNCIONARIOS <- 40
DIAS <- 14
TAM_POPULACAO <- 60
GERACOES <- 120
ELITE <- 5
PROB_MUTACAO <- 0.08
COBERTURA_MINIMA <- 12   # funcionarios trabalhando por dia

criar_individuo <- function(...) {
  matrix(sample(c(0L, 1L), N_FUNCIONARIOS * DIAS, replace = TRUE,
                prob = c(0.35, 0.65)),
         nrow = N_FUNCIONARIOS)  # celula com valor 1 significa trabalhando
}

fitness <- function(escala) {
  por_dia <- colSums(escala)
  por_semana_funcionario <- rowSums(escala[, 1:7]) + rowSums(escala[, 8:14])

  penalidade_cobertura <- sum(pmax(0, COBERTURA_MINIMA - por_dia)) * 10
  penalidade_sobrecarga <- sum(pmax(0, por_semana_funcionario - 6)) * 5
  # folga em dias alternados e desejavel: penaliza sequencias longas de trabalho
  penalidade_sequencia <- sum(apply(escala, 1, function(linha) {
    rle_seq <- rle(linha)
    max(rle_seq$lengths[rle_seq$values == 1])
  }) - 4)

  -(penalidade_cobertura + penalidade_sobrecarga + max(penalidade_sequencia, 0))
}

torneio <- function(populacao, scores) {
  candidatos <- sample(seq_len(TAM_POPULACAO), 3)
  populacao[[candidatos[which.max(scores[candidatos])]]]
}

crossover <- function(pai_a, pai_b) {
  corte <- sample(2:(N_FUNCIONARIOS * DIAS - 1), 1)
  filho <- c(pai_a[1:corte], pai_b[(corte + 1):(N_FUNCIONARIOS * DIAS)])
  matrix(filho, nrow = N_FUNCIONARIOS)
}

mutar <- function(individuo) {
  trocas <- sample(which(individuo == 0 | individuo == 1),
                   round(PROB_MUTACAO * N_FUNCIONARIOS * DIAS))
  individuo[trocas] <- 1L - individuo[trocas]
  individuo
}

# --- evolucao ----------------------------------------------------------------
populacao <- lapply(seq_len(TAM_POPULACAO), criar_individuo)
melhores_por_geracao <- numeric(GERACOES)

for (geracao in seq_len(GERACOES)) {
  scores <- vapply(populacao, fitness, numeric(1))
  melhores_por_geracao[geracao] <- max(scores)

  ordem <- order(scores, decreasing = TRUE)
  nova_populacao <- populacao[ordem[seq_len(ELITE)]]

  while (length(nova_populacao) < TAM_POPULACAO) {
    filho <- crossover(torneio(populacao, scores), torneio(populacao, scores))
    nova_populacao[[length(nova_populacao) + 1]] <- mutar(filho)
  }
  populacao <- nova_populacao
}

scores_finais <- vapply(populacao, fitness, numeric(1))
melhor_indice <- which.max(scores_finais)
melhor_escala <- populacao[[melhor_indice]]

cat("=== EVOLUCAO ===\n")
cat(sprintf("- geracao 1 : melhor fitness %.0f\n", melhores_por_geracao[1]))
cat(sprintf("- geracao %d : melhor fitness %.0f\n",
            GERACOES, melhores_por_geracao[GERACOES]))

cobertura_final <- colSums(melhor_escala)
cat(sprintf("\nCobertura por dia (minima exigida: %d):\n", COBERTURA_MINIMA))
print(cobertura_final)

dias_quebrando <- sum(cobertura_final < COBERTURA_MINIMA)
horas_por_pessoa <- rowSums(melhor_escala)
cat(sprintf("\nDias abaixo da cobertura minima: %d\n", dias_quebradingo <- dias_quebrando))
cat(sprintf("Carga por funcionario: min %d | media %.1f | max %d\n",
            min(horas_por_pessoa), mean(horas_por_pessoa), max(horas_por_pessoa)))

png("outputs/genetico_turnos.png", width = 900, height = 430, res = 110)
plot(melhores_por_geracao, type = "l", lwd = 2.2, col = "#7c3aed",
     xlab = "geracao", ylab = "melhor fitness",
     main = "Convergencia do algoritmo genetico")
grid()
dev.off()
cat("\nCurva salva em outputs/genetico_turnos.png\n")
