#!/usr/bin/env python3
"""ROS integration regression. Use an isolated ROS domain, never a running robot."""
import json
import os
import tempfile
import time
from pathlib import Path
import numpy as np
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from rosgraph_msgs.msg import Clock
from geometry_msgs.msg import TwistStamped
from week08_perception import live_vision
from week08_perception.vision_guard import VisionGuard


def main():
    if int(os.environ.get('ROS_DOMAIN_ID','0')) != 128:
        raise RuntimeError('Run with ROS_DOMAIN_ID=128 to isolate this test')
    rclpy.init(args=['--ros-args','-p','use_sim_time:=true'])
    with tempfile.TemporaryDirectory() as folder:
        live_vision.ROOT = Path(folder)
        active = Path(folder)/'runtime/worlds/active.json'
        active.parent.mkdir(parents=True)
        active.write_text(json.dumps({'mode':'pillars','run_id':'isolated-test'}))
        controller = live_vision.LiveVision()
        guard = VisionGuard()
        driver = rclpy.create_node('live_control_test')
        executor = SingleThreadedExecutor()
        for node in (controller,guard,driver): executor.add_node(node)
        camera = driver.create_publisher(Image,'/camera/image_raw',qos_profile_sensor_data)
        clock = driver.create_publisher(Clock,'/clock',10)
        commands = []
        driver.create_subscription(TwistStamped,'/cmd_vel',lambda msg:commands.append((time.monotonic(),msg.twist.linear.x,msg.twist.angular.z)),10)
        image = np.zeros((270,480,3),np.uint8)
        image[80:220,330:420] = (0,0,255)
        bridge = CvBridge()
        sim = 1.
        start_wall = time.monotonic()
        def pump(seconds,frames=True):
            nonlocal sim
            end = time.monotonic()+seconds
            while time.monotonic()<end:
                sim = 1.+time.monotonic()-start_wall
                stamp = Clock()
                stamp.clock.sec = int(sim)
                stamp.clock.nanosec = int((sim-int(sim))*1e9)
                clock.publish(stamp)
                if frames:
                    msg = bridge.cv2_to_imgmsg(image,'bgr8')
                    msg.header.stamp = stamp.clock
                    camera.publish(msg)
                executor.spin_once(timeout_sec=.01)
        try:
            pump(3.)
            assert any(v[2]<0 for v in commands), 'Right-hand target did not cause a right turn'
            assert all(v[1]==0 and abs(v[2])<=.6 for v in commands), 'Pillar command outside limits'
            pump(1.5,False)
            assert commands[-1][1:] == (0.,0.), 'Camera loss did not stop'
            pump(1.)
            assert any(v[2]<0 for v in commands[-20:]), 'Fresh frames did not restore centering'
            executor.remove_node(controller)
            controller.destroy_node()
            pump(.8,False)
            assert commands[-1][1:] == (0.,0.), 'Independent guard did not stop on controller loss'
            print('PASS live steering sign, turn-only limits, camera loss and independent watchdog')
        finally:
            executor.shutdown()
            guard.destroy_node()
            driver.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__': main()
