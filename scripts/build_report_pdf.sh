#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "ERROR: pandoc is not installed." >&2
  echo "Install with: brew install pandoc" >&2
  exit 1
fi

PDF_ENGINE=""
if command -v tectonic >/dev/null 2>&1; then
  PDF_ENGINE="tectonic"
elif command -v xelatex >/dev/null 2>&1; then
  PDF_ENGINE="xelatex"
elif command -v pdflatex >/dev/null 2>&1; then
  PDF_ENGINE="pdflatex"
fi

if [[ -z "$PDF_ENGINE" ]]; then
  echo "ERROR: no PDF engine found for pandoc." >&2
  echo "Recommended: brew install tectonic" >&2
  echo "Alternative: install a LaTeX distribution (e.g., MacTeX) to provide xelatex/pdflatex." >&2
  exit 1
fi

echo "Building Report.pdf using pandoc + $PDF_ENGINE..."
pandoc "Report.md" \
  --from=gfm \
  --pdf-engine="$PDF_ENGINE" \
  --output="Report.pdf"

echo "Wrote Report.pdf"
