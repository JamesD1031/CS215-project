from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Iterable

from .algorithms import MaxFlowResult, dinic
from .network import FlowNetwork


@dataclass(slots=True)
class MinCutResult:
    reachable: list[bool]
    cut_edges: list[tuple[int, int, float]]
    cut_capacity: float


def min_cut(network: FlowNetwork, source: int) -> MinCutResult:
    if not (0 <= source < network.num_nodes):
        raise IndexError("source must be a valid node index")

    reachable = [False] * network.num_nodes
    q: deque[int] = deque([source])
    reachable[source] = True

    while q:
        u = q.popleft()
        for edge in network.adj[u]:
            if edge.cap <= 0:
                continue
            if reachable[edge.to]:
                continue
            reachable[edge.to] = True
            q.append(edge.to)

    cut_edges: list[tuple[int, int, float]] = []
    cut_capacity = 0.0
    for u, edges in enumerate(network.adj):
        if not reachable[u]:
            continue
        for edge in edges:
            if edge.original_cap <= 0:
                continue
            if reachable[edge.to]:
                continue
            cut_edges.append((u, edge.to, edge.original_cap))
            cut_capacity += edge.original_cap

    return MinCutResult(reachable=reachable, cut_edges=cut_edges, cut_capacity=cut_capacity)


MaxFlowFunc = Callable[[FlowNetwork, int, int], MaxFlowResult]


@dataclass(slots=True)
class BipartiteMatchingResult:
    matching: list[tuple[int, int]]
    size: int
    flow_result: MaxFlowResult


def bipartite_maximum_matching(
    num_left: int,
    num_right: int,
    edges: Iterable[tuple[int, int]],
    algo: MaxFlowFunc = dinic,
) -> BipartiteMatchingResult:
    if num_left < 0 or num_right < 0:
        raise ValueError("num_left and num_right must be non-negative")

    source = 0
    left_offset = 1
    right_offset = left_offset + num_left
    sink = right_offset + num_right
    network = FlowNetwork(sink + 1)

    for u in range(num_left):
        network.add_edge(source, left_offset + u, 1.0)
    for v in range(num_right):
        network.add_edge(right_offset + v, sink, 1.0)

    for u, v in edges:
        if not (0 <= u < num_left and 0 <= v < num_right):
            raise IndexError("bipartite edge endpoint out of range")
        network.add_edge(left_offset + u, right_offset + v, 1.0)

    flow_result = algo(network, source, sink)

    matching: list[tuple[int, int]] = []
    for u in range(num_left):
        node = left_offset + u
        for edge in network.adj[node]:
            if edge.original_cap != 1.0:
                continue
            if not (right_offset <= edge.to < sink):
                continue
            sent = edge.original_cap - edge.cap
            if sent > 0.0:
                matching.append((u, edge.to - right_offset))

    return BipartiteMatchingResult(matching=matching, size=len(matching), flow_result=flow_result)
