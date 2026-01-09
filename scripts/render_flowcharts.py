#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch


@dataclass(frozen=True)
class Box:
    cx: float
    cy: float
    w: float
    h: float
    text: str

    @property
    def left(self) -> float:
        return self.cx - self.w / 2

    @property
    def right(self) -> float:
        return self.cx + self.w / 2

    @property
    def bottom(self) -> float:
        return self.cy - self.h / 2

    @property
    def top(self) -> float:
        return self.cy + self.h / 2


def _new_figure(*, figsize: tuple[float, float]) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _draw_box(ax: plt.Axes, box: Box, *, fc: str = "#F7FAFC", ec: str = "#1F2937") -> None:
    patch = FancyBboxPatch(
        (box.left, box.bottom),
        box.w,
        box.h,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        linewidth=1.2,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(
        box.cx,
        box.cy,
        box.text,
        ha="center",
        va="center",
        fontsize=10,
        color="#111827",
        wrap=True,
    )


def _arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    label: str | None = None,
    label_xy: tuple[float, float] | None = None,
    rad: float = 0.0,
    color: str = "#111827",
    lw: float = 1.2,
) -> None:
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=lw,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(patch)
    if label:
        lx, ly = label_xy if label_xy is not None else ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        ax.text(lx, ly, label, ha="center", va="center", fontsize=9, color=color)


def render_dinic_main_loop(out_dir: Path) -> Path:
    fig, ax = _new_figure(figsize=(9.5, 4.8))

    init = Box(0.18, 0.78, 0.26, 0.14, "Initialize\nflow = 0")
    bfs = Box(0.50, 0.78, 0.34, 0.14, "BFS: build level graph\n(from residual graph)")
    stop = Box(0.82, 0.78, 0.26, 0.14, "Stop:\ncurrent flow is maximum")
    dfs = Box(0.50, 0.50, 0.40, 0.14, "DFS: send blocking flow\n(on level graph)")
    update = Box(0.50, 0.22, 0.34, 0.14, "Update residual\ncapacities")

    for b in [init, bfs, stop, dfs, update]:
        _draw_box(ax, b)

    _arrow(ax, (init.right, init.cy), (bfs.left, bfs.cy))
    _arrow(ax, (bfs.right, bfs.cy + 0.03), (stop.left, stop.cy + 0.03), label="t unreachable", label_xy=(0.66, 0.88))
    _arrow(ax, (bfs.cx, bfs.bottom), (dfs.cx, dfs.top), label="t reachable", label_xy=(0.58, 0.64))
    _arrow(ax, (dfs.cx, dfs.bottom), (update.cx, update.top))
    _arrow(
        ax,
        (update.right, update.cy),
        (bfs.right, bfs.cy - 0.02),
        rad=0.45,
    )

    ax.set_title("Dinic algorithm main loop", fontsize=12, pad=12)

    out_path = out_dir / "flowchart_dinic_main_loop.png"
    fig.savefig(out_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return out_path


def render_experiment_pipeline(out_dir: Path) -> Path:
    fig, ax = _new_figure(figsize=(10.5, 2.9))

    boxes = [
        Box(0.08, 0.55, 0.16, 0.18, "Implement\nalgorithms"),
        Box(0.24, 0.55, 0.16, 0.18, "Write tests\n+ checks"),
        Box(0.40, 0.55, 0.16, 0.18, "Generate graphs\n(fixed seeds)"),
        Box(0.56, 0.55, 0.16, 0.18, "Run benchmarks\n(repeats)"),
        Box(0.72, 0.55, 0.16, 0.18, "Summarize\n+ plot"),
        Box(0.88, 0.55, 0.16, 0.18, "Write report\n+ figures"),
    ]

    for b in boxes:
        _draw_box(ax, b, fc="#F0F9FF", ec="#0F172A")

    for a, b in zip(boxes, boxes[1:]):
        _arrow(ax, (a.right, a.cy), (b.left, b.cy))

    ax.set_title("Experiment workflow (reproducible end-to-end)", fontsize=12, pad=12)

    out_path = out_dir / "flowchart_experiment_pipeline.png"
    fig.savefig(out_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _node(ax: plt.Axes, xy: tuple[float, float], label: str) -> None:
    circle = Circle(xy, radius=0.06, facecolor="#FFFFFF", edgecolor="#111827", linewidth=1.2)
    ax.add_patch(circle)
    ax.text(xy[0], xy[1], label, ha="center", va="center", fontsize=11, color="#111827")


def _edge(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    label: str,
    *,
    color: str = "#111827",
    lw: float = 1.4,
    label_offset: tuple[float, float] = (0.0, 0.0),
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=lw,
        color=color,
        shrinkA=10,
        shrinkB=10,
    )
    ax.add_patch(arrow)
    mx = (start[0] + end[0]) / 2 + label_offset[0]
    my = (start[1] + end[1]) / 2 + label_offset[1]
    ax.text(mx, my, label, fontsize=9, color=color, ha="center", va="center")


def render_residual_min_cut(out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.axis("off")
    ax.set_xlim(-0.1, 2.2)
    ax.set_ylim(-0.2, 1.3)

    s = (0.0, 0.9)
    u = (1.0, 0.9)
    v = (1.0, 0.2)
    t = (2.0, 0.9)

    for xy, lbl in [(s, "s"), (u, "u"), (v, "v"), (t, "t")]:
        _node(ax, xy, lbl)

    _edge(ax, s, u, "c=5, f=3", label_offset=(0.0, 0.12))
    _edge(ax, s, v, "c=4, f=4", label_offset=(-0.10, 0.0))
    _edge(ax, u, t, "c=3, f=1", label_offset=(0.0, 0.12))
    _edge(ax, v, t, "c=2, f=2", label_offset=(0.0, -0.12))
    _edge(ax, u, v, "c=2, f=2", label_offset=(0.12, 0.0))

    # Highlight an example augmenting path.
    _edge(ax, s, u, "", color="#DC2626", lw=3.0)
    _edge(ax, u, t, "", color="#DC2626", lw=3.0)
    ax.text(1.0, 1.15, "Example augmenting path", color="#DC2626", fontsize=10, ha="center")

    ax.set_title("Residual network illustration (capacities and flow)", fontsize=12, pad=10)

    out_path = out_dir / "residual_min_cut.png"
    fig.savefig(out_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render report flowcharts as PNGs (matplotlib only).")
    parser.add_argument("--out", default="figs", help="Output directory (default: figs)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = [
        render_dinic_main_loop(out_dir),
        render_experiment_pipeline(out_dir),
        render_residual_min_cut(out_dir),
    ]
    for p in paths:
        print(f"Wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
