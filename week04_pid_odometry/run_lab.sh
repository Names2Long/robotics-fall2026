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
    echo "Lab 4 needs Python 3.12 or newer. Install it, then retry; student_submission is untouched." >&2
    exit 1
  fi
  "$chosen" -m venv "$venv_root"
fi

if ! "$venv_root/bin/python" -c 'import sys; raise SystemExit(sys.version_info[:2] < (3, 12))'; then
  echo "This Lab 4 .venv uses an older Python. Preserve student_submission, then recreate only week04_pid_odometry/.venv with Python 3.12 or newer." >&2
  exit 1
fi
echo "Lab 4 interpreter: $("$venv_root/bin/python" --version)"

"$venv_root/bin/python" -m pip install --upgrade pip
"$venv_root/bin/python" -m pip install -r "$lab_root/requirements.txt"
"$venv_root/bin/python" "$lab_root/app.py" --preflight
"$venv_root/bin/python" -m streamlit run "$lab_root/app.py" --browser.gatherUsageStats=false
