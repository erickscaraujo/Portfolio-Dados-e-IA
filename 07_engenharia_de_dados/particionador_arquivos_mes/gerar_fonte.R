# Gera o CSV grande de vendas que sera particionado

dir.create("outputs", showWarnings = FALSE)
set.seed(730)

n <- 6000
vendas <- data.frame(
  pedido_id = sprintf("V%05d", seq_len(n)),
  data = format(as.Date("2024-01-01") + sample(0:364, n, replace = TRUE),
                "%Y-%m-%d"),
  valor = round(runif(n, 15, 1200), 2),
  canal = sample(c("site", "app", "loja"), n, replace = TRUE)
)

dir.create("fontes", showWarnings = FALSE)
write.csv(vendas, "fontes/vendas_ano.csv", row.names = FALSE)
cat(sprintf("Fonte gerada: %d linhas em fontes/vendas_ano.csv\n", n))
