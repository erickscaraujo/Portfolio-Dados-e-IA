# Frota: consumo, custo por km e utilizacao dos veiculos

dir.create("outputs", showWarnings = FALSE)
set.seed(440)

gerar_frota <- function(n = 30) {
  tipo <- sample(c("Sedan", "SUV", "Fiorino"), n, replace = TRUE, prob = c(0.5, 0.3, 0.2))
  km_mes <- round(runif(n, 1800, 6500))

  # SUV bebe mais; Fiorino economiza
  base_consumo <- c(Sedan = 11, SUV = 8.2, Fiorino = 13.5)[tipo]
  km_por_litro <- pmax(4, rnorm(n, base_consumo, 1.2))
  custo_manutencao <- round(runif(n, 400, 2600), 2)
  lambda_parados <- ifelse(tipo == "Fiorino", 2, ifelse(tipo == "SUV", 4, 3))
  dias_parados <- rpois(n, lambda = lambda_parados)

  data.frame(
    veiculo = sprintf("VEI-%02d", seq_len(n)),
    tipo = tipo,
    km_mes = km_mes,
    litros = round(km_mes / km_por_litro),
    custo_manutencao = custo_manutencao,
    dias_parados = dias_parados
  )
}

frota <- gerar_frota()
frota$km_por_litro <- round(frota$km_mes / frota$litros, 2)

preco_diesel <- 6.10
frota$custo_combustivel <- frota$litros * preco_diesel
frota$custo_km <- round((frota$custo_combustivel + frota$custo_manutencao) / frota$km_mes, 3)
frota$utilizacao_pct <- round((22 - frota$dias_parados) / 22 * 100, 1)

cat("=== TOP 8 CUSTOS POR KM (piores) ===\n")
piores <- frota[order(-frota$custo_km), ][1:8, ]
print(piores[, c("veiculo", "tipo", "km_mes", "km_por_litro", "custo_km", "utilizacao_pct")], row.names = FALSE)

# --- alertas -----------------------------------------------------------------
alerta_custo <- frota$frota_alerta_flag <- frota$custo_km > 1.20
alerta_consumo <- frota$km_por_litro < 8

cat("\n=== ALERTAS ===\n")
cat(sprintf("- Veiculos com custo/km acima de R$ 1,20 : %d\n", sum(alerta_custo)))
cat(sprintf("- Veiculos abaixo de 8 km/l             : %d\n", sum(alerta_consumo)))

criticos <- frota[alerta_custo | alerta_consumo, ]
if (nrow(criticos) > 0) {
  cat("\nLista critica:\n")
  print(criticos[, c("veiculo", "tipo", "custo_km", "km_por_litro")], row.names = FALSE)
}

resumo_tipo <- aggregate(
  cbind(custo_km_medio = custo_km, utilizacao = utilizacao_pct) ~ tipo,
  data = frota, FUN = mean
)
resumo_tipo <- transform(resumo_tipo,
                         custo_km_medio = round(custo_km_medio, 3),
                         utilizacao = round(utilizacao, 1))
cat("\n=== RESUMO POR TIPO ===\n")
print(resumo_tipo, row.names = FALSE)

# --- grafico -----------------------------------------------------------------
png("outputs/frota_veiculos.png", width = 1100, height = 460, res = 110)
par(mfrow = c(1, 2), mar = c(5, 4.2, 3, 1))

plot(frota$km_por_litro, frota$custo_km * 1000,
     col = ifelse(alerta_custo | alerta_consumo, "#dc2626", "#2563eb"),
     pch = 19, xlab = "consumo (km/l)", ylab = "custo por mil km (R$)",
     main = "Consumo x custo — vermelho = em alerta")
abline(h = 1200, lty = 2)
abline(v = 8, lty = 2)

barplot(resumo_tipo$custo_km_medio, names.arg = resumo_tipo$tipo,
        col = "#059669", border = NA,
        main = "Custo/km medio por tipo", ylab = "R$")

dev.off()

write.csv(criticos, "outputs/frota_alertas.csv", row.names = FALSE)
cat("\nPainel e CSV de alertas salvos em outputs/\n")
