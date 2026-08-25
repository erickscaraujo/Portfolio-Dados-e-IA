# Perceptron de camada unica: aprende AND/OR, falha no XOR

dir.create("outputs", showWarnings = FALSE)
set.seed(710)

TAXA_APRENDIZADO <- 0.1
MAX_EPOCAS <- 200


treinar_perceptron <- function(X, y, max_epocas = MAX_EPOCAS) {
  pesos <- runif(ncol(X) + 1, -0.5, 0.5)   # ultimo peso = bias
  historico_erros <- integer(max_epocas)

  for (epoca in seq_len(max_epocas)) {
    erros_epoca <- 0
    for (i in seq_len(nrow(X))) {
      entrada <- c(as.numeric(X[i, ]), 1)
      ativacao <- if (sum(entrada * pesos) > 0) 1 else 0
      erro <- y[i] - ativacao

      if (erro != 0) {
        pesos <- pesos + TAXA_APRENDIZADO * erro * entrada
        erros_epoca <- erros_epoca + 1
      }
    }
    historico_erros[epoca] <- erros_epoca
    if (erros_epoca == 0) {
      return(list(pesos = pesos, epocas = epoca, convergiu = TRUE,
                  historico = historico_erros[seq_len(epoca)]))
    }
  }
  list(pesos = pesos, epocas = max_epocas, convergiu = FALSE,
       historico = historico_erros)
}

predizer <- function(modelo, X) {
  vapply(seq_len(nrow(X)), function(i) {
    as.integer(sum(c(as.numeric(X[i, ]), 1) * modelo$pesos) > 0)
  }, integer(1))
}

# datasets classicos com bias embutido como coluna extra
X_logico <- data.frame(a = c(0, 0, 1, 1), b = c(0, 1, 0, 1))

casos <- list(
  AND = data.frame(X_logico, y = c(0, 0, 0, 1)),
  OR = data.frame(X_logico, y = c(0, 1, 1, 1)),
  XOR = data.frame(X_logico, y = c(0, 1, 1, 0))
)

for (nome in names(casos)) {
  caso <- casos[[nome]]
  X <- caso[, c("a", "b")]
  y <- caso$y

  modelo <- treinar_perceptron(X, y)

  cat(sprintf("\n=== PORTA %s ===\n", nome))
  if (modelo$convergiu) {
    cat(sprintf("Convergiu em %d epocas\n", modelo$epocas))
  } else {
    cat(sprintf("NAO convergiu apos %d epocas: o XOR nao e linearmente separavel\n",
                modelo$epocas))
  }

  predicoes <- predizer(modelo, X)
  for (i in seq_along(predicoes)) {
    cat(sprintf("  %d %s %d -> previsto %d | real %d\n",
                X$a[i], "&", X$b[i], predicoes[i], y[i]))
  }

  if (nome == "AND" && modelo$convergiu) {
    # fronteira de decisao em grade para visualizar a reta aprendida
    grade <- expand.grid(a = 0:4, b = 0:4)
    saidas <- matrix(predizer(modelo, grade), nrow = 5, byrow = TRUE)
    cat("\nFronteira de decisao (grade estendida):\n")
    print(saidas)
  }
}

cat("\nMoral da historia: um neuronio so desenha uma reta. O XOR precisa de duas")
cat("\nretas -> nasce a ideia de camada oculta e o multilayer perceptron.\n")
