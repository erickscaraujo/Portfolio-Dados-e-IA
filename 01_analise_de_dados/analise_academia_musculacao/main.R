# Diario de musculacao: volume, progressao de carga e recordes

dir.create("outputs", showWarnings = FALSE)
set.seed(600)

EXERCICIOS <- data.frame(
  exercicio = c("supino", "agachamento", "remada", "rosca"),
  grupo = c("peito", "pernas", "costas", "biceps"),
  carga_inicial = c(60, 90, 50, 20),
  progressao_semanal = c(1.4, 2.0, 1.1, 0.5),
  stringsAsFactors = FALSE
)

SEMANAS <- 12
SERIES <- 4
REPS <- 8


gerar_treinos <- function() {
  linhas <- list()
  for (i in seq_len(nrow(EXERCICIOS))) {
    cfg <- EXERCICIOS[i, ]
    for (semana in seq_len(SEMANAS)) {
      carga_base <- cfg$carga_inicial + cfg$progressao_semanal * (semana - 1)
      # semanas de deload a cada 5: carga cai para consolidar
      carga_efetiva <- ifelse(semana %% 5 == 0, carga_base * 0.9, carga_base)
      linhas[[length(linhas) + 1]] <- data.frame(
        semana = semana,
        exercicio = cfg$exercicio,
        grupo = cfg$grupo,
        series = SERIES,
        reps = sample(6:10, 1),
        carga = round(max(carga_efetiva * rnorm(1, 1, 0.03), cfg$carga_inicial * 0.8), 1)
      )
    }
  }
  do.call(rbind, linhas)
}

treinos <- gerar_treinos()
treinos$volume <- treinos$series * treinos$reps * treinos$carga

# --- volume semanal ----------------------------------------------------------
volume_semanal <- tapply(treinos$volume, treinos$semana, sum)
cat("=== VOLUME TOTAL POR SEMANA (kg levantados) ===\n")
print(round(volume_semanal))

tendencia_volume <- lm(volume ~ semana,
                       data = data.frame(volume = as.numeric(volume_semanal),
                                         semana = as.integer(names(volume_semanal))))
cat(sprintf("\nTendencia do volume: %+.0f kg por semana (R2 %.2f)\n",
            coef(tendencia_volume)[2], summary(tendencia_volume)$r.squared))

# --- volume por grupo --------------------------------------------------------
volume_grupo <- tapply(treinos$volume, treinos$grupo, sum)
cat("\n=== VOLUME POR GRUPO MUSCULAR ===\n")
print(sort(round(volume_grupo), decreasing = TRUE))

# --- progressao de carga e PRs ----------------------------------------------
cat("\n=== PROGRESSAO E RECORDES POR EXERCICIO ===\n")
for (nome in EXERCICIOS$exercicio) {
  serie_exercicio <- treinos[treinos$exercicio == nome, ]
  ajuste <- lm(carga ~ semana, data = serie_exercicio)
  inclinacao <- coef(ajuste)[2]
  pr_idx <- which.max(serie_exercicio$carga)

  rotulo_progressao <- ifelse(inclinacao > 0.3,
                              sprintf("+%.1f kg/semana", inclinacao),
                              "estagnado")

  cat(sprintf("- %-13s PR %.1f kg (semana %d) | tendencia %s\n",
              nome, serie_exercicio$carga[pr_idx],
              serie_exercicio$semana[pr_idx], rotulo_progressao))
}

# --- grafico -----------------------------------------------------------------
png("outputs/musculacao_progresso.png", width = 1100, height = 440, res = 110)
par(mfrow = c(1, 2), mar = c(4.5, 4.2, 3, 1))

plot(as.integer(names(volume_semanal)), as.numeric(volume_semanal),
     type = "b", pch = 19, col = "#2563eb",
     xlab = "semana", ylab = "volume (kg)",
     main = "Volume total semanal")
abline(tendencia_volume, lty = 2, col = "gray40")

cores_grupos <- rainbow(length(unique(treinos$grupo)))
for (i in seq_along(EXERCICIOS$exercicio)) {
  sub <- treinos[treinos$exercicio == EXERCICIOS$exercicio[i], ]
  if (i == 1) {
    plot(sub$semana, sub$carga, type = "b", pch = 19, cex = 0.7,
         col = cores_grupos[i], xlab = "semana", ylab = "carga (kg)",
         main = "Progressao de carga por exercicio")
  } else {
    points(sub$semana, sub$carga, type = "b", pch = 19, cex = 0.7,
           col = cores_grupos[i])
  }
}
legend("topleft", legend = EXERCICIOS$exercicio, col = cores_grupos,
       pch = 19, cex = 0.8, bty = "n")

dev.off()
cat("\nPainel salvo em outputs/musculacao_progresso.png\n")
