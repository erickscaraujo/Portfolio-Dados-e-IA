"""Cliente educado de API: token bucket + backoff exponencial com jitter."""

import random

LIMITE_RPS = 40
JITTER_MAX_MS = 25


class ApiSimulada:
    """Aceita ate LIMITE_RPS por segundo; acima disso responde 429 com Retry-After."""

    def __init__(self, limite_rps: int = LIMITE_RPS) -> None:
        self.limite_rps = limite_rps
        self.janela_ms: float = -1e9
        self.contador_janela = 0
        self.total_429 = 0

    def chamar(self, agora_ms: float) -> tuple[int, float]:
        """Devolve (status, retry_after_ms). Tempo e simulado em ms."""
        janela_atual = int(agora_ms // 1000)
        if janela_atual != self.janela_ms:
            self.janela_ms = janela_atual
            self.contador_janela = 0

        if self.contador_janela >= self.limite_rps:
            self.total_429 += 1
            retry_after = int(1000 - (agora_ms % 1000)) + 5
            return 429, retry_after

        self.contador_janela += 1
        return 200, 0


def cliente_ingenuo(api: ApiSimulada, n_requisicoes: int) -> dict:
    sucessos = falhas = 0
    relogio = 0.0
    for _ in range(n_requisicoes):
        status, _ = api.chamar(relogio)
        if status == 200:
            sucessos += 1
        else:
            falhas += 1  # ingenuo ignora o 429 e nao tenta de novo
        relogio += 2  # dispara sem pausa relevante
    return {"sucessos": sucessos, "falhas_429": falhas, "tempo_total_ms": relogio}


def cliente_respeitoso(api: ApiSimulada, n_requisicoes: int, max_tentativas: int = 6) -> dict:
    sucessos = falhas = 0
    relogio = 0.0
    tokens_disponiveis = LIMITE_RPS
    ultima_chamada_ms = 0.0

    for _ in range(n_requisicoes):
        # token bucket local evita nem enviar o request que viraria 429
        intervalo_ms = max(relogio - ultima_chamada_ms, 0)
        tokens_disponiveis = min(LIMITE_RPS, tokens_disponiveis + LIMITE_RPS * intervalo_ms / 1000)

        tentativa = 0
        while True:
            if tokens_disponiveis >= 1:
                tokens_disponiveis -= 1
                status, retry_after = api.chamar(relogio)
            else:
                status, retry_after = 429, 30

            if status == 200:
                ultima_chamada_ms = relogio
                sucessos += 1
                break

            tentativa += 1
            if tentativa > max_tentativas:
                falhas += 1
                break

            espera = max(retry_after, 2**tentativa * 10 + random.uniform(0, JITTER_MAX_MS))
            relogio += espera
            tokens_disponiveis = min(LIMITE_RPS, tokens_disponiveis + LIMITE_RPS * espera / 1000)

        relogio += 3

    return {"sucessos": sucessos, "falhas_429": falhas, "tempo_total_ms": round(relogio)}


if __name__ == "__main__":
    N_REQUISICOES = 300  # mais que o limite por segundo: forcara 429s

    print(f"Enviando {N_REQUISICOES} requisicoes contra uma API de {LIMITE_RPS} rps...\n")

    resultado_ingenuo = cliente_ingenuo(ApiSimulada(), N_REQUISICOES)
    print("=== CLIENTE INGENUO ===")
    for chave, valor in resultado_ingenuo.items():
        print(f"- {chave}: {valor}")

    resultado_educado = cliente_respeitoso(ApiSimulada(), N_REQUISICOES)
    print("\n=== CLIENTE COM BUCKET + BACKOFF + JITTER ===")
    for chave, valor in resultado_educado.items():
        print(f"- {chave}: {valor}")

    if resultado_educado["sucessos"] > resultado_ingenuo["sucessos"]:
        ganho = resultado_educado["sucessos"] / max(resultado_ingenuo["sucessos"], 1)
        print(f"\nCliente educado entregou {ganho:.1f}x mais requisicoes bem-sucedidas.")
    print("Regra de ouro: respeite Retry-After, adicione jitter para nao sincronizar clientes.")
