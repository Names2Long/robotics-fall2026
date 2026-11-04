"""Make the same pure-Python core available offline and in the ROS package."""
from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[1] / 'ros2_ws/src/week09_nav_tools/planning'))
