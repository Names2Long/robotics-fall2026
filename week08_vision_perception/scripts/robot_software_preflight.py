#!/usr/bin/env python3
"""Check installed ROS software and built entry points without launching Gazebo."""
import importlib
import json
import os
import shutil
from pathlib import Path
from ament_index_python.packages import get_package_share_directory, get_package_prefix


def checks():
    rows = []
    def check(label,action):
        try:
            result = action()
            rows.append({'check':label,'passed':True,'detail':str(result),'required':True})
        except Exception as error:
            rows.append({'check':label,'passed':False,'detail':str(error),'required':True})
    def distro():
        if os.environ.get('ROS_DISTRO') != 'jazzy': raise ValueError('Use the course ROS 2 Jazzy environment')
        return 'ROS 2 Jazzy sourced. Simulation does not need to be running'
    check('ROS 2 distribution',distro)
    def gazebo():
        executable = shutil.which('gz')
        if not executable: raise ValueError('Gazebo executable not found in the course environment')
        return executable
    check('Gazebo executable',gazebo)
    for module in ('rclpy','cv_bridge'):
        check('ROS Python interface: '+module,lambda name=module:importlib.import_module(name).__file__)
    for package in ('ros_gz_sim','ros_gz_bridge','ros_gz_image','turtlebot3_gazebo','image_view'):
        check('ROS package: '+package,lambda name=package:get_package_share_directory(name))
    def built():
        share = Path(get_package_share_directory('week08_perception'))
        prefix = Path(get_package_prefix('week08_perception'))
        expected = [share/'launch/vision_world.launch.py',*(prefix/'lib/week08_perception'/name for name in ('live_vision','vision_guard'))]
        if any(not path.is_file() for path in expected): raise ValueError('Rebuild the Lab 7 workspace with colcon build --symlink-install')
        for package in ('week08_interfaces','course_cmd_vel_guard'): get_package_share_directory(package)
        return 'Lab launch file, controller, guard and supporting packages found'
    check('Built Lab 7 workspace',built)
    def model():
        path = Path(get_package_share_directory('turtlebot3_gazebo'))/'models/turtlebot3_waffle/model.sdf'
        if not path.is_file(): raise ValueError('Camera-equipped Waffle model is missing')
        return str(path)
    check('Gazebo camera robot model',model)
    def assets():
        root = Path(__file__).resolve().parents[1]
        for name in ('track.png','practice.png'):
            if not (root/'assets/robot_worlds'/name).is_file(): raise ValueError('Missing robot world texture: '+name)
        return 'Straight and curved route textures found'
    check('Robot world assets',assets)
    return rows


if __name__ == '__main__': print(json.dumps(checks()))
