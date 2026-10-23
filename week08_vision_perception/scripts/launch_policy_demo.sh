#!/usr/bin/env bash
set -e
source "$(dirname "${BASH_SOURCE[0]}")/ros_env.sh"
exec ros2 launch week08_perception policy_demo.launch.py
