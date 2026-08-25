"""Mini orquestrador: DAG topologico com retries, status e bloqueio de dependentes."""

import logging
import time
from collections import deque
from collections.abc import Callable

logger = logging.getLogger(__name__)

PENDENTE = "pendente"
SUCESSO = "sucesso"
FALHA = "falha"
IGNORADA = "ignorada"


class Tarefa:
    def __init__(
        self,
        nome: str,
        funcao: Callable[[], object],
        dependencias: list[str] | None = None,
        max_tentativas: int = 1,
    ) -> None:
        self.nome = nome
        self.funcao = funcao
        self.dependencias = dependencias or []
        self.max_tentativas = max_tentativas
        self.status = PENDENTE
        self.erro: Exception | None = None


class Orquestrador:
    def __init__(self) -> None:
        self.tarefas: dict[str, Tarefa] = {}

    def adicionar(self, tarefa: Tarefa) -> None:
        if any(dep not in self.tarefas and dep != tarefa.nome for dep in tarefa.dependencias):
            raise ValueError(f"dependencia ainda nao registrada para '{tarefa.nome}'")
        self.tarefas[tarefa.nome] = tarefa

    def _ordem_topologica(self) -> list[str]:
        """Kahn; falha cedo se houver ciclo no DAG."""
        grau = {nome: len(t.dependencias) for nome, t in self.tarefas.items()}
        fila = deque(nome for nome, g in grau.items() if g == 0)
        ordem: list[str] = []
        while fila:
            atual = fila.popleft()
            ordem.append(atual)
            for nome, tarefa in self.tarefas.items():
                if atual in tarefa.dependencias:
                    grau[nome] -= 1
                    if grau[nome] == 0:
                        fila.append(nome)
        if len(ordem) != len(self.tarefas):
            ciclicas = sorted(set(self.tarefas) - set(ordem))
            raise ValueError(f"ciclo detectado envolvendo: {', '.join(ciclicas)}")
        return ordem

    def executar(self) -> dict[str, str]:
        for nome in self._ordem_topologica():
            tarefa = self.tarefas[nome]
            pais_falhos = [d for d in tarefa.dependencias if self.tarefas[d].status != SUCESSO]
            if pais_falhos:
                tarefa.status = IGNORADA
                logger.warning("'%s' ignorada: depende de %s", nome, ", ".join(pais_falhos))
                continue

            for tentativa in range(1, tarefa.max_tentativas + 1):
                inicio = time.perf_counter()
                try:
                    tarefa.funcao()
                except Exception as erro:  # noqa: BLE001 - orquestrador isola qualquer falha da task
                    tarefa.erro = erro
                    espera = 0.2 * tentativa
                    logger.error(
                        "'%s' falhou na tentativa %d/%d (%s); retry em %.1fs",
                        nome,
                        tentativa,
                        tarefa.max_tentativas,
                        erro,
                        espera,
                    )
                    time.sleep(espera)
                else:
                    duracao = time.perf_counter() - inicio
                    tarefa.status = SUCESSO
                    logger.info("'%s' concluida em %.3fs", nome, duracao)
                    break
            else:
                tarefa.status = FALHA

        return {nome: tarefa.status for nome, tarefa in self.tarefas.items()}

    def resumo(self) -> str:
        linhas = [f"{'tarefa':<18} status"]
        for nome, tarefa in self.tarefas.items():
            detalhe = f" ({tarefa.erro})" if tarefa.erro and tarefa.status == FALHA else ""
            linhas.append(f"{nome:<18} {tarefa.status}{detalhe}")
        return "\n".join(linhas)
