"""Deduplicacao fuzzy de cadastros: mesma pessoa escrita de formas diferentes."""

from difflib import SequenceMatcher


def normalizar(texto: str) -> str:
    return " ".join("".join(c for c in texto.lower() if c.isalnum() or c == " ").split())


def similaridade(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _blocos_por_inicial(registros: list[dict]) -> dict[str, list[int]]:
    """Blocking barato: so compara nomes que comecam com a mesma letra."""
    blocos: dict[str, list[int]] = {}
    for indice, registro in enumerate(registros):
        blocos.setdefault(normalizar(registro["nome"])[:1], []).append(indice)
    return blocos


def encontrar_duplicatas(
    registros: list[dict],
    limiar_nome: float = 0.82,
    exigir_email_ou_telefone: bool = True,
) -> list[tuple[int, int, float]]:
    """Pares candidatos: nome parecido + (email OU telefone coincidindo)."""
    pares: list[tuple[int, int, float]] = []
    for _, indices in _blocos_por_inicial(registros).items():
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                a, b = registros[indices[i]], registros[indices[j]]

                score_nome = similaridade(normalizar(a["nome"]), normalizar(b["nome"]))
                if score_nome < limiar_nome:
                    continue

                mesmo_email = normalizar(a.get("email", "")) == normalizar(b.get("email", "")) != ""
                mesmo_telefone = (
                    {d for d in a.get("telefone", "") if d.isdigit()}
                    == {d for d in b.get("telefone", "") if d.isdigit()}
                    != set()
                )

                contato_confirma = mesmo_email or mesmo_telefone
                if contato_confirma or not exigir_email_ou_telefone:
                    pares.append((indices[i], indices[j], round(score_nome, 3)))
    return pares


def agrupar(pares: list[tuple[int, int, float]], n_registros: int) -> list[list[int]]:
    """Union-find simples transforma os pares em clusters de duplicatas."""
    pai = list(range(n_registros))

    def raiz(x: int) -> int:
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for a, b, _ in pares:
        pai[raiz(a)] = raiz(b)

    clusters: dict[int, list[int]] = {}
    for indice in range(n_registros):
        clusters.setdefault(raiz(indice), []).append(indice)
    return [grupo for grupo in clusters.values() if len(grupo) > 1]
