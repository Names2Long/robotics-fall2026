#!/usr/bin/env bash
set -e
if [[ "${1:-}" != classical && "${1:-}" != learned ]]; then
  echo "Usage: bash scripts/launch_pipeline.sh classical|learned [camera_topic]"
  exit 2
fi
source "$(dirname "${BASH_SOURCE[0]}")/ros_env.sh"
exec ros2 launch week08_perception pipeline.launch.py mode:="$1" camera_topic:="${2:-/camera/image_raw}" model_path:="$LAB7_ROOT/assets/models/detector.onnx"
