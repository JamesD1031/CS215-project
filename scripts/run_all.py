from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to JSON config (used by run_experiments.py)")
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = json.loads(config_path.read_text())
    exp_dir = Path(cfg.get("output_dir", "results/exp_standard"))

    python = sys.executable
    _run([python, "scripts/run_experiments.py", "--config", str(config_path)])
    _run([python, "scripts/plot_results.py", "--exp", str(exp_dir), "--out", "figs"])
    _run([python, "scripts/render_flowcharts.py", "--out", "figs"])

    raw_csv = exp_dir / "raw.csv"
    if not raw_csv.exists() or raw_csv.stat().st_size == 0:
        raise RuntimeError(f"missing or empty: {raw_csv}")

    expected = [
        Path("figs") / f"exp_{cfg.get('exp_name', 'standard')}_runtime_vs_n.png",
        Path("figs") / f"exp_{cfg.get('exp_name', 'standard')}_edge_scans_vs_n.png",
        Path("figs") / f"exp_{cfg.get('exp_name', 'standard')}_speedup_vs_n.png",
        Path("figs") / f"exp_{cfg.get('exp_name', 'standard')}_runtime_vs_edge_scans.png",
        Path("figs") / "flowchart_dinic_main_loop.png",
        Path("figs") / "flowchart_experiment_pipeline.png",
        Path("figs") / "residual_min_cut.png",
    ]
    missing = [p for p in expected if not p.exists()]
    if missing:
        raise RuntimeError(f"missing expected plots: {missing}")

    print("OK: experiments and plots generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
