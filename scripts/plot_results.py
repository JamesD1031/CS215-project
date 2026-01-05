from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def _label(algo: str, p: float | None) -> str:
    if p is None:
        return algo
    return f"{algo} (p={p:g})"

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


def _spearman_rho(x: pd.Series, y: pd.Series) -> float:
    x_rank = x.rank(method="average")
    y_rank = y.rank(method="average")
    if len(x_rank) < 2:
        return float("nan")
    return float(np.corrcoef(x_rank.to_numpy(), y_rank.to_numpy())[0, 1])


def _load_seed_summary(exp_dir: Path) -> pd.DataFrame:
    seed_summary_path = exp_dir / "seed_summary.csv"
    if seed_summary_path.exists():
        return pd.read_csv(seed_summary_path)

    raw = pd.read_csv(exp_dir / "raw.csv")
    key_cols = ["exp", "graph_family", "n", "p", "seed", "algo", "layers", "width", "bipartite_n"]
    key_cols = [c for c in key_cols if c in raw.columns]
    grouped = (
        raw.groupby(key_cols, dropna=False)
        .agg(
            runtime_sec_median=("runtime_sec", "median"),
            edge_scans=("edge_scans", "first"),
            bfs_edge_scans=("bfs_edge_scans", "first"),
            dfs_edge_scans=("dfs_edge_scans", "first"),
        )
        .reset_index()
    )
    return grouped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp", required=True, help="Path to results/exp_<name> directory")
    parser.add_argument("--out", default="figs", help="Output directory for plots")
    args = parser.parse_args()

    exp_dir = Path(args.exp)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    seed_df = _load_seed_summary(exp_dir)
    exp_name = str(seed_df["exp"].iloc[0]) if "exp" in seed_df.columns and len(seed_df) else exp_dir.name.replace("exp_", "")

    families = sorted(set(seed_df["graph_family"].dropna().tolist()))

    group_cols = ["graph_family", "algo", "n", "p", "layers", "width", "bipartite_n"]
    group_cols = [c for c in group_cols if c in seed_df.columns]

    def agg_median_ci(series: pd.Series) -> tuple[float, float, float]:
        values = [float(x) for x in series.tolist() if pd.notna(x)]
        med = float(np.median(values)) if values else float("nan")
        low, high = _bootstrap_ci95_median(values, seed=0, num_resamples=2000)
        return (med, low, high)

    runtime_rows: list[dict] = []
    for key, grp in seed_df.groupby(group_cols, dropna=False):
        key_dict = dict(zip(group_cols, key, strict=False))
        med, low, high = agg_median_ci(grp["runtime_sec_median"])
        runtime_rows.append({**key_dict, "runtime_sec_median": med, "ci_low": low, "ci_high": high})
    runtime = pd.DataFrame(runtime_rows).sort_values(["graph_family", "p", "algo", "n"])

    fig, axes = plt.subplots(1, len(families), figsize=(6 * len(families), 4), squeeze=False)
    for ax, family in zip(axes[0], families):
        sub = runtime[runtime["graph_family"] == family]
        for (algo, p), grp in sub.groupby(["algo", "p"], dropna=False):
            p_val = None if pd.isna(p) else float(p)
            y = grp["runtime_sec_median"]
            yerr = [y - grp["ci_low"], grp["ci_high"] - y]
            ax.errorbar(grp["n"], y, yerr=yerr, marker="o", capsize=3, label=_label(str(algo), p_val))
        ax.set_title(f"{family}: runtime vs n")
        ax.set_xlabel("n (nodes)")
        ax.set_ylabel("runtime (sec)")
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    runtime_out = out_dir / f"exp_{exp_name}_runtime_vs_n.png"
    fig.savefig(runtime_out, dpi=200)
    plt.close(fig)

    scans_rows: list[dict] = []
    for key, grp in seed_df.groupby(group_cols, dropna=False):
        key_dict = dict(zip(group_cols, key, strict=False))
        values = [float(x) for x in grp["edge_scans"].tolist() if pd.notna(x)]
        med = float(np.median(values)) if values else float("nan")
        low, high = _bootstrap_ci95_median(values, seed=0, num_resamples=2000)
        scans_rows.append({**key_dict, "edge_scans_median": med, "ci_low": low, "ci_high": high})
    edge_scans = pd.DataFrame(scans_rows).sort_values(["graph_family", "p", "algo", "n"])

    fig, axes = plt.subplots(1, len(families), figsize=(6 * len(families), 4), squeeze=False)
    for ax, family in zip(axes[0], families):
        sub = edge_scans[edge_scans["graph_family"] == family]
        for (algo, p), grp in sub.groupby(["algo", "p"], dropna=False):
            p_val = None if pd.isna(p) else float(p)
            y = grp["edge_scans_median"]
            yerr = [y - grp["ci_low"], grp["ci_high"] - y]
            ax.errorbar(grp["n"], y, yerr=yerr, marker="o", capsize=3, label=_label(str(algo), p_val))
        ax.set_title(f"{family}: edge scans vs n")
        ax.set_xlabel("n (nodes)")
        ax.set_ylabel("edge_scans (median)")
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    scans_out = out_dir / f"exp_{exp_name}_edge_scans_vs_n.png"
    fig.savefig(scans_out, dpi=200)
    plt.close(fig)

    pivot_source = seed_df.copy()
    for col in ["layers", "width", "bipartite_n"]:
        if col in pivot_source.columns:
            pivot_source[col] = pivot_source[col].fillna(-1)

    pivot_cols = ["graph_family", "n", "p", "layers", "width", "bipartite_n", "seed"]
    pivot_cols = [c for c in pivot_cols if c in pivot_source.columns]
    pivot = pivot_source.pivot_table(index=pivot_cols, columns="algo", values="runtime_sec_median", aggfunc="first")
    pivot = pivot.dropna(subset=["edmonds_karp", "dinic"]).reset_index()
    pivot["speedup"] = pivot["edmonds_karp"] / pivot["dinic"]

    speedup_group_cols = [c for c in pivot_cols if c != "seed"]
    speedup_rows: list[dict] = []
    for key, grp in pivot.groupby(speedup_group_cols, dropna=False):
        key_dict = dict(zip(speedup_group_cols, key, strict=False))
        values = [float(x) for x in grp["speedup"].tolist() if pd.notna(x)]
        med = float(np.median(values)) if values else float("nan")
        low, high = _bootstrap_ci95_median(values, seed=0, num_resamples=2000)
        speedup_rows.append({**key_dict, "speedup_median": med, "ci_low": low, "ci_high": high})
    speedup = pd.DataFrame(speedup_rows).sort_values(["graph_family", "p", "n"])

    fig, axes = plt.subplots(1, len(families), figsize=(6 * len(families), 4), squeeze=False)
    for ax, family in zip(axes[0], families):
        sub = speedup[speedup["graph_family"] == family]
        for p, grp in sub.groupby("p", dropna=False):
            p_val = None if pd.isna(p) else float(p)
            y = grp["speedup_median"]
            yerr = [y - grp["ci_low"], grp["ci_high"] - y]
            ax.errorbar(grp["n"], y, yerr=yerr, marker="o", capsize=3, label=_label("speedup", p_val))
        ax.axhline(1.0, color="black", linewidth=1)
        ax.set_title(f"{family}: EK/Dinic speedup")
        ax.set_xlabel("n (nodes)")
        ax.set_ylabel("speedup")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    speedup_out = out_dir / f"exp_{exp_name}_speedup_vs_n.png"
    fig.savefig(speedup_out, dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, len(families), figsize=(6 * len(families), 4), squeeze=False)
    for ax, family in zip(axes[0], families):
        sub = seed_df[seed_df["graph_family"] == family].copy()
        sub = sub[pd.notna(sub["runtime_sec_median"]) & pd.notna(sub["edge_scans"])]
        for algo, grp in sub.groupby("algo", dropna=False):
            ax.scatter(grp["edge_scans"], grp["runtime_sec_median"], s=12, alpha=0.6, label=str(algo))

        rho = _spearman_rho(sub["edge_scans"], sub["runtime_sec_median"])
        ax.set_title(f"{family}: runtime vs edge_scans (Spearman ρ={rho:.2f})")
        ax.set_xlabel("edge_scans (per-seed median run)")
        ax.set_ylabel("runtime_sec_median")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    scatter_out = out_dir / f"exp_{exp_name}_runtime_vs_edge_scans.png"
    fig.savefig(scatter_out, dpi=200)
    plt.close(fig)

    print(f"Wrote plots to {out_dir}")
    print(f"- {runtime_out}")
    print(f"- {scans_out}")
    print(f"- {speedup_out}")
    print(f"- {scatter_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
