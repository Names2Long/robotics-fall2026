#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/ros_env.sh"
export GZ_PARTITION=lab7_vision
mode="${1:-pillars}"
case "$mode" in pillars|practice|track) ;; *) echo 'Choose pillars, practice or track'; exit 2;; esac
mkdir -p runtime/worlds
echo "Starting fresh $mode world and robot. Stop it with Ctrl+C before changing worlds."
if flock --close -n -E 73 runtime/vision_world.lock ros2 launch week08_perception vision_world.launch.py world:="$mode" "${@:2}"; then
  exit 0
else
  status=$?
  if [[ "$status" == 73 ]]; then echo 'A lab world is already running. Stop its terminal with Ctrl+C before launching another.' >&2; fi
  exit "$status"
fi
