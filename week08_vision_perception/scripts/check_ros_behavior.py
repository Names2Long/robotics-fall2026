"""Live ROS regression check on isolated topics. Run after sourcing ros_env.sh."""
import time
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.duration import Duration
from geometry_msgs.msg import Twist
from week08_interfaces.msg import TargetObservation
from week08_perception.target_behavior import TargetBehavior


def main():
    rclpy.init(args=['--ros-args', '-r', '__ns:=/lab7_check',
                     '-r', '/perception/target:=/lab7_check/target',
                     '-r', '/student_cmd_vel:=/lab7_check/commands',
                     '-r', '/perception/policy_state:=/lab7_check/state'])
    behavior = TargetBehavior()
    probe = Node('probe')
    publisher = probe.create_publisher(TargetObservation, '/lab7_check/target', 10)
    commands = []
    probe.create_subscription(Twist, '/lab7_check/commands', lambda m: commands.append((m.linear.x, m.angular.z)), 10)
    executor = SingleThreadedExecutor()
    executor.add_node(behavior)
    executor.add_node(probe)

    def phase(duration, age=None):
        commands.clear()
        end = time.monotonic() + duration
        next_frame = 0
        while time.monotonic() < end:
            if age is not None and time.monotonic() >= next_frame:
                message = TargetObservation()
                message.header.stamp = (probe.get_clock().now() - Duration(seconds=age)).to_msg()
                message.detected = True
                message.confidence = .9
                message.center_offset = .02
                message.area_fraction = .1
                publisher.publish(message)
                next_frame = time.monotonic() + .1
            executor.spin_once(timeout_sec=.02)
        return list(commands)

    try:
        phase(.5)
        fresh = phase(1.5, .01)
        assert any(x > 0 for x, _ in fresh), 'Fresh confirmed observations never approached'
        missing = phase(1.2)
        assert missing and all(x == 0 and z == 0 for x, z in missing[-3:]), 'Missing observations did not stop'
        stale = phase(1.2, 1.5)
        assert stale and all(x == 0 and z == 0 for x, z in stale), 'Stale captures enabled motion'
        recovered = phase(1.2, .01)
        assert any(x > 0 for x, _ in recovered), 'Fresh evidence did not recover'
        print('PASS: live ROS confirmation, missing timeout, stale capture rejection and recovery')
    finally:
        executor.shutdown()
        behavior.destroy_node()
        probe.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
