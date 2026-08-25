# Scanner de fontes: perfila os CSVs de uma pasta e sugere chaves/relacoes

dir.create("outputs", showWarnings = FALSE)

perfil_coluna <- function(serie) {
  list(
    tipo_inferido = class(serie)[1],
    nulos_pct = round(mean(is.na(serie)) * 100, 1),
    unicos = length(unique(serie)),
    amostra = as.character(head(na.omit(serie), 3))
  )
}

perfil_arquivo <- function(caminho) {
  df <- read.csv(caminho, stringsAsFactors = FALSE)
  colunas <- lapply(df, perfil_coluna)

  chaves_candidatas <- names(colunas)[
    vapply(colunas, function(p) p$nulos_pct == 0 && p$unicos == nrow(df), logical(1))
  ]

  list(
    arquivo = basename(caminho),
    linhas = nrow(df),
    colunas = colunas,
    chaves_primarias_candidatas = chaves_candidatas,
    df = df
  )
}

par_e_fk <- function(valores_origem, destino, col_destino) {
  valores_destino <- unique(na.omit(destino$df[[col_destino]]))
  length(valores_destino) > 0 && all(valores_origem %in% valores_destino)
}

detectar_relacoes <- function(perfis) {
  relacoes <- character(0)

  for (origem in perfis) {
    for (coluna in names(origem$colunas)) {
      if (coluna %in% origem$chaves_primarias_candidatas) next

      valores_origem <- unique(na.omit(origem$df[[coluna]]))
      if (length(valores_origem) == 0) next

      for (destino in perfis) {
        if (identical(destino$arquivo, origem$arquivo)) next
        colunas_candidatas <- names(destino$colunas)[
          vapply(names(destino$colunas),
                 function(cd) par_e_fk(valores_origem, destino, cd),
                 logical(1))
        ]
        relacoes <- c(relacoes,
                      sprintf("%s:%s -> %s:%s",
                              origem$arquivo, coluna,
                              destino$arquivo, colunas_candidatas))
      }
    }
  }
  sort(unique(relacoes))
}

main <- function() {
  arquivos <- sort(list.files("fontes", pattern = "\\.csv$", full.names = TRUE))
  if (length(arquivos) == 0) {
    cat(sprintf("Nenhum CSV encontrado em fontes/\n"))
    return(invisible(NULL))
  }

  cat(sprintf("=== DESCOBERTA: %d fonte(s) em fontes/ ===\n", length(arquivos)))
  perfis <- lapply(arquivos, perfil_arquivo)

  for (perfil in perfis) {
    cat(sprintf("\n[ %s ] %d linhas | chaves candidatas: %s\n",
                perfil$arquivo, perfil$linhas,
                paste(perfil$chaves_primarias_candidatas, collapse = ", ")))
    for (coluna in names(perfil$colunas)) {
      dados <- perfil$colunas[[coluna]]
      cat(sprintf("   - %-18s %-9s nulos %5.1f%% unicos %4d\n",
                  coluna, dados$tipo_inferido, dados$nulos_pct, dados$unicos))
    }
  }

  relacoes <- detectar_relacoes(perfis)
  cat("\n=== RELACOES SUGERIDAS (FK provavel) ===\n")
  for (relacao in relacoes) cat(sprintf("- %s\n", relacao))

  inventario <- lapply(perfis, function(p) p[names(p) != "df"])
  json_minimo <- sprintf(
    '{"fontes": [%s], "relacoes_sugeridas": [%s]}',
    paste(vapply(inventario, function(f) {
      sprintf('{"arquivo": "%s", "linhas": %d}', f$arquivo, f$linhas)
    }, character(1)), collapse = ", "),
    paste0('"', relacoes, '"', collapse = ", ")
  )
  writeLines(json_minimo, "outputs/inventario_fontes.json")

  cat("\nInventario salvo em outputs/inventario_fontes.json\n")
}

main()
