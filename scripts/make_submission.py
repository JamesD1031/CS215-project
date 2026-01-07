#!/usr/bin/env python3
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

FIXED_ZIP_DATETIME = (2020, 1, 1, 0, 0, 0)

# Project submission allowlist (repo-root relative).
ALLOWLIST = [
    "Report.md",
    "README.md",
    "requirements.txt",
    "CS215project(1).pdf",
    # Optional artifact: built via scripts/build_report_pdf.sh (if present).
    # (Included conditionally; see OPTIONAL_ALLOWLIST below.)
    "src",
    "scripts",
    "tests",
    "results/exp_standard/config.json",
    "results/exp_standard/summary.csv",
    "results/exp_standard/seed_summary.csv",
    "figs/exp_standard_*.png",
    "figs/flowchart_*.png",
    "figs/residual_min_cut.png",
]

OPTIONAL_ALLOWLIST = [
    "Report.pdf",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def should_skip(rel_posix: str) -> bool:
    parts = rel_posix.split("/")
    if any(
        part in {".git", ".venv", ".pytest_cache", "__pycache__", "plan", "issues", "dist"}
        for part in parts
    ):
        return True
    if rel_posix.endswith((".pyc", ".pyo")):
        return True
    if rel_posix.endswith(".DS_Store"):
        return True
    if rel_posix == "results/exp_standard/raw.csv":
        return True
    return False


def iter_files_under(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise FileNotFoundError(path)
    return [p for p in path.rglob("*") if p.is_file()]


def build_file_list(root: Path) -> list[Path]:
    rel_to_abs: dict[str, Path] = {}

    def add_allow_entry(entry: str, *, required: bool) -> None:
        if any(ch in entry for ch in "*?[]"):
            matches = sorted(root.glob(entry))
            if not matches and required:
                raise FileNotFoundError(f"No matches for allowlist pattern: {entry}")
            if not matches and not required:
                return
            for match in matches:
                for p in iter_files_under(match):
                    rel = p.relative_to(root).as_posix()
                    if should_skip(rel):
                        continue
                    rel_to_abs.setdefault(rel, p)
            return

        p = root / entry
        if not p.exists() and required:
            raise FileNotFoundError(f"Missing required path: {entry}")
        if not p.exists() and not required:
            return
        for f in iter_files_under(p):
            rel = f.relative_to(root).as_posix()
            if should_skip(rel):
                continue
            rel_to_abs.setdefault(rel, f)

    for entry in ALLOWLIST:
        add_allow_entry(entry, required=True)

    for entry in OPTIONAL_ALLOWLIST:
        add_allow_entry(entry, required=False)

    return [rel_to_abs[rel] for rel in sorted(rel_to_abs)]


def write_zip(zip_path: Path, root: Path, files: list[Path]) -> list[str]:
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    names: list[str] = []
    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as zf:
        for f in files:
            rel = f.relative_to(root).as_posix()
            info = zipfile.ZipInfo(rel, date_time=FIXED_ZIP_DATETIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 & 0xFFFF) << 16
            zf.writestr(info, f.read_bytes())
            names.append(rel)

    return names


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a minimal, deterministic submission zip under dist/ using an allowlist."
        )
    )
    parser.add_argument("--out", default="dist/submission.zip", help="Zip output path")
    parser.add_argument(
        "--manifest", default="dist/MANIFEST.txt", help="Manifest output path"
    )
    args = parser.parse_args()

    root = repo_root()
    zip_path = Path(args.out)
    if not zip_path.is_absolute():
        zip_path = root / zip_path
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path

    files = build_file_list(root)
    names = write_zip(zip_path, root, files)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(names) + "\n", encoding="utf-8")

    print(f"Wrote {zip_path.relative_to(root)} ({len(names)} files)")
    print(f"Wrote {manifest_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
