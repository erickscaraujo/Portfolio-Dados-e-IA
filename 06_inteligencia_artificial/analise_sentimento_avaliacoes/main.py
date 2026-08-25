"""Comparacao entre analise de sentimento lexica e modelo supervisionado."""

from random import Random

import lexico
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

SEED = 33
RNG = Random(SEED)

TEMPLATES_POSITIVOS = [
    "produto {adj} e chegou {tempo}, {verbo} demais",
    "atendimento {adj}, resolveram tudo {tempo}",
    "experiencia {adj}! entrega {tempo} e embalagem perfeita",
    "o app ficou {adj} e muito facil de usar",
    "comprei de novo porque e {adj}, {verbo} a loja",
]
TEMPLATES_NEGATIVOS = [
    "produto {adj} e ainda veio {tempo}",
    "atendimento {adj}, ninguem resolveu meu problema",
    "experiencia {adj}, o app fica travando {tempo}",
    "chegou {adj} e com defeito, {verbo} ter comprado",
    "servico {adj} e caro para a qualidade oferecida",
]
TEMPLATES_NEUTROS = [
    "o produto tem duas cores disponiveis",
    "comprei na segunda feira pela manha",
    "a loja fica no centro da cidade",
    "o pedido numero 8472 foi separado hoje",
    "a categoria eletronicos tem 130 itens",
]
ADJETIVOS_POS = ["otimo", "excelente", "maravilhoso", "perfeito", "rapido"]
ADJETIVOS_NEG = ["pessimo", "horrivel", "lento", "caro", "complicado"]
TEMPOS = ["antes do prazo", "no prazo", "em dois dias", "com uma semana de atraso"]
VERBOS_POS = ["recomendo", "adorei", "amei"]
VERBOS_NEG = ["arrependido", "odiei"]


def _preencher(templates: list[str], adjetivos: list[str], verbos: list[str], qtd: int) -> list[str]:
    frases = []
    for _ in range(qtd):
        template = RNG.choice(templates)
        frase = template.format(
            adj=RNG.choice(adjetivos),
            tempo=RNG.choice(TEMPOS),
            verbo=RNG.choice(verbos),
        )
        frases.append(frase)
    return frases


def gerar_avaliacoes(n_por_classe: int = 250) -> pd.DataFrame:
    dados = []
    rotulos = (
        ("positivo", TEMPLATES_POSITIVOS, ADJETIVOS_POS, VERBOS_POS),
        ("negativo", TEMPLATES_NEGATIVOS, ADJETIVOS_NEG, VERBOS_NEG),
        ("neutro", TEMPLATES_NEUTROS, [""], [""].copy()),
    )
    for classe, templates, adjs, verbos in rotulos:
        if classe == "neutro":
            # neutros nao usam adjetivos sentimentais
            for _ in range(n_por_classe):
                dados.append({"texto": RNG.choice(templates), "classe": classe})
        else:
            for frase in _preencher(templates, adjs, verbos, n_por_classe):
                dados.append({"texto": frase, "classe": classe})
    RNG.shuffle(dados)
    return pd.DataFrame(dados).reset_index(drop=True)


if __name__ == "__main__":
    base = gerar_avaliacoes()
    treino, teste = train_test_split(base, test_size=0.3, stratify=base["classe"], random_state=SEED)

    # abordagem 1: lexico (nao precisa de treino)
    pred_lexico = teste["texto"].map(lexico.classificar)
    acc_lexico = (pred_lexico == teste["classe"]).mean()

    # abordagem 2: TF-IDF + regressao logistica treinada nos exemplos
    modelo = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), lowercase=True),
        LogisticRegression(max_iter=1000),
    )
    modelo.fit(treino["texto"], treino["classe"])
    pred_ml = modelo.predict(teste["texto"])
    acc_ml = (pred_ml == teste["classe"]).mean()

    print("=== ANALISE DE SENTIMENTO: LEXICO VS SUPERVISIONADO ===")
    print(f"Acuracia lexico            : {acc_lexico:.1%}")
    print(f"Acuracia TF-IDF + LogReg   : {acc_ml:.1%}")

    print("\nRelatorio detalhado do modelo supervisionado:")
    print(classification_report(teste["classe"], pred_ml, digits=3))

    print("Matriz de confusao do lexico (linhas=real):")
    rotulos_ordenados = ["negativo", "neutro", "positivo"]
    matriz = confusion_matrix(teste["classe"], pred_lexico, labels=rotulos_ordenados)
    print(pd.DataFrame(matriz, index=rotulos_ordenados, columns=rotulos_ordenados).to_string())

    exemplos_dificeis = [
        "nao foi otimo o atendimento",
        "nao tenho do que reclamar",
        "produto muito bom, mas chegou lento",
    ]
    print("\nCasos dificeis (lexico vs modelo):")
    for frase in exemplos_dificeis:
        print(f"- '{frase}' -> lexico: {lexico.classificar(frase)} | modelo: {modelo.predict([frase])[0]}")
