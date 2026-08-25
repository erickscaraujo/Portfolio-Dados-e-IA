"""API simulada com paginacao por cursor: substituivel por qualquer REST real."""

import time


class ClienteApiEventos:
    """Entrega eventos ordenados por id crescente, paginados; imita cursor-based pagination."""

    def __init__(self, total_eventos: int = 500, page_size: int = 120) -> None:
        self.eventos = [
            {
                "id": i + 1,
                "tipo": "pedido_criado" if (i + 1) % 3 else "pagamento_confirmado",
                "valor": round(20 + ((i * 37) % 900) + i % 7 * 0.5, 2),
                "criado_em": f"2025-01-{1 + i % 28:02d}T{(i * 3) % 24:02d}:15:00",
            }
            for i in range(total_eventos)
        ]
        self.page_size = min(page_size, 200)
        self.chamadas = 0

    def listar_apos(self, ultimo_id: int) -> list[dict]:
        """Retorna uma pagina de eventos com id > ultimo_id."""
        self.chamadas += 1
        time.sleep(0.01)  # latencia de rede simulada
        inicio = next(
            (idx for idx, ev in enumerate(self.eventos) if ev["id"] > ultimo_id),
            len(self.eventos),
        )
        return self.eventos[inicio : inicio + self.page_size]
