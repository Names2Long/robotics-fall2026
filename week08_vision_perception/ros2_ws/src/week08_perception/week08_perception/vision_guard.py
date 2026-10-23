"""Independent monotonic command timeout and Twist-to-TwistStamped interface."""
import time
import rclpy
from rclpy.node import Node
from rclpy.clock import Clock, ClockType
from geometry_msgs.msg import Twist, TwistStamped
from perception.vision_control import bounded_command


class VisionGuard(Node):
    def __init__(self):
        super().__init__('lab7_vision_guard')
        self.output = self.create_publisher(TwistStamped,'/cmd_vel',10)
        self.last = 0.
        self.create_subscription(Twist,'/lab7/request_cmd',self.receive,10)
        self.create_timer(.05,self.check,clock=Clock(clock_type=ClockType.STEADY_TIME))

    def publish(self, linear=0., angular=0.):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x, msg.twist.angular.z = bounded_command(linear,angular)
        self.output.publish(msg)

    def receive(self, msg):
        self.last = time.monotonic()
        self.publish(msg.linear.x,msg.angular.z)

    def check(self):
        if time.monotonic()-self.last > .4: self.publish()


def main():
    from rclpy.signals import SignalHandlerOptions
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = VisionGuard()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.publish()
        node.destroy_node()
        rclpy.try_shutdown()
