import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, AppendEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def start(context):
    from perception.vision_world import build_world
    from perception.dataset import ROOT
    mode = LaunchConfiguration('world').perform(context)
    yaw = float(LaunchConfiguration('yaw').perform(context))
    models = Path(get_package_share_directory('turtlebot3_gazebo'))/'models'
    world = build_world(mode,models/'turtlebot3_waffle/model.sdf',ROOT/'runtime/worlds'/f'{mode}.sdf',yaw)
    gazebo = Path(get_package_share_directory('ros_gz_sim'))/'launch/gz_sim.launch.py'
    return [AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', str(models)),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(str(gazebo)),launch_arguments={'gz_args':f'-r -s -v2 {world}', 'on_exit_shutdown':'true'}.items()),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(str(gazebo)),condition=IfCondition(LaunchConfiguration('gui')),launch_arguments={'gz_args':'-g -v2'}.items()),
            Node(package='ros_gz_bridge',executable='parameter_bridge',arguments=[
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                '/cmd_vel@geometry_msgs/msg/TwistStamped]gz.msgs.Twist'],output='screen'),
            Node(package='ros_gz_image',executable='image_bridge',arguments=['/camera/image_raw','/lab7/world_view'],output='screen'),
            Node(package='week08_perception',executable='vision_guard',parameters=[{'use_sim_time':True}],output='screen')]


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument('world',default_value='pillars'),
                              DeclareLaunchArgument('gui',default_value='true'),
                              DeclareLaunchArgument('yaw',default_value='0'),OpaqueFunction(function=start)])
