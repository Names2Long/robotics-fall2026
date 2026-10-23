#!/usr/bin/env bash
# Source this in every terminal used for Lab 7 ROS commands.
LAB7_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
if [[ ! -f "$LAB7_ROOT/ros2_ws/install/setup.bash" ]]; then
  echo "Build first: cd $LAB7_ROOT/ros2_ws && colcon build --symlink-install"
  return 1 2>/dev/null || exit 1
fi
source "$LAB7_ROOT/ros2_ws/install/setup.bash"
export ROS_DOMAIN_ID=28
export WEEK08_LAB_ROOT="$LAB7_ROOT"
export PYTHONPATH="$LAB7_ROOT${PYTHONPATH:+:$PYTHONPATH}"
cd "$LAB7_ROOT"
