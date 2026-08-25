"""Demonstra o mascaramento em uma base de clientes com PII e texto livre."""

import pathlib

import numpy as np
import pandas as pd
from mascarador import anonimizar_base, mascarar_texto

SEED = 77

OBSERVACOES_TIPO = [
    "Cliente prefere contato por email joao.silva@mail.com apos as 18h",
    "CPF 123.456.789-09 ja verificado na recepcao",
    "Ligar para (11) 98765-4321 antes de entregar",
    "Sem observacoes especiais",
    "Reclamou de cobranca; email maria.clara@mail.com para resposta",
]


def gerar_clientes(n: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    cpfs_base = rng.choice(99999999999, size=n, replace=False)
    return pd.DataFrame(
        {
            "cliente_id": range(1, n + 1),
            "nome": [f"Cliente {i}" for i in range(1, n + 1)],
            "cpf": [
                f"{c:011d}"[:3] + "." + f"{c:011d}"[3:6] + "." + f"{c:011d}"[6:9] + "-" + f"{c:011d}"[9:]
                for c in cpfs_base
            ],
            "email": [f"cliente{i}@mail.com" for i in range(1, n + 1)],
            "telefone": [
                f"({rng.integers(11, 99)}) 9{rng.integers(1000, 9999)}-{rng.integers(1000, 9999)}" for _ in range(n)
            ],
            "observacoes": rng.choice(OBSERVACOES_TIPO, n),
        }
    )


if __name__ == "__main__":
    pathlib.Path("outputs").mkdir(exist_ok=True)

    base_original = gerar_clientes()

    # prova do mascarador em texto livre antes da base inteira
    exemplo = "Falar com paula_ribeiro@mail.com ou (21) 98888-7777, CPF 987.654.321-00"
    print("=== TESTE DE TEXTO LIVRE ===")
    print(f"antes : {exemplo}")
    print(f"depois: {mascarar_texto(exemplo)}")

    base_anonima, auditoria = anonimizar_base(base_original)

    print("\n=== AUDITORIA DO MASCARAMENTO ===")
    for chave, valor in auditoria.items():
        print(f"- {chave}: {valor}")

    amostra = base_anonima.sample(3, random_state=SEED)
    print("\n=== AMOSTRA ANONIMIZADA ===")
    print(amostra.to_string(index=False))

    caminho = "outputs/clientes_anonimizados.csv"
    base_anonima.to_csv(caminho, index=False)
    print(f"\nBase segura salva em {caminho}")

    vazamentos = (
        base_anonima["email"].str.contains("@mail").any()
        or base_anonima["observacoes"].str.contains(r"\d{3}\.\d{3}\.\d{3}", regex=True).any()
    )
    print("Checagem final de vazamento:", "FALHOU" if vazamentos else "nenhum PII residual detectado")
