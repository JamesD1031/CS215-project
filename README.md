# CS215 Discrete Math Project: Max-Flow Algorithms (Edmonds–Karp vs Dinic)

This repository implements two maximum-flow algorithms from scratch (Edmonds–Karp and Dinic), plus:
- s–t min-cut extraction from the residual graph
- bipartite maximum matching via max-flow reduction

It also includes reproducible experiment sweeps and plotting scripts, producing artifacts under `results/` and `figs/`.

## Quickstart

Create a local virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest -q
```

Run experiments + plots (end-to-end):

```bash
python scripts/run_all.py --config scripts/configs/standard.json
```

## Outputs

- Experiment outputs: `results/exp_standard/` (`raw.csv`, `seed_summary.csv`, `summary.csv`, `config.json`)
- Figures (bootstrap CI error bars): `figs/exp_standard_runtime_vs_n.png`, `figs/exp_standard_edge_scans_vs_n.png`, `figs/exp_standard_speedup_vs_n.png`, `figs/exp_standard_runtime_vs_edge_scans.png`
- Report figures (generated): `figs/flowchart_dinic_main_loop.png`, `figs/flowchart_experiment_pipeline.png`, `figs/residual_min_cut.png`

## What’s in `scripts/`

- `scripts/run_all.py`: one command to run experiments + plots end-to-end
- `scripts/run_experiments.py`: generates graphs, runs algorithms, writes CSVs under `results/`
- `scripts/plot_results.py`: reads CSVs and writes plots under `figs/`
- `scripts/summarize_results.py`: prints the “Results at a glance” table used in `Report.md`
- `scripts/build_report_pdf.sh`: optional PDF build for the report (pandoc required)
- `scripts/make_submission.py`: builds a minimal submission zip under `dist/`
- `scripts/configs/standard.json`: experiment sweep configuration

## Build report PDF (optional)

This step requires `pandoc` plus a PDF engine. The simplest option on macOS is:

```bash
brew install pandoc tectonic
```

Then run:

```bash
./scripts/build_report_pdf.sh
```

Output: `Report.pdf`.

## Submission package

Create a minimal, deterministic submission zip (excludes local environment/caches and `results/exp_standard/raw.csv`):

```bash
python scripts/make_submission.py
```

Outputs: `dist/submission.zip` and `dist/MANIFEST.txt` (includes `Report.pdf` if present).

## Repo layout

- `src/` library code (flow network + algorithms + applications)
- `scripts/` experiment/plot runners
- `tests/` pytest suite
- `Report.md` final paper-style report
