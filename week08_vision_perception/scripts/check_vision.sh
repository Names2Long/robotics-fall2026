#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/ros_env.sh"
export GZ_PARTITION=lab7_vision
exec python3 scripts/vision_preflight.py
