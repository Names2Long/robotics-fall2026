#!/usr/bin/env bash
set -eo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$LAB_ROOT/ros2_ws/install/setup.bash"
set -u
export ROS_DOMAIN_ID=26
export TURTLEBOT3_MODEL=burger

required=(/scan /odom /map /tf)
missing=("${required[@]}")
topics=""
for attempt in {1..10}; do
  topics="$(timeout 6 ros2 topic list --no-daemon --spin-time 2 2>&1)" || true
  missing=()
  for topic in "${required[@]}"; do
    if ! grep -Fxq "$topic" <<<"$topics"; then
      missing+=("$topic")
    fi
  done
  if (( ${#missing[@]} == 0 )); then
    break
  fi
  sleep 2
done

if (( ${#missing[@]} != 0 )); then
  printf 'Lab 6 ROS domain: %s\n' "$ROS_DOMAIN_ID" >&2
  printf 'Missing mapping topics: %s\n' "${missing[*]}" >&2
  printf 'Topics found:\n%s\n' "$topics" >&2
  printf 'Check the mapping terminal for errors. Keep it running and retry this command.\n' >&2
  exit 1
fi

printf 'Lab 6 ROS domain %s has /scan, /odom, /map, and /tf.\n' "$ROS_DOMAIN_ID"
if [[ ${1:-} == --check ]]; then
  exit 0
fi
exec rviz2
