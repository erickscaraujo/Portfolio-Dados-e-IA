"""Scheduler com heap: prioridade + aging contra inanicao."""

import heapq
import statistics
from collections import defaultdict
from itertools import count

TICKS_SIMULADOS = 400
CAPACIDADE_POR_TICK = 2
PESO_AGING = 0.05  # quanto a prioridade efetiva sobe por tick de espera

_DESEMPATE = count()  # garante ordem total na heap: nunca compara dois dicts


def gerar_jobs(seed: int = 230, total: int = 260) -> list[dict]:
    import random

    rng = random.Random(seed)
    jobs = []
    for i in range(total):
        classe = rng.choices(["alta", "media", "baixa"], weights=[0.2, 0.3, 0.5])[0]
        jobs.append(
            {
                "id": f"J{i:03d}",
                "classe": classe,
                "chegada": rng.randint(0, TICKS_SIMULADOS - 20),
                "duracao": rng.randint(1, 4),
                "prioridade": float({"alta": 10, "media": 5, "baixa": 1}[classe]),
            }
        )
    return sorted(jobs, key=lambda j: j["chegada"])


def executar(jobs: list[dict], modo: str) -> dict[str, list[int]]:
    """modos: 'fifo' | 'prioridade' | 'prioridade_aging'.

    Tupla da heap: (chave, desempate, job); a chave muda por modo.
    """
    assert modo in ("fifo", "prioridade", "prioridade_aging")
    usar_prioridade = modo != "fifo"
    com_aging = modo == "prioridade_aging"

    esperas: dict[str, list[int]] = defaultdict(list)
    fila: list[tuple] = []
    indice_chegada = 0

    def chave_de(job: dict, tick: int) -> float:
        if not usar_prioridade:
            return float(job["chegada"])  # FIFO: mais antigo primeiro
        base = -job["prioridade"]  # heap e min: negativo = maior prioridade
        if com_aging:
            base -= PESO_AGING * max(tick - job["chegada"], 0)
        return base

    em_execucao: list[tuple[float, int, dict]] = []

    for tick in range(TICKS_SIMULADOS):
        # devolve os que continuam em execucao com a chave atualizada
        for job in em_execucao:
            heapq.heappush(fila, (chave_de(job, tick), next(_DESEMPATE), job))
        em_execucao = []

        while indice_chegada < len(jobs) and jobs[indice_chegada]["chegada"] <= tick:
            job = jobs[indice_chegada]
            heapq.heappush(fila, (chave_de(job, tick), next(_DESEMPATE), job))
            indice_chegada += 1

        for _ in range(CAPACIDADE_POR_TICK):
            if not fila:
                break
            _, _, job = heapq.heappop(fila)
            job["duracao"] -= 1
            if job["duracao"] <= 0:
                esperas[job["classe"]].append(tick - job["chegada"])
            else:
                em_execucao.append(job)

    return esperas


def resumo(nome: str, esperas: dict[str, list[int]]) -> None:
    print(f"\n=== {nome} ===")
    todas = []
    for classe in ("alta", "media", "baixa"):
        valores = esperas.get(classe, [])
        todas.extend(valores)
        if valores:
            print(f"- {classe:<6} n={len(valores):>3} | p50={statistics.median(valores):>3.0f} max={max(valores):>3}")
    if todas:
        print(f"- max wait global: {max(todas)} ticks")


if __name__ == "__main__":
    jobs_originais = gerar_jobs()

    resumo("FIFO", executar([{**j} for j in jobs_originais], "fifo"))
    resumo("Prioridade SEM aging", executar([{**j} for j in jobs_originais], "prioridade"))
    resumo("Prioridade COM aging", executar([{**j} for j in jobs_originais], "prioridade_aging"))

    print("\nLeitura esperada: prioridade pura acelera 'alta' mas estoura o max da 'baixa';")
    print("com aging o max global volta a ficar contido (anti-starvation).")
