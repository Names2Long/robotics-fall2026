#!/usr/bin/env bash
set -e
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
cd "$LAB_ROOT/ros2_ws" || exit 1
if [[ "${1:-}" == "--setup" ]]; then
    colcon build --symlink-install || exit 1
fi
source install/setup.bash
set -u
export WEEK03_EVIDENCE_DIR="$LAB_ROOT/runtime/evidence"
export ROS_DOMAIN_ID=25
python3 "$LAB_ROOT/scripts/preflight.py" "$@"
