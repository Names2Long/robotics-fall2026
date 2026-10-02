#!/usr/bin/env bash
set -euo pipefail
lab_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv_root="$lab_root/.venv"
if [[ ! -x "$venv_root/bin/python" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$venv_root"
  else
    echo "Install Python 3.12 or newer, then retry. No sudo or Docker is needed." >&2
    exit 1
  fi
fi
"$venv_root/bin/python" -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 'Lab 5 requires Python 3.12 or newer. Install it and recreate this lab virtual environment after preserving your work.')"
"$venv_root/bin/python" -m pip install -r "$lab_root/requirements.txt"
"$venv_root/bin/python" "$lab_root/app.py" --preflight
"$venv_root/bin/python" -m streamlit run "$lab_root/app.py"
