#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/ros_env.sh"
exec python3 scripts/robot_software_preflight.py
