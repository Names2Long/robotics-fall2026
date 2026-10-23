"""Expose the ROS package's single shared implementation to the guide."""
from pathlib import Path
__path__ = [str(Path(__file__).resolve().parents[1]/"ros2_ws/src/week08_perception/perception")]
