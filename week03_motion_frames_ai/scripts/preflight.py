"""Read-only dependency and live connection checks, each with a bounded wait."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]


def check(label,passed,detail,recovery):
    return {'check':label,'passed':bool(passed),'detail':detail,'recovery':recovery}


def package_check(name):
    try:
        done=subprocess.run(['ros2','pkg','prefix',name],capture_output=True,text=True,timeout=10)
        passed=done.returncode==0
    except (OSError,subprocess.TimeoutExpired): passed=False
    return check('Package: '+name,passed,'Available' if passed else 'Not found','Run the setup/build command in this page, then source the workspace.')


def live_checks():
    names=('Simulation clock advances','Odometry messages received','Course command guard connected','Required transforms available')
    repair='Start the lab launch in terminal A, wait for Gazebo, unpause simulation, and rerun these checks.'
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import qos_profile_sensor_data
        from rclpy.time import Time
        from nav_msgs.msg import Odometry
        from rosgraph_msgs.msg import Clock
        from tf2_ros import Buffer,TransformListener
    except ImportError:
        return [check(n,False,'ROS Python packages are unavailable',repair) for n in names]
    rclpy.init();node=Node('week03_preflight');clocks=[];odometry=[]
    buffer=Buffer();listener=TransformListener(buffer,node)
    node.create_subscription(Clock,'/clock',lambda msg:clocks.append(msg.clock.sec+msg.clock.nanosec*1e-9),qos_profile_sensor_data)
    node.create_subscription(Odometry,'/odom',lambda msg:odometry.append(time.monotonic()),qos_profile_sensor_data)
    try:
        deadline=time.monotonic()+6
        while time.monotonic()<deadline: rclpy.spin_once(node,timeout_sec=.1)
        guard=any(i.node_name=='course_cmd_vel_guard' for i in node.get_subscriptions_info_by_topic('/student_cmd_vel'))
        guard=guard and any(i.node_name=='course_cmd_vel_guard' and i.topic_type=='geometry_msgs/msg/TwistStamped' for i in node.get_publishers_info_by_topic('/cmd_vel'))
        transforms=all(buffer.can_transform(target,source,Time()) for target,source in (
            ('odom','base_link'),('base_link','base_scan'),('base_link','rear_camera_link'),('base_link','hall_camera')))
        passed=(len(clocks)>1 and clocks[-1]>clocks[0],len(odometry)>1,guard,transforms)
        return [check(n,p,'Observed during this check' if p else 'Not observed',repair) for n,p in zip(names,passed)]
    finally:
        node.destroy_node();rclpy.shutdown()


def main():
    out=ROOT/'runtime/evidence'
    try: out.mkdir(parents=True,exist_ok=True);writable=os.access(out,os.W_OK)
    except OSError: writable=False
    checks=[check('ROS distribution',os.environ.get('ROS_DISTRO')=='jazzy',os.environ.get('ROS_DISTRO','not sourced'),'Source /opt/ros/jazzy/setup.bash.'),
            check('ROS domain',os.environ.get('ROS_DOMAIN_ID')=='25',os.environ.get('ROS_DOMAIN_ID','not set'),'Use export ROS_DOMAIN_ID=25 in each ROS terminal.'),
            check('Evidence storage',writable,str(out),'Check permissions on the cloned lab folder.')]
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks.extend(pool.map(package_check,('turtlebot3_gazebo','tf2_ros','tf2_tools','course_cmd_vel_guard','course_motion_tools','week03_camera_transform','week03_pattern')))
    if '--setup' not in sys.argv: checks.extend(live_checks())
    payload={'schema_version':2,'captured_at':datetime.now(timezone.utc).isoformat(),'scope':'setup' if '--setup' in sys.argv else 'live',
             'checks':checks,'ready':all(c['passed'] for c in checks)}
    if writable:
        target=out/'preflight.json';temp=target.with_suffix('.tmp')
        temp.write_text(json.dumps(payload,indent=2),encoding='utf-8');temp.replace(target)
    for c in checks: print(f"{'PASS' if c['passed'] else 'FAIL'}: {c['check']}: {c['detail']}")
    return 0 if payload['ready'] else 1


if __name__=='__main__': raise SystemExit(main())
