"""Linhagem em nivel de coluna: arestas coluna->coluna com analise de impacto."""

from collections import defaultdict, deque


class LinhagemColuna:
    def __init__(self) -> None:
        # (tabela_origem, coluna_origem, tabela_destino, coluna_destino, transformacao)
        self.arestas: list[tuple[str, str, str, str, str]] = []

    def adicionar(
        self, origem: str, coluna_o: str, destino: str, coluna_d: str, transformacao: str = "pass-through"
    ) -> None:
        self.arestas.append((origem, coluna_o, destino, coluna_d, transformacao))

    def _grafo(self, direcao: int) -> dict[tuple[str, str], list[tuple[str, str, str]]]:
        grafo: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
        for t_o, c_o, t_d, c_d, transformacao in self.arestas:
            de = (t_o, c_o) if direcao > 0 else (t_d, c_d)
            para = ((t_d, c_d), transformacao) if direcao > 0 else ((t_o, c_o), transformacao)
            grafo[de].append(para)
        return grafo

    def _busca(self, tabela: str, coluna: str, direcao: int) -> dict[str, set[str]]:
        """Retorna {tabela: {colunas}} alcançáveis a partir da coluna informada."""
        grafo = self._grafo(direcao)
        visitados: dict[str, set[str]] = defaultdict(set)
        fila = deque([(tabela, coluna)])

        while fila:
            no_atual = fila.popleft()
            if no_atual not in grafo:
                continue
            for vizinho, _ in grafo[no_atual]:
                if vizinho[1] in visitados[vizinho[0]]:
                    continue
                visitados[vizinho[0]].add(vizinho[1])
                fila.append(vizinho)
        return visitados

    def impacto(self, tabela: str, coluna: str) -> dict[str, set[str]]:
        return self._busca(tabela, coluna, direcao=1)

    def origem(self, tabela: str, coluna: str) -> dict[str, set[str]]:
        return self._busca(tabela, coluna, direcao=-1)

    def mostrar_impacto(self, tabela: str, coluna: str) -> None:
        dependentes = self.impacto(tabela, coluna)
        print(f"Impacto de mudar {tabela}.{coluna}:")
        for tabela_dep, colunas in sorted(dependentes.items()):
            print(f"  - {tabela_dep}: {', '.join(sorted(colunas))}")
        if not dependentes:
            print("  - nenhuma dependencia")


if __name__ == "__main__":
    grafo = LinhagemColuna()

    # raw -> staging
    grafo.adicionar("raw_clientes", "id", "stg_clientes", "cliente_id", "rename")
    grafo.adicionar("raw_clientes", "nm_cliente", "stg_clientes", "nome", "trim + title")
    grafo.adicionar("raw_clientes", "cpf", "stg_clientes", "cpf_hash", "sha256")
    grafo.adicionar("raw_clientes", "vl_renda", "stg_clientes", "renda", "cast decimal")
    # staging -> fato
    grafo.adicionar("stg_clientes", "cliente_id", "ft_emprestimos", "cliente_id", "join")
    grafo.adicionar("stg_clientes", "renda", "ft_emprestimos", "renda_contratada", "pass-through")
    grafo.adicionar("stg_clientes", "renda", "ft_emprestimos", "divida_sobre_renda", "calculo")
    grafo.adicionar("stg_clientes", "cpf_hash", "dim_clientes", "sk_cpf", "surrogate key")
    # fato -> agregado do BI
    grafo.adicionar("ft_emprestimos", "divida_sobre_renda", "agg_risco_bi", "dsr_medio", "avg")
    grafo.adicionar("ft_emprestimos", "renda_contratada", "agg_risco_bi", "carteira_total", "sum")

    print("=== IMPACTO DE COLUNA ===")
    grafo.mostrar_impacto("raw_clientes", "vl_renda")

    print("\n=== ORIGEM DE COLUNA DO BI ===")
    fontes = grafo.origem("agg_risco_bi", "carteira_total")
    for tabela, colunas in fontes.items():
        print(f"- agg_risco_bi.carteira_total vem de {tabela}: {', '.join(colunas)}")

    cpf_afetado = grafo.impacto("raw_clientes", "cpf")
    tem_pii_downstream = any("cpf" in c or "sk_cpf" in c for cols in cpf_afetado.values() for c in cols)
    print(
        f"\nPII check — alterar raw_clientes.cpf toca dado sensivel? "
        f"{'SIM' if tem_pii_downstream else 'nao'} ({list(cpf_afetado.items())})"
    )
