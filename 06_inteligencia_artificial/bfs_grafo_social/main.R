# BFS em grafo social: graus de separacao e influencia

dir.create("outputs", showWarnings = FALSE)
set.seed(720)

N_PESSOAS <- 25

gerar_amizades <- function(n = N_PESSOAS, densidade = 0.18) {
  nomes <- sprintf("P%02d", seq_len(n))
  amizades <- matrix(FALSE, n, n, dimnames = list(nomes, nomes))

  for (i in seq_len(n - 1)) {
    for (j in (i + 1):n) {
      if (runif(1) < densidade) {
        amizades[i, j] <- TRUE
        amizades[j, i] <- TRUE
      }
    }
  }
  # garante conectividade: cada pessoa conhece o proximo id
  for (i in seq_len(n - 1)) {
    amizades[i, i + 1] <- TRUE
    amizades[i + 1, i] <- TRUE
  }

  vizinhos <- lapply(seq_len(n), function(i) names(which(amizades[i, ])))
  names(vizinhos) <- nomes
  list(amizades = amizades, vizinhos = vizinhos)
}

rede <- gerar_amizades()

bfs_distancias <- function(origem) {
  distancias <- setNames(rep(NA_integer_, N_PESSOAS), names(rede$vizinhos))
  distancias[origem] <- 0
  fila <- origem

  while (length(fila) > 0) {
    atual <- fila[1]
    fila <- fila[-1]

    for (vizinho in rede$vizinhos[[atual]]) {
      if (is.na(distancias[vizinho])) {
        distancias[vizinho] <- distancias[atual] + 1
        fila <- c(fila, vizinho)
      }
    }
  }
  distancias
}

caminho_mais_curto <- function(origem, destino) {
  distancias <- setNames(rep(NA_integer_, N_PESSOAS), names(rede$vizinhos))
  distancias[origem] <- 0
  pais <- setNames(rep(NA_character_, N_PESSOAS), names(rede$vizinhos))
  fila <- origem

  while (length(fila) > 0) {
    atual <- fila[1]
    fila <- fila[-1]
    if (atual == destino) break

    for (vizinho in rede$vizinhos[[atual]]) {
      if (is.na(distancias[vizinho])) {
        distancias[vizinho] <- distancias[atual] + 1
        pais[vizinho] <- atual
        fila <- c(fila, vizinho)
      }
    }
  }

  caminho <- destino
  no_atual <- destino
  while (!is.na(pais[no_atual]) && pais[no_atual] != origem) {
    no_atual <- pais[no_atual]
    caminho <- c(no_atual, caminho)
  }
  c(origem, caminho)
}

alcance_dois_saltos <- vapply(names(rede$vizinhos), function(pessoa) {
  dists <- bfs_distancias(pessoa)
  sum(!is.na(dists) & dists <= 2)
}, integer(1))

cat("=== PESSOAS MAIS INFLUENTES (alcance em ate 2 saltos) ===\n")
top_influentes <- head(sort(alcance_dois_saltos, decreasing = TRUE), 5)
for (pessoa in names(top_influentes)) {
  cat(sprintf("- %s alcanca %d pessoas\n", pessoa, top_influentes[pessoa]))
}

graus_separacao_medios <- sapply(names(rede$vizinhos), function(pessoa) {
  media_dists <- mean(bfs_distancias(pessoa)[-which(names(bfs_distancias(pessoa)) == pessoa)],
                      na.rm = TRUE)
})
cat(sprintf("\nGrau medio de separacao na rede: %.2f saltos\n",
            mean(graus_separacao_medios)))

caminho_demo <- caminho_mais_curto("P01", "P20")
cat(sprintf("\nCaminho mais curto P01 -> P20 (%d saltos):\n",
            length(caminho_demo) - 1))
cat(paste(caminho_demo, collapse = " -> "), "\n")
