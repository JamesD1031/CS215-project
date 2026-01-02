from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import pandas as pd

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from dmh_flow import (
    FlowNetwork,
    MaxFlowResult,
    dinic,
    edmonds_karp,
    min_cut,
)
from dmh_flow.generators import (
    bipartite_graph_edges,
    erdos_renyi_digraph_edges,
    layered_digraph_edges,
)


def _build_network(num_nodes: int, edges: list[tuple[int, int, float]]) -> FlowNetwork:
    g = FlowNetwork(num_nodes)
    for u, v, c in edges:
        g.add_edge(u, v, c)
    return g


def _run_maxflow(algo: str, g: FlowNetwork, s: int, t: int) -> MaxFlowResult:
    if algo == "edmonds_karp":
        return edmonds_karp(g, s, t)
    if algo == "dinic":
        return dinic(g, s, t)
    raise ValueError(f"unknown algorithm: {algo}")

def _bootstrap_ci95_median(values: list[float], seed: int = 0, num_resamples: int = 2000) -> tuple[float, float]:
    if not values:
        return (float("nan"), float("nan"))
    if len(values) == 1:
        return (values[0], values[0])

    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    idx = rng.integers(0, len(arr), size=(num_resamples, len(arr)))
    samples = arr[idx]
    medians = np.median(samples, axis=1)
    low, high = np.quantile(medians, [0.025, 0.975])
    return (float(low), float(high))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to JSON config file")
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = json.loads(config_path.read_text())

    exp_name = str(cfg.get("exp_name", "exp"))
    output_dir = Path(cfg.get("output_dir", f"results/exp_{exp_name}"))
    seeds: list[int] = list(cfg["seeds"])
    repeats: int = int(cfg.get("repeats", 1))
    algorithms: list[str] = list(cfg["algorithms"])
    families: list[dict] = list(cfg["graph_families"])

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "config.json").write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")

    rows: list[dict] = []

    for family in families:
        family_name = family["name"]
        params = dict(family.get("params", {}))

        if family_name == "erdos_renyi":
            n_values = list(params["n_values"])
            p_values = list(params["p_values"])
            cap_max = int(params.get("cap_max", 20))
            for n in n_values:
                for p in p_values:
                    for seed in seeds:
                        rng = random.Random(seed)
                        edges = erdos_renyi_digraph_edges(rng, num_nodes=int(n), p=float(p), cap_max=cap_max)
                        s, t = 0, int(n) - 1
                        m = len(edges)

                        for algo in algorithms:
                            for repeat in range(repeats):
                                g = _build_network(int(n), edges)
                                start_ns = time.perf_counter_ns()
                                result = _run_maxflow(algo, g, s, t)
                                runtime_ns = time.perf_counter_ns() - start_ns
                                runtime_sec = runtime_ns / 1e9
                                cut = min_cut(g, s)
                                if cut.cut_capacity != result.flow_value:
                                    raise RuntimeError("max-flow != min-cut on generated graph")

                                rows.append(
                                    {
                                        "exp": exp_name,
                                        "graph_family": family_name,
                                        "n": int(n),
                                        "m": m,
                                        "p": float(p),
                                        "seed": int(seed),
                                        "algo": algo,
                                        "repeat": repeat,
                                        "flow_value": result.flow_value,
                                        "cut_capacity": cut.cut_capacity,
                                        "matching_size": None,
                                        "runtime_ns": runtime_ns,
                                        "runtime_sec": runtime_sec,
                                        **result.counters.as_dict(),
                                    }
                                )

        elif family_name == "layered":
            layers_values = list(params["layers_values"])
            width_values = list(params["width_values"])
            p = float(params.get("p", 0.3))
            cap_max = int(params.get("cap_max", 20))
            for layers in layers_values:
                for width in width_values:
                    for seed in seeds:
                        rng = random.Random(seed)
                        num_nodes, edges = layered_digraph_edges(
                            rng, layers=int(layers), width=int(width), p=p, cap_max=cap_max
                        )
                        s, t = 0, num_nodes - 1
                        m = len(edges)

                        for algo in algorithms:
                            for repeat in range(repeats):
                                g = _build_network(num_nodes, edges)
                                start_ns = time.perf_counter_ns()
                                result = _run_maxflow(algo, g, s, t)
                                runtime_ns = time.perf_counter_ns() - start_ns
                                runtime_sec = runtime_ns / 1e9
                                cut = min_cut(g, s)
                                if cut.cut_capacity != result.flow_value:
                                    raise RuntimeError("max-flow != min-cut on generated graph")

                                rows.append(
                                    {
                                        "exp": exp_name,
                                        "graph_family": family_name,
                                        "n": num_nodes,
                                        "m": m,
                                        "p": p,
                                        "seed": int(seed),
                                        "algo": algo,
                                        "repeat": repeat,
                                        "layers": int(layers),
                                        "width": int(width),
                                        "flow_value": result.flow_value,
                                        "cut_capacity": cut.cut_capacity,
                                        "matching_size": None,
                                        "runtime_ns": runtime_ns,
                                        "runtime_sec": runtime_sec,
                                        **result.counters.as_dict(),
                                    }
                                )

        elif family_name == "bipartite":
            n_values = list(params["n_values"])
            p_values = list(params["p_values"])
            for n in n_values:
                for p in p_values:
                    for seed in seeds:
                        rng = random.Random(seed)
                        bip_edges = bipartite_graph_edges(rng, num_left=int(n), num_right=int(n), p=float(p))
                        m = len(bip_edges)

                        for algo in algorithms:
                            algo_func = edmonds_karp if algo == "edmonds_karp" else dinic

                            num_left = int(n)
                            num_right = int(n)
                            source = 0
                            left_offset = 1
                            right_offset = left_offset + num_left
                            sink = right_offset + num_right

                            edges = []
                            for u in range(num_left):
                                edges.append((source, left_offset + u, 1.0))
                            for v in range(num_right):
                                edges.append((right_offset + v, sink, 1.0))
                            for u, v in bip_edges:
                                edges.append((left_offset + u, right_offset + v, 1.0))

                            for repeat in range(repeats):
                                g = _build_network(sink + 1, edges)
                                start_ns = time.perf_counter_ns()
                                result = algo_func(g, source, sink)
                                runtime_ns = time.perf_counter_ns() - start_ns
                                runtime_sec = runtime_ns / 1e9
                                cut = min_cut(g, source)
                                if cut.cut_capacity != result.flow_value:
                                    raise RuntimeError("max-flow != min-cut on generated bipartite network")

                                matching_size = 0
                                for u in range(num_left):
                                    node = left_offset + u
                                    for edge in g.adj[node]:
                                        if edge.original_cap != 1.0:
                                            continue
                                        if not (right_offset <= edge.to < sink):
                                            continue
                                        if edge.original_cap - edge.cap > 0.0:
                                            matching_size += 1

                                rows.append(
                                    {
                                        "exp": exp_name,
                                        "graph_family": family_name,
                                        "n": sink + 1,
                                        "m": len(edges),
                                        "p": float(p),
                                        "seed": int(seed),
                                        "algo": algo,
                                        "repeat": repeat,
                                        "bipartite_n": int(n),
                                        "flow_value": result.flow_value,
                                        "cut_capacity": cut.cut_capacity,
                                        "matching_size": matching_size,
                                        "runtime_ns": runtime_ns,
                                        "runtime_sec": runtime_sec,
                                        **result.counters.as_dict(),
                                    }
                                )

        else:
            raise ValueError(f"unknown graph family: {family_name}")

    df = pd.DataFrame(rows)
    raw_path = output_dir / "raw.csv"
    df.to_csv(raw_path, index=False)

    key_cols = ["exp", "graph_family", "n", "p", "seed", "algo", "layers", "width", "bipartite_n"]
    key_cols = [c for c in key_cols if c in df.columns]

    seed_summary = (
        df.groupby(key_cols, dropna=False)
        .agg(
            m=("m", "first"),
            repeats=("repeat", "nunique"),
            runtime_ns_median=("runtime_ns", "median"),
            runtime_ns_mean=("runtime_ns", "mean"),
            runtime_ns_std=("runtime_ns", "std"),
            flow_value=("flow_value", "first"),
            cut_capacity=("cut_capacity", "first"),
            matching_size=("matching_size", "first"),
            edge_scans=("edge_scans", "first"),
            bfs_edge_scans=("bfs_edge_scans", "first"),
            dfs_edge_scans=("dfs_edge_scans", "first"),
            bfs_count=("bfs_count", "first"),
            augment_count=("augment_count", "first"),
            phase_count=("phase_count", "first"),
            dfs_calls=("dfs_calls", "first"),
        )
        .reset_index()
    )
    seed_summary["runtime_sec_median"] = seed_summary["runtime_ns_median"] / 1e9
    seed_summary["runtime_sec_mean"] = seed_summary["runtime_ns_mean"] / 1e9
    seed_summary["runtime_sec_std"] = seed_summary["runtime_ns_std"] / 1e9
    seed_summary.to_csv(output_dir / "seed_summary.csv", index=False)

    group_cols = ["exp", "graph_family", "algo", "n", "p", "layers", "width", "bipartite_n"]
    group_cols = [c for c in group_cols if c in seed_summary.columns]

    summary = (
        seed_summary.groupby(group_cols, dropna=False)
        .agg(
            num_seeds=("seed", "nunique"),
            repeats=("repeats", "first"),
            m_mean=("m", "mean"),
            m_std=("m", "std"),
            runtime_sec_median=("runtime_sec_median", "median"),
            flow_value_mean=("flow_value", "mean"),
            matching_size_mean=("matching_size", "mean"),
            edge_scans_mean=("edge_scans", "mean"),
            bfs_edge_scans_mean=("bfs_edge_scans", "mean"),
            dfs_edge_scans_mean=("dfs_edge_scans", "mean"),
            bfs_count_mean=("bfs_count", "mean"),
            augment_count_mean=("augment_count", "mean"),
            phase_count_mean=("phase_count", "mean"),
            dfs_calls_mean=("dfs_calls", "mean"),
        )
        .reset_index()
    )

    ci = (
        seed_summary.groupby(group_cols, dropna=False)["runtime_sec_median"]
        .apply(lambda s: _bootstrap_ci95_median([float(x) for x in s.tolist() if pd.notna(x)], seed=0, num_resamples=2000))
        .apply(pd.Series)
        .rename(columns={0: "runtime_sec_median_ci95_low", 1: "runtime_sec_median_ci95_high"})
        .reset_index()
    )
    summary = summary.merge(ci, on=group_cols, how="left")
    summary.to_csv(output_dir / "summary.csv", index=False)

    print(f"Wrote {len(df)} rows to {raw_path}")
    print(f"Wrote {len(seed_summary)} rows to {output_dir / 'seed_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
