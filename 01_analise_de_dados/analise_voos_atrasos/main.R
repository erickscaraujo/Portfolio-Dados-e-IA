# Atrasos de voos: pontualidade, cauda longa e cancelamentos

dir.create("outputs", showWarnings = FALSE)
set.seed(610)

COMPANHIAS <- data.frame(
  nome = c("AzulAir", "VerdeLinhas", "SolVoos", "PontaNet"),
  peso = c(0.30, 0.28, 0.24, 0.18),
  prob_atraso = c(0.16, 0.22, 0.30, 0.11),
  atraso_medio = c(38, 45, 65, 28),
  prob_cancelamento = c(0.012, 0.020, 0.031, 0.008)
)

AEROPORTOS <- c("GRU", "BSB", "REC", "POA")

gerar_voos <- function(n = 6000) {
  companhia <- sample(COMPANHIAS$nome, n, replace = TRUE, prob = COMPANHIAS$peso)
  params <- COMPANHIAS[match(companhia, COMPANHIAS$nome), ]

  atrasado <- runif(n) < params$prob_atraso
  atraso_min <- ifelse(atrasado,
                       pmin(600, rexp(n, 1 / params$atraso_medio)),
                       pmax(0, rnorm(n, 3, 5)))
  cancelado <- runif(n) < params$prob_cancelamento

  data.frame(
    companhia = companhia,
    origem = sample(AEROPORTOS, n, replace = TRUE),
    destino = sample(AEROPORTOS, n, replace = TRUE),
    atraso_min = round(pmax(0, ifelse(cancelado, NA, atraso_min)), 0),
    cancelado = cancelado
  )
}

voos <- gerar_voos()
voos$pontual <- !voos$cancelado & !is.na(voos$atraso_min) & voos$atraso_min < 15

# --- por companhia -----------------------------------------------------------
resumo <- do.call(rbind, lapply(COMPANHIAS$nome, function(nome) {
  sub <- voos[voos$companhia == nome & !voos$cancelado, ]
  atrasados <- sub$atraso_min[sub$atraso_min >= 15]

  data.frame(
    companhia = nome,
    voos = sum(voos$companhia == nome),
    pontualidade_pct = round(mean(sub$atraso_min < 15) * 100, 1),
    atraso_medio_quando_ocorre = round(mean(atrasados), 1),
    p90_atraso = round(quantile(sub$atraso_min, 0.9), 0),
    cancelamento_pct = round(mean(voos$cancelado[voos$companhia == nome]) * 100, 1)
  )
}))

cat("=== DESEMPENHO POR COMPANHIA ===\n")
print(resumo[order(-resumo$pontualidade_pct), ], row.names = FALSE)

melhor <- resumo[which.max(resumo$pontualidade_pct), ]
pior <- resumo[which.min(resumo$pontualidade_pct), ]
cat(sprintf("\nMais puntual: %s (%.1f%%) | menos puntual: %s (%.1f%%)\n",
            melhor$companhia, melhor$pontualidade_pct,
            pior$companhia, pior$pontualidade_pct))

# --- piores rotas ------------------------------------------------------------
voos_validos <- voos[!voos$cancelado, ]
voos_validos$rota <- paste(voos_validos$origem, "->", voos_validos$destino)
rotas_com_volume <- names(which(table(voos_validos$rota) >= 60))
rota_atraso <- tapply(voos_validos$atraso_min, voos_validos$rota, mean)
rota_atraso <- sort(rota_atraso[names(rota_atraso) %in% rotas_com_volume], decreasing = TRUE)

cat("\n=== ROTAS COM MAIOR ATRASO MEDIO (min 60 voos) ===\n")
for (rota in names(head(rota_atraso, 4))) {
  cat(sprintf("- %-14s %.0f min\n", rota, rota_atraso[rota]))
}

# --- grafico -----------------------------------------------------------------
png("outputs/voos_atrasos.png", width = 1150, height = 440, res = 110)
par(mfrow = c(1, 3), mar = c(4.5, 4.2, 3, 1))

hist(voos$atraso_min[!is.na(voos$atraso_min) & voos$atraso_min > 15],
     breaks = 40, col = "#b91c1c", border = "white",
     main = "Cauda dos atrasos (>15 min)", xlab = "minutos")

barplot(resumo$pontualidade_pct, names.arg = resumo$companhia,
        col = "#2563eb", border = NA, ylim = c(0, 100),
        main = "Pontualidade (%)", ylab = "% voos < 15 min de atraso")

barplot(resumo$cancelamento_pct, names.arg = resumo$companhia,
        col = "#dc2626", border = NA,
        main = "Cancelamentos (%)")

dev.off()
cat("\nPainel salvo em outputs/voos_atrasos.png\n")
