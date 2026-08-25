"""Trilha de auditoria encadeada por hash: alterar o passado fica evidente."""

import hashlib
import json
from datetime import datetime, timedelta


def _hash(payload: dict, hash_anterior: str) -> str:
    conteudo = json.dumps(payload, sort_keys=True) + hash_anterior
    return hashlib.sha256(conteudo.encode()).hexdigest()


class TrilhaAuditoria:
    def __init__(self) -> None:
        self.registros: list[dict] = []
        self._hash_atual = "0" * 64  # genesis

    def registrar(self, ator: str, acao: str, detalhe: dict) -> dict:
        agora = datetime.now()
        payload = {
            "ator": ator,
            "acao": acao,
            "detalhe": detalhe,
            "timestamp": (agora + timedelta(seconds=len(self.registros))).isoformat(timespec="seconds"),
        }
        registro = {
            "seq": len(self.registros),
            **payload,
            "hash_anterior": self._hash_atual,
            "hash": _hash(payload, self._hash_atual),
        }
        self.registros.append(registro)
        self._hash_atual = registro["hash"]
        return registro

    def verificar(self) -> tuple[bool, int | None]:
        """Recomputa a cadeia; devolve (ok, seq do primeiro registro adulterado)."""
        hash_esperado = "0" * 64
        for registro in self.registros:
            payload = {k: registro[k] for k in ("ator", "acao", "detalhe", "timestamp")}
            recalculado = _hash(payload, hash_esperado)

            if registro["hash_anterior"] != hash_esperado or registro["hash"] != recalculado:
                return False, registro["seq"]

            hash_esperado = registro["hash"]
        return True, None

    def salvar(self, caminho: str) -> None:
        with open(caminho, "w", encoding="utf-8") as arq:
            json.dump(self.registros, arq, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    trilha = TrilhaAuditoria()

    # operacoes legitimas de um dia qualquer
    trilha.registrar("ana.souza", "SELECT", {"dataset": "base_clientes_pii", "linhas": 1200})
    trilha.registrar("bruno.lima", "UPDATE", {"tabela": "pedidos", "id": 8471, "campo": "status"})
    trilha.registrar("carla.dias", "EXPORT", {"destino": "s3://relatorios/", "formato": "csv"})
    trilha.registrar("diego.rocha", "GRANT", {"concedido_para": "elisa.melo", "em": "vw_vendas"})

    ok, seq = trilha.verificar()
    print(f"Cadeia apos operacoes legitimas: {'INTEGRA' if ok else f'VIOLADA em {seq}'}")

    # tentativa de apagar a evidencia: alguem edita o export no meio da trilha
    trilha.salvar("outputs/trilha_antes.json")
    registro_alterado = trilha.registros[2]
    registro_alterado["detalhe"]["formato"] = "xlsx"  # fraude silenciosa

    ok, seq = trilha.verificar()
    print(f"Apos editar o registro 2 retroativamente: {'INTEGRA' if ok else f'VIOLACAO detectada no seq={seq}'}")

    # restaurando o arquivo original, a cadeia volta a validar
    with open("outputs/trilha_antes.json", encoding="utf-8") as arq:
        trilha.registros = json.load(arq)
    ok, seq = trilha.verificar()
    print(f"Apos restaurar do snapshot salvo: {'INTEGRA' if ok else 'VIOLADA'}")

    trilha.salvar("outputs/trilha_auditoria.json")
    print(f"\n{len(trilha.registros)} registros persistidos em outputs/trilha_auditoria.json")
