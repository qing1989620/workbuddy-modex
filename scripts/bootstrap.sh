#!/usr/bin/env bash
# Bootstrap (Linux/macOS) - thin wrapper around the cross-platform CLI.
# Canonical logic lives in src/ommw. Installs uv if missing, syncs deps,
# installs the ommw console script, then defers to `ommw doctor`.
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found on PATH. Install Python 3.12+ first." >&2
  exit 1
fi
py_ver="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
py_major="${py_ver%%.*}"; py_minor="${py_ver##*.}"
if [ "$py_major" -lt 3 ] || { [ "$py_major" -eq 3 ] && [ "$py_minor" -lt 12 ]; }; then
  echo "Python $py_ver is too old; OMMW requires 3.12+." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv (user-scoped)..." >&2
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "Syncing dependencies (uv sync --frozen)..."
uv sync --frozen

echo "Installing ommw console script (editable)..."
uv pip install -e .

echo "Running ommw doctor..."
uv run ommw doctor
