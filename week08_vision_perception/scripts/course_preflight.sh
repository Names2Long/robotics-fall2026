#!/usr/bin/env bash
set -eo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$LAB_ROOT/scripts/ros_env.sh"
set -u
python3 "$LAB_ROOT/scripts/preflight.py"
