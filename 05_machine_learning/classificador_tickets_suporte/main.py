"""Roteamento automatico de tickets de suporte para as filas corretas."""

from random import Random

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

SEED = 27
FILAS = {
    "cobranca": [
        "fatura veio errada cobraram duas vezes",
        "estorno do pagamento nao caiu na conta",
        "parcelamento com juros indevido na fatura",
        "boleto pago mas nao baixou o debito",
        "queria revisar a taxa da mensalidade",
        "cobranca de servico que nao contratei",
    ],
    "tecnico": [
        "aplicativo fecha sozinho ao abrir o extrato",
        "nao consigo fazer login aparece erro 500",
        "sistema fora do ar desde ontem a noite",
        "integração com o erp parou de sincronizar",
        "tela branca ao salvar relatorio",
        "lentidao extrema no carregamento das paginas",
    ],
    "cadastro": [
        "preciso atualizar meu endereco e telefone",
        "como altero o email cadastrado na conta",
        "quero incluir um dependente no perfil",
        "mudei de nome civil preciso corrigir o cadastro",
        "conta bloqueada por dados desatualizados",
        "trocar o cpf titular da assinatura",
    ],
    "sugestao": [
        "voces deveriam ter versao escura do app",
        "seria util exportar os relatorios em pdf",
        "sugiro notificacao quando a fatura fechar",
        "adicionem pix parcelado por favor",
        "achei legal o dashboard, falta filtro por mes",
        "poderiam liberar api publica para integracoes",
    ],
}
RUIDO = ["obrigado pela atencao", "bom dia equipe", "aguardo retorno", "segue em anexo print"]

RNG = Random(SEED)


def gerar_tickets(n_por_fila: int = 220) -> tuple[list[str], list[str]]:
    textos: list[str] = []
    rotulos: list[str] = []
    for fila, frases in FILAS.items():
        for _ in range(n_por_fila):
            base = RNG.choice(frases)
            # ruido realista: saudacao/anexo anexados a metade dos tickets
            if RNG.random() < 0.5:
                base = f"{RNG.choice(RUIDO)}, {base}"
            textos.append(base)
            rotulos.append(fila)
    return textos, rotulos


if __name__ == "__main__":
    textos, rotulos = gerar_tickets()
    treino_x, teste_x, treino_y, teste_y = train_test_split(
        textos, rotulos, test_size=0.25, stratify=rotulos, random_state=SEED
    )

    modelo = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        LogisticRegression(max_iter=1000, C=8),
    )
    modelo.fit(treino_x, treino_y)
    preditos = modelo.predict(teste_x)

    print("=== RELATORIO POR FILA ===")
    print(classification_report(teste_y, preditos, digits=3))

    ordem = sorted(FILAS)
    matriz = confusion_matrix(teste_y, preditos, labels=ordem)
    print("Matriz de confusao (linhas = fila real):")
    print(f"{'':<12}" + "".join(f"{fila:>12}" for fila in ordem))
    for fila, linha in zip(ordem, matriz, strict=True):
        print(f"{fila:<12}" + "".join(f"{v:>12}" for v in linha))

    vetorizador = modelo.named_steps["tfidfvectorizer"]
    classificador = modelo.named_steps["logisticregression"]
    vocabulo = np.array(vetorizador.get_feature_names_out())
    print("\nTermos mais decisivos por fila:")
    for idx, fila in enumerate(classificador.classes_):
        top = vocabulo[np.argsort(classificador.coef_[idx])[::-1][:5]]
        print(f"- {fila:<10} {', '.join(top)}")

    erros = [
        (real, previsto, texto)
        for texto, real, previsto in zip(teste_x, teste_y, preditos, strict=True)
        if real != previsto
    ]
    print(f"\nExemplos mal roteados ({len(erros)} de {len(teste_x)}):")
    for real, previsto, texto in erros[:3]:
        print(f"- [{texto[:60]}...] real={real} | roteado={previsto}")
