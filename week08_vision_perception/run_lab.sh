#!/usr/bin/env bash
set -e
LAB7_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$LAB7_ROOT/.venv/bin/python" ]]; then
  chosen=""
  for candidate in python3.14 python3.13 python3.12 python3; do
    if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)'; then
      chosen="$candidate"
      break
    fi
  done
  if [[ -z "$chosen" ]]; then echo "Install Python 3.12 or newer first."; exit 1; fi
  "$chosen" -m venv "$LAB7_ROOT/.venv"
fi
PYTHON="$LAB7_ROOT/.venv/bin/python"
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else "The lab virtual environment needs Python 3.12 or newer. Preserve submissions before replacing only .venv.")'
"$PYTHON" -m pip install -r "$LAB7_ROOT/requirements.txt"
exec "$PYTHON" -m streamlit run "$LAB7_ROOT/app.py" --browser.gatherUsageStats=false
