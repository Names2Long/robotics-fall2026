"""Publish a reference image through each real ROS detector on isolated topics."""
import time
import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from week08_interfaces.msg import TargetObservation
from week08_perception.classical_detector import ClassicalDetector
from week08_perception.learned_detector import LearnedDetector
from perception.dataset import tuning_image


def main():
    rclpy.init(args=['--ros-args', '-r', '/camera/image_raw:=/lab7_check/image',
                     '-r', '/perception/target:=/lab7_check/target',
                     '-r', '/perception/annotated:=/lab7_check/annotated',
                     '-r', '/perception/raw_mask:=/lab7_check/raw_mask',
                     '-r', '/perception/mask:=/lab7_check/mask',
                     '-r', '/perception/contours:=/lab7_check/contours'])
    probe = Node('image_probe')
    publisher = probe.create_publisher(Image, '/lab7_check/image', 10)
    observations, images = [], []
    probe.create_subscription(TargetObservation, '/lab7_check/target', observations.append, 10)
    probe.create_subscription(Image, '/lab7_check/annotated', images.append, 10)
    executor = SingleThreadedExecutor()
    executor.add_node(probe)
    try:
        for detector_type in (ClassicalDetector, LearnedDetector):
            detector = detector_type()
            executor.add_node(detector)
            observations.clear()
            images.clear()
            message = CvBridge().cv2_to_imgmsg(tuning_image(), 'bgr8')
            message.header.stamp = probe.get_clock().now().to_msg()
            deadline = time.monotonic() + 20
            next_publish = 0
            try:
                while time.monotonic() < deadline and not (observations and images):
                    if time.monotonic() >= next_publish:
                        publisher.publish(message)
                        next_publish = time.monotonic() + 1
                    executor.spin_once(timeout_sec=.05)
                assert observations and images, 'No detector output'
                assert observations[-1].detected, 'Reference cup not detected'
                assert observations[-1].header.stamp == message.header.stamp, 'Capture timestamp changed'
                print('PASS:', detector_type.__name__, 'image, detection, annotation and capture timestamp')
            finally:
                executor.remove_node(detector)
                detector.destroy_node()
    finally:
        executor.shutdown()
        probe.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
