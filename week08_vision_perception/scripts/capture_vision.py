#!/usr/bin/env python3
"""Capture one live image for instructor diagnosis, without commanding motion."""
import argparse
import time
import cv2
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic',default='/lab7/world_view')
    parser.add_argument('--output',default='runtime/world-view.png')
    args = parser.parse_args()
    rclpy.init()
    node = rclpy.create_node('capture_vision')
    received = []
    bridge = CvBridge()
    node.create_subscription(Image,args.topic,lambda m:received.append(m),qos_profile_sensor_data)
    end = time.monotonic()+20
    while not received and time.monotonic()<end: rclpy.spin_once(node,timeout_sec=.2)
    if not received: raise RuntimeError('No image received')
    assert cv2.imwrite(args.output,bridge.imgmsg_to_cv2(received[-1],'bgr8'))
    print(args.output)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__': main()
