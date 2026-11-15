"""Keyboard teleoperation with ROS command pulses and release-to-stop behavior."""
import select
import sys
import termios
import tty
import rclpy
from geometry_msgs.msg import Twist


def main():
    rclpy.init()
    node = rclpy.create_node("lab10_keyboard")
    publisher = node.create_publisher(Twist, "/lab10/manual_cmd", 10)
    settings = termios.tcgetattr(sys.stdin)
    print("Focus this terminal. W forward, S reverse, A left, D right. Space stops. Q exits.")
    print("Hold a key for repeated commands. Keep the guide open for its heartbeat.")
    try:
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            readable, _, _ = select.select([sys.stdin], [], [], .1)
            if not readable:
                continue
            key = sys.stdin.read(1).lower()
            if key in ("q", "\x03"):
                break
            linear, angular = {"w": (.35, 0.), "s": (-.35, 0.), "a": (0., .8),
                               "d": (0., -.8), " ": (0., 0.)}.get(key, (0., 0.))
            message = Twist()
            message.linear.x, message.angular.z = linear, angular
            publisher.publish(message)
    finally:
        publisher.publish(Twist())
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
