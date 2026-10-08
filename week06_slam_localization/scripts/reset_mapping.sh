#!/usr/bin/env bash
set -eo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$LAB_ROOT/ros2_ws/install/setup.bash"
set -u
export ROS_DOMAIN_ID=26

active_nodes="$(timeout 8 ros2 node list --no-daemon --spin-time 1 2>/dev/null)" || active_nodes=""
if grep -Eq '^/(slam_toolbox|robot_state_publisher)$' <<<"$active_nodes"; then
  printf 'The first mapping launch is still active. Stop it with Ctrl+C and wait, then retry.\n' >&2
  exit 1
fi

# ROS launch can exit while its Gazebo server and GUI remain alive. Match only
# the exact TurtleBot3 House server and its standard GUI in this course container.
for pattern in \
  '^gz sim -r -s -v2 /opt/ros/jazzy/share/turtlebot3_gazebo/worlds/turtlebot3_house.world$' \
  '^gz sim -g -v2$'; do
  while read -r pid; do
    [[ -n "$pid" ]] || continue
    kill -TERM "$pid" 2>/dev/null || true
  done < <(pgrep -f "$pattern" || true)
done

for attempt in {1..10}; do
  if ! pgrep -f '^gz sim -r -s -v2 /opt/ros/jazzy/share/turtlebot3_gazebo/worlds/turtlebot3_house.world$' >/dev/null; then
    printf 'Old TurtleBot3 House server stopped. Saved Mission 1 files were not changed.\n'
    exit 0
  fi
  sleep 1
done
printf 'The old Gazebo server is still running. Do not start Mission 2 yet.\n' >&2
exit 1
