#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/ros_env.sh"
export GZ_PARTITION=lab7_vision
kind="${1:-pillar_search}"
mode="${2:-pillars}"
case "$kind:$mode" in pillar_search:pillars|line_following:practice|line_following:track) ;; *) echo 'Use pillar_search pillars, line_following practice, or line_following track'; exit 2;; esac
echo 'Controller starting. Ctrl+C saves an interrupted attempt and stops motion.'
if flock --close -n -E 73 runtime/vision_control.lock ros2 run week08_perception live_vision --ros-args -p use_sim_time:=true -p kind:="$kind" -p world:="$mode" -p settings_file:="${WEEK08_SUBMISSION_DIR:-$LAB7_ROOT/student_submission}/$kind/settings.json"; then
  exit 0
else
  status=$?
  if [[ "$status" == 73 ]]; then echo 'A controller is already running. Stop its terminal with Ctrl+C before starting another.' >&2; fi
  exit "$status"
fi
