"""Synthetic sequence publisher. No physical robot is controlled by this node."""
import rclpy
import json
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from rclpy.duration import Duration
from week08_interfaces.msg import TargetObservation
from evaluation.behavior import SCENARIOS, sequence


class Demo(Node):
    def __init__(self):
        super().__init__("lab7_observation_demo")
        self.declare_parameter("seed_json","{}")
        seed = json.loads(self.get_parameter("seed_json").value)
        self.events = [(name, event) for name in SCENARIOS for event in sequence(name,seed)]
        self.index = 0
        self.publisher = self.create_publisher(TargetObservation, "/perception/target", 10)
        self.create_timer(.1, self.tick)

    def tick(self):
        name, event = self.events[self.index % len(self.events)]
        self.index += 1
        if event["frame_id"] == 0: self.get_logger().info("Sequence: " + name)
        if event["observation"] is None: return
        message = TargetObservation()
        message.header.stamp = (self.get_clock().now()-Duration(seconds=event["age"])).to_msg()
        message.label = "cup"
        for key, value in event["observation"].items(): setattr(message, key, value)
        self.publisher.publish(message)


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = Demo()
    try:
        while rclpy.ok(): rclpy.spin_once(node, timeout_sec=.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
