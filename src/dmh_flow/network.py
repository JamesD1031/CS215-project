from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Edge:
    to: int
    rev: int
    cap: float
    original_cap: float


class FlowNetwork:
    def __init__(self, num_nodes: int) -> None:
        if num_nodes <= 0:
            raise ValueError("num_nodes must be positive")
        self._n = num_nodes
        self._adj: list[list[Edge]] = [[] for _ in range(num_nodes)]

    @property
    def num_nodes(self) -> int:
        return self._n

    @property
    def adj(self) -> list[list[Edge]]:
        return self._adj

    def add_edge(self, u: int, v: int, capacity: float) -> None:
        if not (0 <= u < self._n and 0 <= v < self._n):
            raise IndexError("u and v must be valid node indices")
        if u == v:
            raise ValueError("self-loops are not supported in FlowNetwork")
        if capacity < 0:
            raise ValueError("capacity must be non-negative")

        rev_index_for_forward = len(self._adj[v])
        rev_index_for_reverse = len(self._adj[u])

        forward = Edge(to=v, rev=rev_index_for_forward, cap=capacity, original_cap=capacity)
        reverse = Edge(to=u, rev=rev_index_for_reverse, cap=0.0, original_cap=0.0)

        self._adj[u].append(forward)
        self._adj[v].append(reverse)

    def iter_original_edges(self) -> list[tuple[int, Edge]]:
        original: list[tuple[int, Edge]] = []
        for u, edges in enumerate(self._adj):
            for e in edges:
                if e.original_cap > 0:
                    original.append((u, e))
        return original
