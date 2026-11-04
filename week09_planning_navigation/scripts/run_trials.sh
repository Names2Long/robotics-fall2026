#!/usr/bin/env bash
set -eo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger
export ROS_DOMAIN_ID=29
export GZ_PARTITION=lab8_planning
export PYTHONUNBUFFERED=1
if [[ ! -f ros2_ws/install/setup.bash ]]; then
  echo "Build first: cd ros2_ws && colcon build --symlink-install && cd .."
  exit 2
fi
source ros2_ws/install/setup.bash
python3 scripts/run_trials.py "$@"
