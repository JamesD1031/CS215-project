from dmh_flow import FlowNetwork, dinic, edmonds_karp


def _build(num_nodes: int, edges: list[tuple[int, int, float]]) -> FlowNetwork:
    g = FlowNetwork(num_nodes)
    for u, v, c in edges:
        g.add_edge(u, v, c)
    return g


def test_small_known_graph_flow_value() -> None:
    edges = [(0, 1, 3), (0, 2, 2), (1, 2, 1), (1, 3, 2), (2, 3, 4)]
    expected = 5.0

    ek = edmonds_karp(_build(4, edges), 0, 3)
    di = dinic(_build(4, edges), 0, 3)

    assert ek.flow_value == expected
    assert di.flow_value == expected


def test_single_path_flow_value() -> None:
    edges = [(0, 1, 5), (1, 2, 2), (2, 3, 7)]
    expected = 2.0

    ek = edmonds_karp(_build(4, edges), 0, 3)
    di = dinic(_build(4, edges), 0, 3)

    assert ek.flow_value == expected
    assert di.flow_value == expected
