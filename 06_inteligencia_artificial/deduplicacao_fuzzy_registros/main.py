"""Encontra e consolida cadastros duplicados plantados numa base de clientes."""

from deduplicatas import agrupar, encontrar_duplicatas

BASE = [
    {"nome": "Maria Eduarda Silva", "email": "maria.silva@mail.com", "telefone": "(11) 98888-1234"},
    {"nome": "Maria da Silva, Eduarda", "email": "maria.silva@mail.com", "telefone": "11988881234"},
    {"nome": "Joao Pedro Almeida", "email": "jpalmeida@mail.com", "telefone": "(21) 99777-4321"},
    {"nome": "Joao Pedro de Almeida", "email": "joaopedro.almeida@mail.com", "telefone": "(21) 99777-4321"},
    {"nome": "Carla Regina Souza", "email": "carla.souza@mail.com", "telefone": "(31) 98111-0000"},
    {"nome": "Carlos Eduardo Nunes", "email": "cadu.nunes@mail.com", "telefone": "(41) 99666-5555"},
    {"nome": "carlos eduardo nunes", "email": "cadu.nunes@mail.com", "telefone": "4199666 5555"},
    {"nome": "Rafael Costa", "email": "rafa.costa@mail.com", "telefone": "(85) 98500-2020"},
    # pessoas distintas que o time de cadastro confunde (mesmo sobrenome e telefone antigo)
    {"nome": "Rafaella Costa", "email": "rafaella.costa@mail.com", "telefone": "(85) 98500-2021"},
    {"nome": "Beatriz Lima", "email": "bia.lima@mail.com", "telefone": "(19) 98222-3344"},
    {"nome": "Beatriz Lima", "email": "beatriz.lima@outro.com", "telefone": "(19) 98222-3344"},
    {"nome": "Gustavo Ferreira", "email": "gustavo.f@mail.com", "telefone": "(62) 99333-8080"},
]


def main() -> None:
    pares = encontrar_duplicatas(BASE)
    clusters = agrupar(pares, len(BASE))

    print(f"Registros analisados: {len(BASE)} | pares candidatos: {len(pares)}")
    print("\n=== PARES CANDIDATOS ===")
    for a, b, score in pares:
        print(f"- [{score:.3f}] '{BASE[a]['nome']}' ~ '{BASE[b]['nome']}'")

    print("\n=== GRUPOS DE DUPLICATAS ===")
    for grupo in clusters:
        for indice in grupo:
            print(f"   * {BASE[indice]['nome']} | {BASE[indice]['email']}")
        print("   -> consolidar em um unico cadastro\n")

    falso_positivo_esperado = any(
        len(grupo) > 1
        and any("Rafael" in BASE[i]["nome"] and "Rafaella" in BASE[j]["nome"] for i in grupo for j in grupo if i != j)
        for grupo in clusters
    )
    if falso_positivo_esperado:
        print("Atencao: Rafael x Rafaella empatou no bloco; revisao humana recomendada nesses casos.")


if __name__ == "__main__":
    main()
