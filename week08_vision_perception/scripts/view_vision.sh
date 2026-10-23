#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/ros_env.sh"
export GZ_PARTITION=lab7_vision
ros2 run image_view image_view --ros-args -r image:=/lab7/mask &
mask_pid=$!
trap 'kill "$mask_pid" 2>/dev/null || true' EXIT
ros2 run image_view image_view --ros-args -r image:=/lab7/annotated
