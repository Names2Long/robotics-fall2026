"""ROS-independent perception and behavior evaluation."""
"""Expose the ROS package's single shared policy and metrics implementation."""
from pathlib import Path
__path__ = [str(Path(__file__).resolve().parents[1]/"ros2_ws/src/week08_perception/evaluation")]
