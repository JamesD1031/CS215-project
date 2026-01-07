from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


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


def summarize_best_speedups(exp_dir: Path) -> pd.DataFrame:
    seed_summary_path = exp_dir / "seed_summary.csv"
    if not seed_summary_path.exists():
        raise FileNotFoundError(f"missing: {seed_summary_path}")

    df = pd.read_csv(seed_summary_path)

    for col in ["layers", "width", "bipartite_n"]:
        if col in df.columns:
            df[col] = df[col].fillna(-1)

    idx_cols = ["graph_family", "n", "p", "layers", "width", "bipartite_n", "seed"]
    idx_cols = [c for c in idx_cols if c in df.columns]

    pivot = df.pivot_table(index=idx_cols, columns="algo", values="runtime_sec_median", aggfunc="first").dropna()
    if "edmonds_karp" not in pivot.columns or "dinic" not in pivot.columns:
        raise RuntimeError("seed_summary.csv missing required algo columns for paired speedup")

    pivot = pivot.reset_index()
    pivot["speedup"] = pivot["edmonds_karp"] / pivot["dinic"]

    group_cols = [c for c in idx_cols if c != "seed"]
    rows: list[dict] = []
    for key, grp in pivot.groupby(group_cols, dropna=False):
        key_dict = dict(zip(group_cols, key, strict=False))
        values = [float(x) for x in grp["speedup"].tolist() if pd.notna(x)]
        med = float(np.median(values)) if values else float("nan")
        low, high = _bootstrap_ci95_median(values, seed=0, num_resamples=2000)
        rows.append({**key_dict, "num_seeds": len(values), "speedup_median": med, "ci95_low": low, "ci95_high": high})

    per_setting = pd.DataFrame(rows)
    best = per_setting.sort_values(["graph_family", "speedup_median"], ascending=[True, False]).groupby("graph_family").head(1)
    return best.sort_values("graph_family")


def _fmt_param(value: float | int | None) -> str:
    if value is None:
        return "-"
    try:
        if float(value) < 0:
            return "-"
    except Exception:
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp", required=True, help="Path to results/exp_<name> directory")
    args = parser.parse_args()

    exp_dir = Path(args.exp)
    best = summarize_best_speedups(exp_dir)

    cols = ["graph_family", "n", "p", "layers", "width", "bipartite_n", "speedup_median", "ci95_low", "ci95_high", "num_seeds"]
    cols = [c for c in cols if c in best.columns]
    best = best[cols]

    print("| family | n | p | layers | width | bipartite_n | speedup_median (95% CI) | seeds |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for _, row in best.iterrows():
        family = str(row["graph_family"])
        n = int(row["n"])
        p = float(row["p"])
        layers = _fmt_param(row.get("layers"))
        width = _fmt_param(row.get("width"))
        bip_n = _fmt_param(row.get("bipartite_n"))
        med = float(row["speedup_median"])
        low = float(row["ci95_low"])
        high = float(row["ci95_high"])
        seeds = int(row["num_seeds"])
        print(f"| {family} | {n} | {p:g} | {layers} | {width} | {bip_n} | {med:.2f} [{low:.2f}, {high:.2f}] | {seeds} |")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
