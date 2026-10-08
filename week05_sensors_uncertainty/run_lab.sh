#!/usr/bin/env bash
set -euo pipefail
lab_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv_root="$lab_root/.venv"
if [[ ! -x "$venv_root/bin/python" ]]; then
  chosen=""
  for candidate in python3.14 python3.13 python3.12 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info[:2] < (3, 12))' >/dev/null 2>&1; then
      chosen="$candidate"
      break
    fi
  done
  if [[ -z "$chosen" ]]; then
    echo "Install Python 3.12 or newer, then retry. student_submission is untouched." >&2
    exit 1
  fi
  "$chosen" -m venv "$venv_root"
fi
"$venv_root/bin/python" -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 'Lab 5 requires Python 3.12 or newer. Install it and recreate this lab virtual environment after preserving your work.')"
echo "Lab 5 interpreter: $("$venv_root/bin/python" --version)"
"$venv_root/bin/python" -m pip install -r "$lab_root/requirements.txt"
"$venv_root/bin/python" "$lab_root/app.py" --preflight
"$venv_root/bin/python" -m streamlit run "$lab_root/app.py" --browser.gatherUsageStats=false
