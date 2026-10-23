from dataclasses import fields
import time
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from week08_interfaces.msg import TargetObservation
from evaluation.behavior import BehaviorConfig, Policy


class TargetBehavior(Node):
    def __init__(self):
        super().__init__("target_behavior")
        for field in fields(BehaviorConfig): self.declare_parameter(field.name, field.default)
        self.latest = None
        self.received = 0.
        self.stamp = 0.
        self.config = self.read_config()
        self.policy = Policy(self.config)
        self.publisher = self.create_publisher(Twist, "/student_cmd_vel", 10)
        self.states = self.create_publisher(String, "/perception/policy_state", 10)
        self.create_subscription(TargetObservation, "/perception/target", self.on_observation, 10)
        self.create_timer(.1, self.tick)

    def read_config(self):
        return BehaviorConfig(**{f.name: self.get_parameter(f.name).value for f in fields(BehaviorConfig)})

    def on_observation(self, message):
        stamp = message.header.stamp.sec + message.header.stamp.nanosec/1e9
        if stamp <= self.stamp: return  # Reject replayed and out-of-order captures.
        self.latest = {name: getattr(message, name) for name in ("detected", "confidence", "center_offset", "area_fraction")}
        self.received = time.monotonic()
        self.stamp = stamp

    def tick(self):
        command = Twist()
        try:
            config = self.read_config()
            if config != self.config:
                self.config, self.policy = config, Policy(config)
            now = self.get_clock().now().nanoseconds/1e9
            capture_age = now-self.stamp
            age = max(capture_age, time.monotonic()-self.received) if capture_age >= 0 else -1.
            result = self.policy.step(self.latest, age, self.stamp)
            command.linear.x, command.angular.z = result["linear_x"], result["angular_z"]
            state = String()
            state.data = result["state"]+": "+result["reason"]
            self.states.publish(state)
        except ValueError as error: self.get_logger().error(str(error))
        self.publisher.publish(command)


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = TargetBehavior()
    try:
        while rclpy.ok(): rclpy.spin_once(node, timeout_sec=.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.publisher.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()
