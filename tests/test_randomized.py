import random

import pytest

from dmh_flow import FlowNetwork, dinic, edmonds_karp, min_cut


def _random_digraph_edges(
    rng: random.Random, n: int, p: float, cap_max: int
) -> list[tuple[int, int, int]]:
    edges: list[tuple[int, int, int]] = []
    for u in range(n):
        for v in range(n):
            if u == v:
                continue
            if rng.random() < p:
                edges.append((u, v, rng.randint(1, cap_max)))
    return edges


def _build(num_nodes: int, edges: list[tuple[int, int, int]]) -> FlowNetwork:
    g = FlowNetwork(num_nodes)
    for u, v, c in edges:
        g.add_edge(u, v, float(c))
    return g


def test_randomized_ek_equals_dinic_and_matches_min_cut() -> None:
    for seed in range(10):
        rng = random.Random(seed)
        n = 7
        edges = _random_digraph_edges(rng, n=n, p=0.25, cap_max=8)
        s, t = 0, n - 1

        g1 = _build(n, edges)
        ek = edmonds_karp(g1, s, t)
        cut1 = min_cut(g1, s)
        assert ek.flow_value == cut1.cut_capacity

        g2 = _build(n, edges)
        di = dinic(g2, s, t)
        cut2 = min_cut(g2, s)
        assert di.flow_value == cut2.cut_capacity

        assert ek.flow_value == di.flow_value


def test_against_networkx_when_available() -> None:
    nx = pytest.importorskip("networkx")

    for seed in range(5):
        rng = random.Random(seed)
        n = 8
        edges = _random_digraph_edges(rng, n=n, p=0.2, cap_max=10)
        s, t = 0, n - 1

        G = nx.DiGraph()
        G.add_nodes_from(range(n))
        for u, v, c in edges:
            if G.has_edge(u, v):
                G[u][v]["capacity"] += c
            else:
                G.add_edge(u, v, capacity=c)

        nx_flow = float(nx.maximum_flow_value(G, s, t, capacity="capacity"))

        ek = edmonds_karp(_build(n, edges), s, t)
        di = dinic(_build(n, edges), s, t)

        assert ek.flow_value == nx_flow
        assert di.flow_value == nx_flow
