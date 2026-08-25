# k-NN do zero: qualidade de vinho (bom/ruim) por propriedades quimicas

dir.create("outputs", showWarnings = FALSE)
set.seed(480)

gerar_vinhos <- function(n = 1200) {
  # classes com distribuições condicionais distintas -> separáveis no espaço químico
  classe <- sample(c("bom", "ruim"), n, replace = TRUE)

  alcool <- ifelse(classe == "bom", rnorm(n, 12.4, 0.6), rnorm(n, 9.9, 0.8))
  sulfitos <- ifelse(classe == "bom", rnorm(n, 42, 10), rnorm(n, 66, 13))
  acidez <- ifelse(classe == "bom", rnorm(n, 6.8, 0.5), rnorm(n, 7.3, 0.6))
  acucar <- ifelse(classe == "bom", rexp(n, 1 / 2.0), rexp(n, 1 / 3.4))

  data.frame(
    acidez = round(acidez, 2),
    acucar = round(acucar, 2),
    alcool = round(alcool, 2),
    sulfitos = round(sulfitos, 1),
    classe = factor(classe, levels = c("bom", "ruim"))
  )
}

vinhos <- gerar_vinhos()

# split estratificado: 30% para teste final
indices_teste <- c(
  sample(which(vinhos$classe == "bom"), sum(vinhos$classe == "bom") * 0.3),
  sample(which(vinhos$classe == "ruim"), sum(vinhos$classe == "ruim") * 0.3)
)
treino <- vinhos[-sort(indices_teste), ]
teste <- vinhos[sort(indices_teste), ]

features <- c("acidez", "acucar", "alcool", "sulfitos")

# padronizacao APENAS com estatisticas de treino (evita vazamento do holdout)
medias <- colMeans(treino[features])
desvios <- sapply(treino[features], sd)
padronizar <- function(df) as.data.frame(scale(df[features], center = medias, scale = desvios))

treino_x <- padronizar(treino)
teste_x <- padronizar(teste)

knn_prever <- function(X_novo, base_x, base_y, k) {
  novo_m <- as.matrix(X_novo)
  base_m <- as.matrix(base_x)

  # matriz completa de distancias euclidianas via expansao |a-b|^2
  distancias <- sqrt(
    outer(rowSums(novo_m^2), rowSums(base_m^2), "+") - 2 * novo_m %*% t(base_m)
  )

  vapply(seq_len(nrow(novo_m)), function(i) {
    vizinhos <- base_y[order(distancias[i, ])[seq_len(k)]]
    names(which.max(table(vizinhos)))
  }, character(1))
}

# escolha do k por validacao interna: ultimos 20% do treino
corte_val <- floor(0.8 * nrow(treino_x))
val_x <- treino_x[(corte_val + 1):nrow(treino_x), ]
val_y <- treino$classe[(corte_val + 1):nrow(treino)]
base_val_x <- treino_x[seq_len(corte_val), ]
base_val_y <- treino$classe[seq_len(corte_val)]

cat("=== ESCOLHA DO K (validacao interna) ===\n")
acuracias_k <- sapply(1:15, function(k) {
  mean(knn_prever(val_x, base_val_x, base_val_y, k) == val_y)
})
for (k in seq_along(acuracias_k)) {
  cat(sprintf("- k=%2d : %.3f\n", k, acuracias_k[k]))
}
melhor_k <- which.max(acuracias_k)
cat(sprintf("\nMelhor k: %d (%.3f)\n", melhor_k, max(acuracias_k)))

# teste final com o k escolhido
previsoes_final <- factor(knn_prever(teste_x, treino_x, treino$classe, melhor_k),
                          levels = levels(treino$classe))
matriz <- table(real = teste$classe, previsto = previsoes_final)

cat("\n=== MATRIZ DE CONFUSAO (holdout) ===\n")
print(matriz)

acuracia_final <- sum(diag(matriz)) / sum(matriz)
cat(sprintf("\nAcuracia final: %.1f%%\n", acuracia_final * 100))

erro_por_classe <- round(1 - diag(matriz) / rowSums(matriz), 3)
cat("Erro por classe:\n")
print(erro_por_classe)
