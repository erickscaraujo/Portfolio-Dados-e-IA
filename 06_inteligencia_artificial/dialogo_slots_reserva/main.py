"""State tracking de dialogo: preenche slots, aceita correcoes e confirma."""

import re
from datetime import date, timedelta

CIDADES = ["sao paulo", "rio de janeiro", "recife", "curitiba", "salvador", "belo horizonte"]
ORDEM_SLOTS = ["origem", "destino", "data"]
HOJE = date(2025, 8, 15)

REGEX_DATA = re.compile(r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?")


def extrair_cidade(texto: str) -> str | None:
    texto = texto.lower()
    for cidade in CIDADES:
        if cidade in texto:
            return cidade
    return None


def extrair_data(texto: str) -> date | None:
    texto = texto.lower()
    if "hoje" in texto:
        return HOJE
    if "amanha" in texto or "amanhã" in texto:
        return HOJE + timedelta(days=1)
    if correspondencia := REGEX_DATA.search(texto):
        dia, mes = int(correspondencia.group(1)), int(correspondencia.group(2))
        ano = int(correspondencia.group(3)) if correspondencia.group(3) else 2025
        try:
            return date(ano, mes, dia)
        except ValueError:
            return None
    return None


def atualizar_slots(slots: dict, mensagem: str) -> list[str]:
    """Preenche os slots citados na mensagem; devolve o que foi alterado."""
    alterados = []

    cidade = extrair_cidade(mensagem)
    if cidade:
        # se a frase traz duas cidades, a primeira e origem e a segunda destino
        todas = [c for c in CIDADES if c in mensagem.lower()]
        if len(todas) >= 2 and (not slots["origem"] or "de" not in mensagem.lower()):
            pass  # tratado abaixo pelo fluxo de pares
        if "de " + cidade in mensagem.lower() and not slots["origem"]:
            slots["origem"] = cidade
            alterados.append("origem")
        elif "para " + cidade in mensagem.lower() or "pra " + cidade in mensagem.lower():
            slots["destino"] = cidade
            alterados.append("destino")
        elif not slots["origem"]:
            slots["origem"] = cidade
            alterados.append("origem")
        elif not slots["destino"]:
            slots["destino"] = cidade
            alterados.append("destino")

    nova_data = extrair_data(mensagem)
    if nova_data and (
        "dia" in mensagem.lower() or "/" in mensagem or "amanh" in mensagem.lower() or "hoje" in mensagem.lower()
    ):
        slots["data"] = nova_data.isoformat()
        alterados.append("data")

    return alterados


class AssistenteReserva:
    def __init__(self) -> None:
        self.slots = dict.fromkeys(ORDEM_SLOTS)
        self.confirmado = False

    def faltantes(self) -> list[str]:
        return [slot for slot in ORDEM_SLOTS if not self.slots[slot]]

    def processar(self, mensagem: str) -> str:
        alterados = atualizar_slots(self.slots, mensagem)
        feedback = ""
        if alterados:
            resumo = ", ".join(f"{slot}={self.slots[slot]}" for slot in alterados)
            feedback = f"(anotado: {resumo})\n"

        faltando = self.faltantes()
        if faltando:
            perguntas = {
                "origem": "De qual cidade você sai?",
                "destino": "Para onde vamos?",
                "data": "Qual a data da viagem? (dd/mm ou 'amanhã')",
            }
            return feedback + perguntas[faltando[0]]

        if not self.confirmado:
            self.confirmado = True
            return (
                feedback + "Confirmando: "
                f"{self.slots['origem'].title()} -> {self.slots['destino'].title()} "
                f"em {self.slots['data']}. Posso emitir?"
            )
        return feedback + "Reserva emitida! Deseja algo mais? (digite 'reiniciar' para comecar outra)"

    def reiniciar(self) -> str:
        self.slots = dict.fromkeys(ORDEM_SLOTS)
        self.confirmado = False
        return "Nova reserva. De qual cidade você sai?"


if __name__ == "__main__":
    conversa_demo = [
        "quero viajar",
        "saindo de sao paulo",
        "na verdade para recife, nao curitiba",  # correcao no meio do dialogo
        "amanhã",
        "pode emitir sim",
        "reiniciar",
        "de belo horizonte para salvador dia 22/09",
        "ok pode emitir",
    ]

    assistente = AssistenteReserva()
    print("=== DIALOGO DEMO ===")
    for turno_usuario in conversa_demo:
        resposta = assistente.reiniciar() if turno_usuario == "reiniciar" else assistente.processar(turno_usuario)
        print(f"\nusuario> {turno_usuario}")
        print(f"bot>    {resposta}")
