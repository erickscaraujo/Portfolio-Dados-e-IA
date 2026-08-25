# Clima: chuva mensal, veranico e amplitude termica

dir.create("outputs", showWarnings = FALSE)
set.seed(420)

gerar_clima <- function(dias = 1095) {
  datas <- seq(as.Date("2022-01-01"), by = "day", length.out = dias)
  mes <- as.integer(format(datas, "%m"))

  # estacao chuvosa nov-mar; seca de junho a agosto
  proba_chuva <- c(0.55, 0.52, 0.48, 0.35, 0.18, 0.08,
                   0.06, 0.07, 0.15, 0.32, 0.50, 0.58)[mes]
  choveu <- runif(dias) < proba_chuva
  mm <- ifelse(choveu, round(rexp(dias, rate = 1 / 14), 1), 0)

  temp_media <- 24 - abs(mes - 7.5) * 0.6
  data.frame(
    data = datas,
    choveu = choveu,
    mm = mm,
    t_min = round(temp_media - 5 - runif(dias, 0, 3), 1),
    t_max = round(temp_media + 5 + runif(dias, 0, 4), 1)
  )
}

clima <- gerar_clima()
clima$ano_mes <- format(clima$data, "%Y-%m")

# --- chuva ------------------------------------------------------------------
mensal_mm <- tapply(clima$mm, clima$ano_mes, sum)
mensal_dias <- tapply(clima$choveu, clima$ano_mes, sum)

cat("=== CHUVA MENSAL (mm | dias de chuva) ===\n")
for (i in seq_along(mensal_mm)) {
  cat(sprintf("- %s : %6.1f mm | %2d dias\n",
              names(mensal_mm)[i], mensal_mm[i], mensal_dias[i]))
}

# --- maior sequencia seca ---------------------------------------------------
maior_seca <- function(choveu_vec) {
  max_rle <- max(rle(!choveu_vec)$lengths[rle(!choveu_vec)$values])
  max_rle
}
seca_recorte <- maior_seca(clima$choveu[1:365])   # primeiro ano

cat(sprintf("\nMaior veranico do primeiro ano: %d dias sem chuva\n", seca_recorte))

# --- temperatura ------------------------------------------------------------
mes_abreviado <- substr(clima$data, 6, 7)
tmax_mensal <- tapply(clima$t_max, mes_abreviado, mean)
tmin_mensal <- tapply(clima$t_min, mes_abreviado, mean)

amplitude_mensal <- data.frame(
  mes = as.integer(names(tmax_mensal)),
  amplitude = round(as.numeric(tmax_mensal - tmin_mensal), 1)
)

cat("\n=== AMPLITUDE TERMICA MEDIA POR MES ===\n")
print(amplitude_mensal[, c("mes", "amplitude")], row.names = FALSE)

# --- grafico ----------------------------------------------------------------
png("outputs/clima_chuvas.png", width = 1150, height = 700, res = 110)
par(mfrow = c(2, 1), mar = c(4, 4.2, 3, 1))

barplot(mensal_mm, col = "#0ea5e9", border = NA,
        main = "Chuva mensal (mm)", ylab = "mm")
barplot(amplitude_mensal$amplitude,
        names.arg = month.abb[as.integer(amplitude_mensal$mes)],
        col = "#f59e0b", border = NA,
        main = "Amplitude termica media (C)", ylab = "t_max - t_min")

dev.off()
cat("\nPainel salvo em outputs/clima_chuvas.png\n")
