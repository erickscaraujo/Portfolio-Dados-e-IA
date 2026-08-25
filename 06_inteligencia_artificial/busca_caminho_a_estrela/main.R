# A* em grade 20x20 com obstaculos e heuristica de Manhattan

LINHAS <- 20
COLUNAS <- 20
INICIO <- c(1, 1)
ALVO <- c(20, 20)
MOVIMENTOS <- matrix(c(0, 1, 0, -1, 1, 0, -1, 0), ncol = 2, byrow = TRUE)

criar_grade <- function() {
  muros <- matrix(FALSE, LINHAS, COLUNAS)

  # parede vertical no meio com uma passagem
  muros[2:15, 10] <- TRUE
  # blocos espalhados
  muros[5:8, 4:6] <- TRUE
  muros[14:17, 15:17] <- TRUE
  muros[3:4, 16:18] <- TRUE

  muros[INICIO[1], INICIO[2]] <- FALSE
  muros[ALVO[1], ALVO[2]] <- FALSE
  muros
}

heuristica_manhattan <- function(a, b) abs(a[1] - b[1]) + abs(a[2] - b[2])

busca_a_estrela <- function(grade) {
  g_custo <- matrix(Inf, LINHAS, COLUNAS)
  estado_pais <- new.env(parent = emptyenv())
  g_custo[INICIO[1], INICIO[2]] <- 0

  # open set como data.frame simples (grade pequena nao pede heap)
  aberto <- data.frame(
    linha = INICIO[1], coluna = INICIO[2],
    f = heuristica_manhattan(INICIO, ALVO)
  )

  while (nrow(aberto) > 0) {
    atual_idx <- which.min(aberto$f)
    atual <- c(aberto$linha[atual_idx], aberto$coluna[atual_idx])
    if (identical(unname(atual), unname(ALVO))) {
      break
    }
    aberto <- aberto[-atual_idx, ]

    for (m in seq_len(nrow(MOVIMENTOS))) {
      vizinho <- atual + MOVIMENTOS[m, ]
      fora_da_grade <- vizinho[1] < 1 || vizinho[1] > LINHAS ||
        vizinho[2] < 1 || vizinho[2] > COLUNAS
      if (fora_da_grade || grade[vizinho[1], vizinho[2]]) next

      custo_novo <- g_custo[atual[1], atual[2]] + 1
      if (custo_novo < g_custo[vizinho[1], vizinho[2]]) {
        g_custo[vizinho[1], vizinho[2]] <- custo_novo
        indice_vizinho <- vizinho[1] + (vizinho[2] - 1) * LINHAS
        assign(as.character(indice_vizinho), atual, envir = estado_pais)

        ja_no_aberto <- any(aberto$linha == vizinho[1] & aberto$coluna == vizinho[2])
        if (!ja_no_aberto) {
          aberto <- rbind(aberto, data.frame(
            linha = vizinho[1], coluna = vizinho[2],
            f = custo_novo + heuristica_manhattan(vizinho, ALVO)
          ))
        }
      }
    }
  }

  # reconstrucao do caminho a partir do alvo
  caminho <- list(ALVO)
  no_atual <- ALVO
  while (!identical(unname(no_atual), unname(INICIO))) {
    anterior <- get(as.character(no_atual[1] + (no_atual[2] - 1) * LINHAS),
                    envir = estado_pais)
    if (is.null(anterior)) return(list(caminho = NULL))
    caminho[[length(caminho) + 1]] <- anterior
    no_atual <- anterior
  }
  list(caminho = rev(caminho), g_final = g_custo[ALVO[1], ALVO[2]])
}

grade <- criar_grade()
resultado <- busca_a_estrela(grade)
caminho <- resultado$caminho

if (is.null(caminho)) {
  stop("nenhum caminho encontrado")
}

cat(sprintf("Caminho encontrado: %d passos (custo teorico sem muros seria %d)\n",
            length(caminho) - 1, sum(abs(ALVO - INICIO))))

# --- mapa ascii --------------------------------------------------------------
mapa_ascii <- matrix(".", LINHAS, COLUNAS)
mapa_ascii[grade] <- "#"
for (passo in caminho) mapa_ascii[passo[1], passo[2]] <- "*"
mapa_ascii[INICIO[1], INICIO[2]] <- "I"
mapa_ascii[ALVO[1], ALVO[2]] <- "A"

cat("\nMapa (I=inicio A=alvo #=muro *=caminho):\n")
print(t(mapa_ascii[, rev(seq_len(ncol(mapa_ascii)))]))
