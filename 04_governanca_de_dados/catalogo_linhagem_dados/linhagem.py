"""Grafo de linhagem (DAG simples) com busca de dependencias e analise de impacto."""

from collections import deque


class Linhagem:
    def __init__(self) -> None:
        # aresta: (origem, destino, transformacao que gerou o destino)
        self.arestas: list[tuple[str, str, str]] = []

    def adicionar(self, origem: str, destino: str, transformacao: str) -> None:
        self.arestas.append((origem, destino, transformacao))

    def _vizinhos(self, direcao: int) -> dict[str, list[str]]:
        grafo: dict[str, list[str]] = {}
        for origem, destino, _ in self.arestas:
            a, b = (origem, destino) if direcao > 0 else (destino, origem)
            grafo.setdefault(a, []).append(b)
        return grafo

    def _busca(self, tabela: str, direcao: int) -> list[str]:
        """BFS em largura; retorna dependentes (downstream) ou fontes (upstream)."""
        grafo = self._vizinhos(direcao)
        visitados: set[str] = set()
        fila = deque(grafo.get(tabela, []))
        while fila:
            no = fila.popleft()
            if no in visitados:
                continue
            visitados.add(no)
            fila.extend(grafo.get(no, []))
        return sorted(visitados)

    def downstream(self, tabela: str) -> list[str]:
        """Tabelas impactadas por uma mudanca na tabela informada."""
        return self._busca(tabela, direcao=1)

    def upstream(self, tabela: str) -> list[str]:
        return self._busca(tabela, direcao=-1)

    def mostrar_arvore(self, tabela: str, direcao: int = 1) -> str:
        prefixo = "dependentes" if direcao == 1 else "fontes"
        linhas = [f"{tabela}"]
        nivel_1 = self._vizinhos(direcao).get(tabela, [])
        for i, filho in enumerate(nivel_1):
            conector = "`-- " if i == len(nivel_1) - 1 else "|-- "
            linhas.append(f"{' ' * 4}{conector}{filho}")
            netos = self._vizinhos(direcao).get(filho, [])
            for j, neto in enumerate(netos):
                c2 = "`-- " if j == len(netos) - 1 else "|-- "
                espaco = "     " if i == len(nivel_1) - 1 else "|    "
                linhas.append(f"{' ' * 4}{espaco}{c2}{neto}")
        corpo = "\n".join(linhas) if len(linhas) > 1 else tabela
        return f"\n{prefixo.capitalize()} de {tabela}:\n{corpo}"
