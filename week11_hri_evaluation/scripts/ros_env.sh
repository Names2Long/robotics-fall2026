#!/usr/bin/env bash
LAB10_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH
source /opt/ros/jazzy/setup.bash
if [[ ! -f "$LAB10_ROOT/ros2_ws/install_hri/setup.bash" ]]; then
  echo "Build Lab 10 first with bash scripts/course_preflight.sh" >&2
  return 1 2>/dev/null || exit 1
fi
source "$LAB10_ROOT/ros2_ws/install_hri/setup.bash"
export WEEK11_LAB_ROOT="$LAB10_ROOT"
export PYTHONPATH="$LAB10_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export ROS_DOMAIN_ID=31
export GZ_PARTITION=lab10_handover
cd "$LAB10_ROOT"
