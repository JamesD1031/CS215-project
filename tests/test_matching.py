from dmh_flow import bipartite_maximum_matching, edmonds_karp


def test_bipartite_maximum_matching_size() -> None:
    edges = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]
    res = bipartite_maximum_matching(3, 3, edges)
    assert res.size == 3


def test_bipartite_matching_with_edmonds_karp() -> None:
    edges = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]
    res = bipartite_maximum_matching(3, 3, edges, algo=edmonds_karp)
    assert res.size == 3
