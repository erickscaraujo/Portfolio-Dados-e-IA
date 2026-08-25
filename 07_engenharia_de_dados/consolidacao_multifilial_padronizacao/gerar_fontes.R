# Gera as fontes das 3 filiais com inconsistencias de proposito

dir.create("fontes", showWarnings = FALSE)
set.seed(510)

gerar_filial <- function(filial, uf_bruta, n = 400) {
  datas <- as.Date("2025-04-01") + sample(0:89, n, replace = TRUE)
  data.frame(
    pedido = sprintf("%s-%04d", filial, seq_len(n)),
    data_venda = format(datas, "%Y-%m-%d"),
    valor = round(runif(n, 25, 1500), 2),
    vendedor = sample(paste0("Vend", 1:12), n, replace = TRUE),
    estado = sample(uf_bruta, n, replace = TRUE)
  )
}

# cada filial escreve a UF do seu jeito
sp <- gerar_filial("SP", c("sp", "SP", "S.P."))
rj <- gerar_filial("RJ", c("rj ", "RJ", "R-j"))
mg <- gerar_filial("MG", c("MG", "mg", "Minas"))

write.csv(sp, "fontes/filial_sp.csv", row.names = FALSE)
write.csv(rj, "fontes/filial_rj.csv", row.names = FALSE)
write.csv(mg, "fontes/filial_mg.csv", row.names = FALSE)

cat("3 fontes regionais geradas em fontes/\n")
