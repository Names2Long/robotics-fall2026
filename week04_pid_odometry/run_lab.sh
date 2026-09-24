#!/usr/bin/env bash
set -euo pipefail

lab_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv_root="$lab_root/.venv"

if [[ ! -x "$venv_root/bin/python" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$venv_root"
  elif command -v python >/dev/null 2>&1; then
    python -m venv "$venv_root"
  else
    echo "Python 3.12 is required. Install Python and run this command again." >&2
    exit 1
  fi
fi

"$venv_root/bin/python" -m pip install --upgrade pip
"$venv_root/bin/python" -m pip install -r "$lab_root/requirements.txt"
"$venv_root/bin/python" "$lab_root/app.py" --preflight
"$venv_root/bin/python" -m streamlit run "$lab_root/app.py"
