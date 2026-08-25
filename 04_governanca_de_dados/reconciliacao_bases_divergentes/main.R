# Reconciliacao CRM x ERP: mesmo cadastro, sistemas que discordam

dir.create("outputs", showWarnings = FALSE)
set.seed(680)

gerar_base <- function(n = 500, sistema = "crm") {
  data.frame(
    cliente_id = sprintf("C%04d", seq_len(n)),
    saldo = round(runif(n, 50, 20000), 2),
    status = sample(c("ativo", "suspenso", "inativo"), n, replace = TRUE,
                    prob = c(0.8, 0.12, 0.08))
  )
}

crm <- gerar_base()
erp <- crm

# o ERP esta desatualizado: saldos defasados e alguns status antigos
set.seed(681)
mudanca_saldo <- sample(seq_len(nrow(erp)), 60)
erp$saldo[mudanca_saldo] <- round(erp$saldo[mudanca_saldo] * runif(60, 0.6, 1.6), 2)
mudanca_status <- sample(setdiff(seq_len(nrow(erp)), mudanca_saldo), 25)
erp$status[mudanca_status] <- sample(c("ativo", "suspenso"), 25, replace = TRUE)

# --- comparacao ---------------------------------------------------------------
comparacao <- merge(crm, erp, by = "cliente_id",
                    suffixes = c("_crm", "_erp"))

comparacao$diferenca_saldo <- round(comparacao$saldo_erp - comparacao$saldo_crm, 2)
comparacao$percentual <- abs(comparacao$diferenca_saldo) / pmax(comparacao$saldo_crm, 1)
comparacao$status_difiere <- comparacao$status_crm != comparacao$status_erp

classificar <- function(percentual, diferenca_saldo, status_difiere) {
  if (!status_difiere && percentual <= 0.01) {
    return("identico")
  }
  if (abs(diferenca_saldo) <= 5 && !status_difiere) {
    return("diferenca aceitavel")
  }
  "divergencia critica"
}

comparacao$classificacao <- mapply(
  classificar,
  comparacao$percentual, comparacao$diferenca_saldo,
  comparacao$status_difiere
)

cat("=== RECONCILIACAO CRM X ERP ===\n")
print(table(comparacao$classificacao))

criticos <- comparacao[comparacao$classificacao == "divergencia critica", ]
cat(sprintf("\nDivergencias criticas: %d registros\n", nrow(criticos)))

if (nrow(criticos) > 0) {
  cat("\nTop 5 por tamanho da diferenca:\n")
  top_criticos <- head(criticos[order(-abs(criticos$diferenca_saldo)), ],
                       min(5, nrow(criticos)))
  print(top_criticos[, c("cliente_id", "saldo_crm", "saldo_erp",
                         "status_crm", "status_erp")], row.names = FALSE)
}

# resumo de qual campo mais diverge
campo_status <- sum(comparacao$status_difiere & comparacao$classificacao == "divergencia critica")
campo_saldo <- sum(abs(comparacao$diferenca_saldo) > max(comparacao$saldo_crm * 0.01, 5) &
                     comparacao$classificacao == "divergencia critica")
cat(sprintf("\nOrigem das criticas: saldo em %d | status em %d\n",
            campo_saldo, campo_status))

write.csv(criticos, "outputs/divergencias_criticas.csv", row.names = FALSE)
cat("\nCSV das criticas salvo em outputs/divergencias_criticas.csv\n")
