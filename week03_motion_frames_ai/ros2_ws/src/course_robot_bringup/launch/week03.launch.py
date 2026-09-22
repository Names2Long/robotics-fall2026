from __future__ import annotations
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
def generate_launch_description():
    gazebo=os.path.join(get_package_share_directory("turtlebot3_gazebo"),"launch","empty_world.launch.py")
    camera=os.path.join(get_package_share_directory("course_robot_bringup"),"models","hall_camera.sdf")
    return LaunchDescription([
        SetEnvironmentVariable("TURTLEBOT3_MODEL","burger"),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(gazebo)),
        Node(package="tf2_ros",executable="static_transform_publisher",name="rear_camera_tf",
             arguments=["--x","-0.18","--y","0","--z","0.22","--yaw","3.1415926536","--pitch","0","--roll","0",
                        "--frame-id","base_link","--child-frame-id","rear_camera_link"]),
        Node(package="tf2_ros",executable="static_transform_publisher",name="hall_camera_tf",
             arguments=["--x","0","--y","-2","--z","1.2","--yaw","1.5707963268","--pitch","0","--roll","0",
                        "--frame-id","odom","--child-frame-id","hall_camera"]),
        Node(package="ros_gz_sim",executable="create",name="spawn_hall_camera",output="screen",
             arguments=["-file",camera,"-name","hall_camera_model","-x","0","-y","-2","-z","0"]),
        Node(package="course_cmd_vel_guard",executable="cmd_vel_guard",output="screen"),
        Node(package="rviz2",executable="rviz2",name="rviz2",output="screen"),
    ])
