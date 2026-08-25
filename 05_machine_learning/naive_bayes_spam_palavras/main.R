# Naive Bayes multinomial de spam, implementado do zero

dir.create("outputs", showWarnings = FALSE)
set.seed(490)

TEMPLATES_SPAM <- c(
  "ganhe {valor} reais agora mesmo clique aqui",
  "oferta imperdivel {produto} com desconto exclusivo para o time",
  "prazo final hoje aproveite a promocao {produto} do mes",
  "voce foi selecionado receba {valor} sem custo no projeto",
  "emprestimo aprovado sem consulta clique ja e confirme hoje"
)
TEMPLATES_HAM <- c(
  "reuniao do projeto amanha as {hora} na sala {sala}",
  "segue o relatorio mensal que combinamos ontem",
  "obrigado pelo feedback vou revisar o relatorio e retorno {hora}",
  "lembrete: aniversario da {pessoa} sexta feira depois do expediente",
  "anexo a planilha com os numeros de {mes} para o time"
)
PRODUTOS <- c("smartwatch", "curso online", "suplemento", "cripto")
PESSOAS <- c("ana", "bruno", "carla", "diego")
MESES <- c("janeiro", "fevereiro", "marco", "abril")


definir_palavra <- function(modelo) UseMethod("definir_palavra", modelo)


# palavras neutras aparecem nas duas classes: evita separacao trivial
FILLER <- c("equipe", "sistema", "cliente", "projeto", "hoje", "rapido", "valor", "time")


gerar_emails <- function(n_por_classe = 400) {
  gerar_um <- function(classe) {
    template <- if (classe == "spam") sample(TEMPLATES_SPAM, 1) else sample(TEMPLATES_HAM, 1)
    texto <- template
    texto <- sub("\\{valor\\}", as.character(sample(c(500, 1000, 5000), 1)), texto)
    texto <- sub("\\{produto\\}", sample(PRODUTOS, 1), texto)
    texto <- sub("\\{hora\\}", paste0(sample(9:17, 1), "h"), texto)
    texto <- sub("\\{sala\\}", sample(c("A", "B", "C"), 1), texto)
    texto <- sub("\\{pessoa\\}", sample(PESSOAS, 1), texto)
    texto <- sub("\\{mes\\}", sample(MESES, 1), texto)
    # ruido compartilhado entre as classes
    texto <- paste(texto, paste(sample(FILLER, 3), collapse = " "))
    data.frame(texto = texto, classe = classe, stringsAsFactors = FALSE)
  }
  rbind(do.call(rbind, lapply(rep("spam", n_por_classe), gerar_um)),
        do.call(rbind, lapply(rep("ham", n_por_classe), gerar_um)))
}

tokenizar <- function(texto) {
  strsplit(tolower(texto), "[^a-z0-9]+")[[1]]
}

emails <- gerar_emails()
indices_teste <- unlist(lapply(unique(emails$classe), function(cl) {
  sample(which(emails$classe == cl), n_por_classe_teste <- 100)
}))
treino <- emails[-indices_teste, ]
teste <- emails[indices_teste, ]

# --- treinamento: contagem de palavras por classe ---------------------------
palavras_spam <- unlist(lapply(treino$texto[treino$classe == "spam"], tokenizar))
palavras_ham <- unlist(lapply(treino$texto[treino$classe == "ham"], tokenizar))

contagem_spam <- table(palavras_spam)
contagem_ham <- table(palavras_ham)
total_spam <- sum(contagem_spam)
total_ham <- sum(contagem_ham)
vocabulario <- union(names(contagem_spam), names(contagem_ham))
prior_spam <- mean(treino$classe == "spam")

cat(sprintf("Treino: %d emails (%.0f%% spam) | vocabulario: %d palavras\n",
            nrow(treino), prior_spam * 100, length(vocabulario)))

# log P(palavra | classe) com Laplace
log_prob_palavra <- function(palavra, contagem, total) {
  frequencia <- ifelse(is.na(contagem[palavra]), 0, as.integer(contagem[palavra]))
  log((frequencia + 1) / (total + length(vocabulario)))
}

classificar <- function(texto) {
  tokens <- tokenizar(texto)
  score_spam <- log(prior_spam) + sum(log_prob_palavra(tokens, contagem_spam, total_spam))
  score_ham <- log(1 - prior_spam) + sum(log_prob_palavra(tokens, contagem_ham, total_ham))
  ifelse(score_spam > score_ham, "spam", "ham")
}

# --- avaliacao --------------------------------------------------------------
teste$previsto <- vapply(teste$texto, classificar, character(1))
matriz <- table(real = teste$classe, previsto = teste$previsto)

vp <- matriz["spam", "spam"]
fn <- matriz["spam", "ham"]
fp <- matriz["ham", "spam"]

precisao <- vp / max(vp + fp, 1)
recall <- vp / max(vp + fn, 1)
f1 <- 2 * precisao * recall / max(precisao + recall, 1e-9)

cat("\n=== MATRIZ DE CONFUSAO ===\n")
print(matriz)
cat(sprintf("\nPrecisao: %.3f | Recall: %.3f | F1: %.3f\n",
            precisao, recall, f1))

# --- palavras mais spammy ---------------------------------------------------
odds_spam <- vapply(vocabulario, function(p) {
  exp(log_prob_palavra(p, contagem_spam, total_spam) -
        log_prob_palavra(p, contagem_ham, total_ham))
}, numeric(1))
ordem_odds <- order(odds_spam, decreasing = TRUE)[1:8]
cat("\nPalavras mais indicativas de spam (razao de odds):\n")
for (i in ordem_odds) {
  cat(sprintf("- %-14s %.1fx\n", vocabulario[i], odds_spam[i]))
}
