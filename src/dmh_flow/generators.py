from __future__ import annotations

import random


def erdos_renyi_digraph_edges(
    rng: random.Random,
    num_nodes: int,
    p: float,
    cap_max: int,
) -> list[tuple[int, int, float]]:
    if num_nodes <= 0:
        raise ValueError("num_nodes must be positive")
    if not (0.0 <= p <= 1.0):
        raise ValueError("p must be in [0, 1]")
    if cap_max <= 0:
        raise ValueError("cap_max must be positive")

    edges: list[tuple[int, int, float]] = []
    for u in range(num_nodes):
        for v in range(num_nodes):
            if u == v:
                continue
            if rng.random() < p:
                edges.append((u, v, float(rng.randint(1, cap_max))))
    return edges


def layered_digraph_edges(
    rng: random.Random,
    layers: int,
    width: int,
    p: float,
    cap_max: int,
) -> tuple[int, list[tuple[int, int, float]]]:
    if layers <= 0:
        raise ValueError("layers must be positive")
    if width <= 0:
        raise ValueError("width must be positive")
    if not (0.0 <= p <= 1.0):
        raise ValueError("p must be in [0, 1]")
    if cap_max <= 0:
        raise ValueError("cap_max must be positive")

    source = 0
    first_layer = 1
    sink = 1 + layers * width
    num_nodes = sink + 1

    edges: list[tuple[int, int, float]] = []

    for i in range(width):
        edges.append((source, first_layer + i, float(rng.randint(1, cap_max))))
    last_layer = first_layer + (layers - 1) * width
    for i in range(width):
        edges.append((last_layer + i, sink, float(rng.randint(1, cap_max))))

    for layer in range(layers - 1):
        base_u = first_layer + layer * width
        base_v = first_layer + (layer + 1) * width
        for i in range(width):
            u = base_u + i
            for j in range(width):
                v = base_v + j
                if rng.random() < p:
                    edges.append((u, v, float(rng.randint(1, cap_max))))

    return num_nodes, edges


def bipartite_graph_edges(
    rng: random.Random,
    num_left: int,
    num_right: int,
    p: float,
) -> list[tuple[int, int]]:
    if num_left < 0 or num_right < 0:
        raise ValueError("num_left and num_right must be non-negative")
    if not (0.0 <= p <= 1.0):
        raise ValueError("p must be in [0, 1]")

    edges: list[tuple[int, int]] = []
    for u in range(num_left):
        for v in range(num_right):
            if rng.random() < p:
                edges.append((u, v))
    return edges
