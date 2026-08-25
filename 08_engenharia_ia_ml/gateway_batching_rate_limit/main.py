"""Gateway de inferencia: token bucket (rate limit) + micro-batching de requisicoes."""

import numpy as np

TAXA_MAX_RPS = 500
JANELA_BATCH_MS = 8.0
LOTE_MAXIMO = 32

# custo do modelo: latencia base por chamada + incremento por item no lote
LATENCIA_BASE_MS = 12.0
LATENCIA_POR_ITEM_MS = 0.9


class TokenBucket:
    """Permite rajadas curtas ate o balde esvaziar; depois recusa com 429."""

    def __init__(self, taxa_rps: float, capacidade: float = 300) -> None:
        self.taxa = taxa_rps
        self.capacidade = capacidade
        self.tokens = capacidade
        self.recusados = 0

    def permitir(self, intervalo_desde_ultima_ms: float) -> bool:
        self.tokens = min(self.capacidade, self.tokens + self.taxa * intervalo_desde_ultima_ms / 1000)
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        self.recusados += 1
        return False


def simular_trafego(n_requisicoes: int = 3_000, seed: int = 95) -> list[float]:
    """Chegada em picos: rajadas seguidas de silencio (padrao real de dashboards)."""
    rng = np.random.default_rng(seed)
    intervalos = rng.choice([2.0, 5.0, 40.0], size=n_requisicoes - 1, p=[0.15, 0.55, 0.30])
    return [0.0] + np.cumsum(intervalos).tolist()


def processar(chegadas_ms: list[float], batching: bool) -> dict:
    balde = TokenBucket(TAXA_MAX_RPS)

    aceitas_ms: list[float] = []
    tamanhos_lote: list[int] = []

    if not batching:
        for i, chegada in enumerate(chegadas_ms):
            anterior = chegadas_ms[i - 1] if i else 0.0
            if not balde.permitir(anterior if i == 0 else chegada - anterior):
                continue
            # sem lote: cada request paga a chamada completa do modelo
            aceitas_ms.append(LATENCIA_BASE_MS + LATENCIA_POR_ITEM_MS)
    else:
        buffer: list[float] = []
        abertura_janela = 0.0
        for i, chegada in enumerate(chegadas_ms):
            anterior = chegadas_ms[i - 1] if i else 0.0
            if not balde.permitir(0.0 if i == 0 else chegada - anterior):
                continue
            buffer.append(i)
            if len(buffer) == 1:
                abertura_janela = chegada
            janela_cheia = (chegada - abertura_janela) >= JANELA_BATCH_MS
            if len(buffer) >= LOTE_MAXIMO or (janela_cheia and buffer):
                # espera media dentro da janela entra na latencia percebida
                espera_media = np.mean([chegadas_ms[j] - abertura_janela for j in buffer])
                latencia = LATENCIA_BASE_MS + LATENCIA_POR_ITEM_MS * len(buffer) + float(espera_media) / 10
                aceitas_ms.extend([latencia] * len(buffer))
                tamanhos_lote.append(len(buffer))
                buffer = []

    percentis = np.percentile(aceitas_ms, [50, 95, 99]) if aceitas_ms else [0, 0, 0]
    return {
        "aceitas": len(aceitas_ms),
        "recusadas": balde.recusados,
        "p50": round(float(percentis[0]), 2),
        "p95": round(float(percentis[1]), 2),
        "p99": round(float(percentis[2]), 2),
        "chamadas_modelo": len(tamanhos_lote) if batching else len(aceitas_ms),
    }


if __name__ == "__main__":
    chegadas = simular_trafego()
    print(f"Requisicoes simuladas: {len(chegadas)} em ~{chegadas[-1] / 1000:.1f}s (pico >> {TAXA_MAX_RPS} rps)\n")

    resultado_sem = processar(chegadas, batching=False)
    resultado_com = processar(chegadas, batching=True)

    print("=== SEM BATCHING ===")
    for chave, valor in resultado_sem.items():
        print(f"- {chave}: {valor}")

    print("\n=== COM MICRO-BATCHING (janela 8ms, lote max 32) ===")
    for chave, valor in resultado_com.items():
        print(f"- {chave}: {valor}")

    reducao = 1 - resultado_com["chamadas_modelo"] / max(resultado_sem["chamadas_modelo"], 1)
    print(
        f"\nChamadas ao modelo reduzidas em {reducao:.0%}; "
        f"p95 passou de {resultado_sem['p95']}ms para {resultado_com['p95']}ms."
    )
