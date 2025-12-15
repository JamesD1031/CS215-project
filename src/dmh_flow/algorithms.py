from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .network import FlowNetwork


@dataclass(slots=True)
class MaxFlowCounters:
    bfs_count: int = 0
    augment_count: int = 0
    phase_count: int = 0
    dfs_calls: int = 0
    bfs_edge_scans: int = 0
    dfs_edge_scans: int = 0
    edge_scans: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "bfs_count": self.bfs_count,
            "augment_count": self.augment_count,
            "phase_count": self.phase_count,
            "dfs_calls": self.dfs_calls,
            "bfs_edge_scans": self.bfs_edge_scans,
            "dfs_edge_scans": self.dfs_edge_scans,
            "edge_scans": self.edge_scans,
        }


@dataclass(slots=True)
class MaxFlowResult:
    flow_value: float
    counters: MaxFlowCounters


def edmonds_karp(network: FlowNetwork, source: int, sink: int) -> MaxFlowResult:
    if source == sink:
        raise ValueError("source and sink must be different")
    if not (0 <= source < network.num_nodes and 0 <= sink < network.num_nodes):
        raise IndexError("source and sink must be valid node indices")

    counters = MaxFlowCounters()
    flow = 0.0
    n = network.num_nodes

    while True:
        counters.bfs_count += 1
        parent: list[tuple[int, int] | None] = [None] * n
        q: deque[int] = deque([source])
        parent[source] = (source, -1)

        while q and parent[sink] is None:
            u = q.popleft()
            for edge_index, edge in enumerate(network.adj[u]):
                counters.bfs_edge_scans += 1
                counters.edge_scans += 1
                if edge.cap <= 0:
                    continue
                if parent[edge.to] is not None:
                    continue
                parent[edge.to] = (u, edge_index)
                if edge.to == sink:
                    break
                q.append(edge.to)

        if parent[sink] is None:
            break

        bottleneck = float("inf")
        v = sink
        while v != source:
            prev = parent[v]
            assert prev is not None
            u, edge_index = prev
            edge = network.adj[u][edge_index]
            if edge.cap < bottleneck:
                bottleneck = edge.cap
            v = u

        v = sink
        while v != source:
            prev = parent[v]
            assert prev is not None
            u, edge_index = prev
            edge = network.adj[u][edge_index]
            rev = network.adj[v][edge.rev]
            edge.cap -= bottleneck
            rev.cap += bottleneck
            v = u

        flow += bottleneck
        counters.augment_count += 1

    return MaxFlowResult(flow_value=flow, counters=counters)


def dinic(network: FlowNetwork, source: int, sink: int) -> MaxFlowResult:
    if source == sink:
        raise ValueError("source and sink must be different")
    if not (0 <= source < network.num_nodes and 0 <= sink < network.num_nodes):
        raise IndexError("source and sink must be valid node indices")

    counters = MaxFlowCounters()
    flow = 0.0
    n = network.num_nodes

    while True:
        counters.phase_count += 1
        counters.bfs_count += 1
        level = [-1] * n
        q: deque[int] = deque([source])
        level[source] = 0

        while q:
            u = q.popleft()
            for edge in network.adj[u]:
                counters.bfs_edge_scans += 1
                counters.edge_scans += 1
                if edge.cap <= 0:
                    continue
                if level[edge.to] != -1:
                    continue
                level[edge.to] = level[u] + 1
                q.append(edge.to)

        if level[sink] == -1:
            break

        it = [0] * n

        def dfs(u: int, pushed: float) -> float:
            counters.dfs_calls += 1
            if pushed <= 0:
                return 0.0
            if u == sink:
                return pushed

            while it[u] < len(network.adj[u]):
                i = it[u]
                edge = network.adj[u][i]
                counters.dfs_edge_scans += 1
                counters.edge_scans += 1
                if edge.cap > 0 and level[edge.to] == level[u] + 1:
                    tr = dfs(edge.to, min(pushed, edge.cap))
                    if tr > 0:
                        edge.cap -= tr
                        network.adj[edge.to][edge.rev].cap += tr
                        return tr
                it[u] += 1
            return 0.0

        while True:
            pushed = dfs(source, float("inf"))
            if pushed == 0:
                break
            flow += pushed

    return MaxFlowResult(flow_value=flow, counters=counters)
