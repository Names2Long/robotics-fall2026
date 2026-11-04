"""Canonical Lab 8 world and Nav2. One launch process per trial resets all state."""
import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory as share
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, IncludeLaunchDescription, AppendEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def start(context):
    from planning.worlds import generate
    name = LaunchConfiguration('map_name').perform(context)
    output = Path(LaunchConfiguration('output').perform(context)).resolve()
    models = Path(share('turtlebot3_gazebo'))/'models'
    world,mapfile,params = generate(name,output,models,Path(share('turtlebot3_navigation2'))/'param/burger.yaml',
                                   LaunchConfiguration('social').perform(context)=='true')
    gz = str(Path(share('ros_gz_sim'))/'launch/gz_sim.launch.py')
    state = str(Path(share('turtlebot3_gazebo'))/'launch/robot_state_publisher.launch.py')
    localization = str(Path(share('nav2_bringup'))/'launch/localization_launch.py')
    bridge = str(Path(share('turtlebot3_gazebo'))/'params/turtlebot3_burger_bridge.yaml')
    return [AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH',str(models)),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(gz),launch_arguments={'gz_args':f'-r -s -v2 {world}','on_exit_shutdown':'true'}.items()),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(gz),condition=IfCondition(LaunchConfiguration('gui')),launch_arguments={'gz_args':'-g -v2'}.items()),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(state),launch_arguments={'use_sim_time':'true'}.items()),
            Node(package='ros_gz_bridge',executable='parameter_bridge',arguments=['--ros-args','-p',f'config_file:={bridge}']),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(localization),launch_arguments={
                'map':str(mapfile),'params_file':str(params),'use_sim_time':'true','autostart':'true','use_composition':'False'}.items())]+navigation_nodes(params)


def navigation_nodes(params):
    """Only launch the services used by these fixed-path experiments.

    Full bringup also starts docking, route, behavior-tree and waypoint servers.
    Their lifecycle transitions are unrelated to ComputePathToPose/FollowPath
    and previously could stall the whole batch before the planner was active.
    Keep the normal controller -> smoother -> collision monitor safety chain.
    """
    remaps = [('/tf','tf'),('/tf_static','tf_static')]
    nodes = []
    for package,executable in [('nav2_controller','controller_server'),('nav2_planner','planner_server'),
                               ('nav2_velocity_smoother','velocity_smoother'),('nav2_collision_monitor','collision_monitor')]:
        velocity_remaps = [('cmd_vel','cmd_vel_nav')] if executable in ('controller_server','velocity_smoother') else []
        nodes.append(Node(package=package,executable=executable,name=executable,output='screen',
            parameters=[str(params),{'use_sim_time':True}],remappings=remaps+velocity_remaps))
    nodes.append(Node(package='nav2_lifecycle_manager',executable='lifecycle_manager',
        name='lifecycle_manager_navigation',output='screen',parameters=[{
            'use_sim_time':True,'autostart':True,
            'node_names':['controller_server','planner_server','velocity_smoother','collision_monitor']}]))
    return nodes


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument('map_name',default_value='open'),
        DeclareLaunchArgument('output',default_value=str(Path.cwd()/'runtime/active')),
        DeclareLaunchArgument('social',default_value='false'),DeclareLaunchArgument('gui',default_value='true'),OpaqueFunction(function=start)])
