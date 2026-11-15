#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH
source /opt/ros/jazzy/setup.bash
echo "Building Lab 10 ROS package"
(cd ros2_ws && colcon build --symlink-install --build-base build_hri --install-base install_hri --packages-select course_hri)
if ! /opt/course-venv/bin/python -c 'import pocketsphinx' 2>/dev/null; then
  /opt/course-venv/bin/python -m pip install pocketsphinx==5.0.4
fi
source scripts/ros_env.sh
ros2 pkg prefix course_hri
echo "Lab 10 software is ready. Start the world using bash scripts/launch_handover.sh"
