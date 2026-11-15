#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/ros_env.sh"
mkdir -p runtime
echo "Starting the cup delivery room, ROS bridge, and interaction controller."
echo "Watch the robot in Gazebo. Keep this terminal running."
if flock --close -n -E 73 runtime/handover.lock ros2 launch course_hri handover.launch.py "$@"; then
  exit 0
else
  status=$?
  if [[ "$status" == 73 ]]; then
    echo "The Lab 10 world is already running or shutting down. Stop its terminal with Ctrl+C and wait for shutdown before starting another." >&2
  fi
  exit "$status"
fi
