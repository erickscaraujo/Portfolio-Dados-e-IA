# Gera as fontes de exemplo que o scanner vai descobrir

dir.create("fontes", showWarnings = FALSE)
set.seed(170)

clientes <- data.frame(
  cliente_id = 1:300,
  nome = paste("Cliente", 1:300),
  uf = sample(c("SP", "RJ", "MG"), 300, replace = TRUE),
  email = paste0("c", 1:300, "@mail.com")
)

pedidos <- data.frame(
  pedido_id = sprintf("P%04d", 1:800),
  cliente_id = sample(1:320, 800, replace = TRUE),   # alguns orfaos de proposito
  valor = round(runif(800, 20, 900), 2)
)

# arquivo sem chave unica: o scanner deve reportar nenhuma candidata
eventos <- data.frame(
  evento = sample(c("view", "cart", "buy"), 500, replace = TRUE),
  cliente_id = sample(1:300, 500, replace = TRUE),
  minuto_do_dia = sample(0:1439, 500, replace = TRUE)
)

write.csv(clientes, "fontes/clientes.csv", row.names = FALSE)
write.csv(pedidos, "fontes/pedidos.csv", row.names = FALSE)
write.csv(eventos, "fontes/eventos.csv", row.names = FALSE)

cat("3 fontes geradas em fontes/ (clientes, pedidos, eventos)\n")
