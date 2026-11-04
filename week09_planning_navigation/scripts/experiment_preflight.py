"""Run inside the course ROS desktop after building the workspace."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
checks = {'ros_distro_jazzy':os.environ.get('ROS_DISTRO')=='jazzy',
          'domain_29':os.environ.get('ROS_DOMAIN_ID')=='29',
          'partition_lab8':os.environ.get('GZ_PARTITION')=='lab8_planning',
          'rclpy':importlib.util.find_spec('rclpy') is not None,
          'gazebo':shutil.which('gz') is not None}
for package in ('nav2_bringup','nav2_smac_planner','nav2_regulated_pure_pursuit_controller',
                'nav2_controller','nav2_planner','nav2_velocity_smoother','nav2_collision_monitor',
                'nav2_lifecycle_manager','turtlebot3_gazebo','week09_nav_tools'):
    result = subprocess.run(['ros2','pkg','prefix',package],capture_output=True,text=True,timeout=10)
    checks[package] = result.returncode==0
    if package=='nav2_controller':
        manifest = Path(result.stdout.strip())/'share/nav2_controller/plugins.xml'
        checks['position_goal_checker'] = result.returncode==0 and manifest.is_file() and 'nav2_controller::PositionGoalChecker' in manifest.read_text()
document = dict(schema=2,checked_unix=time.time(),checks=checks,ready=all(checks.values()),
                note='Software readiness only. Each robot trial separately checks actions, transforms and live lidar.')
target = ROOT/'runtime/preflight.json'
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(document,indent=2))
print(json.dumps(document,indent=2))
raise SystemExit(0 if document['ready'] else 1)
