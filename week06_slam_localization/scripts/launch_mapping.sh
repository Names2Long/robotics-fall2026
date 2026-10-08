#!/usr/bin/env bash
set -eo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$LAB_ROOT/ros2_ws/install/setup.bash"
set -u
export ROS_DOMAIN_ID=26
export TURTLEBOT3_MODEL=burger
active_nodes="$(timeout 8 ros2 node list --no-daemon --spin-time 1 2>/dev/null)" || active_nodes=""
if grep -Eq '^/(slam_toolbox|robot_state_publisher)$' <<<"$active_nodes"; then
  printf 'A mapping world is still active in ROS domain %s.\n' "$ROS_DOMAIN_ID" >&2
  printf 'Stop the prior mapping launch with Ctrl+C and wait for Gazebo to close before starting a new run.\n' >&2
  exit 1
fi
if pgrep -f '^gz sim -r -s -v2 /opt/ros/jazzy/share/turtlebot3_gazebo/worlds/turtlebot3_house.world$' >/dev/null; then
  printf 'The previous Gazebo server is still running. Run bash scripts/reset_mapping.sh before starting another map.\n' >&2
  exit 1
fi
printf 'Starting a fresh TurtleBot3 House, robot pose, and empty SLAM map in ROS domain %s.\n' "$ROS_DOMAIN_ID"
ros2 launch course_slam_tools mapping.launch.py
