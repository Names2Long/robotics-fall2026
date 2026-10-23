#!/usr/bin/env python3
"""Observe live camera and clock, not merely installed Python packages."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from rosgraph_msgs.msg import Clock
from cv_bridge import CvBridge
from perception.dataset import ROOT


def main():
    rclpy.init()
    node = rclpy.create_node('lab7_vision_preflight')
    frames, clocks = [], []
    bridge = CvBridge()
    def camera(msg):
        try:
            image = bridge.imgmsg_to_cv2(msg,'bgr8')
            if image.size: frames.append((msg.header.stamp.sec,msg.header.stamp.nanosec))
        except Exception: pass
    node.create_subscription(Image,'/camera/image_raw',camera,qos_profile_sensor_data)
    node.create_subscription(Clock,'/clock',lambda m:clocks.append((m.clock.sec,m.clock.nanosec)),qos_profile_sensor_data)
    deadline = time.monotonic()+20
    while time.monotonic()<deadline:
        rclpy.spin_once(node,timeout_sec=.2)
        if len(set(frames)) >= 3 and len(set(clocks)) >= 3: break
    types = dict(node.get_topic_names_and_types())
    checks = {'live_camera':len(set(frames)) >= 3, 'advancing_clock':len(set(clocks)) >= 3,
              'command_bridge': 'geometry_msgs/msg/TwistStamped' in types.get('/cmd_vel',[]) and node.count_subscribers('/cmd_vel') > 0,
              'independent_guard':'lab7_vision_guard' in node.get_node_names()}
    active = ROOT/'runtime/worlds/active.json'
    report = {'checked_at':time.time(),'world_run':json.loads(active.read_text()) if active.exists() else {},'checks':checks,'ready':all(checks.values())}
    path = ROOT/'runtime/evidence/vision_preflight.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2))
    for name,passed in checks.items(): print(('PASS ' if passed else 'FAIL ')+name)
    node.destroy_node()
    rclpy.shutdown()
    return 0 if report['ready'] else 1


if __name__ == '__main__': sys.exit(main())
