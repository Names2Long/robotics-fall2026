#!/usr/bin/env bash
set -eo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger
export ROS_DOMAIN_ID=29
export GZ_PARTITION=lab8_planning
if [[ -f ros2_ws/install/setup.bash ]]; then source ros2_ws/install/setup.bash; fi
python3 scripts/experiment_preflight.py
