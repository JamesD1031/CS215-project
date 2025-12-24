from dmh_flow import FlowNetwork, dinic, edmonds_karp, min_cut


def _build(num_nodes: int, edges: list[tuple[int, int, float]]) -> FlowNetwork:
    g = FlowNetwork(num_nodes)
    for u, v, c in edges:
        g.add_edge(u, v, c)
    return g


def test_min_cut_capacity_equals_max_flow_for_both_algorithms() -> None:
    edges = [(0, 1, 3), (0, 2, 2), (1, 2, 1), (1, 3, 2), (2, 3, 4)]

    g1 = _build(4, edges)
    ek = edmonds_karp(g1, 0, 3)
    cut1 = min_cut(g1, 0)
    assert cut1.cut_capacity == ek.flow_value

    g2 = _build(4, edges)
    di = dinic(g2, 0, 3)
    cut2 = min_cut(g2, 0)
    assert cut2.cut_capacity == di.flow_value
