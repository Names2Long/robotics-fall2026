"""ROS 2 interaction controller with Gazebo odometry and bounded velocity output."""
from copy import deepcopy
import json
import math
import time

import rclpy
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist, TwistStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import String

from handover import CUPS, MODES, checkpoint, dispatch, event, load_controller, new_trial


class Interaction(Node):
    def __init__(self):
        super().__init__("lab10_interaction")
        self.output = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        self.status = self.create_publisher(String, "/lab10/status", 10)
        self.events = self.create_publisher(String, "/lab10/events", 10)
        self.create_subscription(Odometry, "/odom", self.odometry, qos_profile_sensor_data)
        self.create_subscription(String, "/lab10/input", self.receive, 10)
        self.create_subscription(Twist, "/lab10/manual_cmd", self.manual, 10)
        self.last_odom = 0.
        self.pose = (0., 0., 0.)
        self.trial = None
        self.trial_id = None
        self.decide = None
        self.lease = 0.
        self.manual_until = 0.
        self.manual_velocity = (0., 0.)
        self.ack = None
        self.error = ""
        self.seen = set()
        self.sequence = 0
        self.distance = 0.
        self.last_tick = 0.
        self.reset_detected = False
        self.paused_at = None
        self.create_timer(.05, self.tick, clock=Clock(clock_type=ClockType.STEADY_TIME))
        self.get_logger().info("Lab 10 ROS controller ready. Waiting for odometry and a trial from the guide.")

    def odometry(self, msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        yaw = math.atan2(2 * (q.w*q.z + q.x*q.y), 1 - 2*(q.y*q.y + q.z*q.z))
        pose = (p.x, p.y, yaw)
        if self.last_odom:
            delta = math.hypot(pose[0]-self.pose[0], pose[1]-self.pose[1])
            if delta > .6 and self.trial:
                self.reset_detected = True
            elif self.trial:
                self.distance += delta
        self.pose, self.last_odom = pose, time.monotonic()

    def velocity(self, linear=0., angular=0.):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x = max(-.35, min(.35, linear))
        msg.twist.angular.z = max(-1., min(1., angular))
        self.output.publish(msg)

    def log_event(self, incoming, source="simulation", intended="", transcript=""):
        before = len(self.trial["events"])
        dispatch(self.trial, incoming, self.decide, source=source, intended=intended, transcript=transcript)
        if len(self.trial["events"]) > before:
            row = self.trial["events"][-1]
            row["ros_pose"] = list(self.pose)
            row["ros_distance_m"] = round(self.distance, 3)
            self.events.publish(String(data=json.dumps(row)))
        self.trial["ros"] = {"pose": list(self.pose), "distance_m": round(self.distance, 3),
                             "topic": "/odom", "backend": "ROS 2 / Gazebo"}

    def receive(self, msg):
        try:
            data = json.loads(msg.data)
            if data.get("kind") == "heartbeat":
                if data.get("trial_id") == self.trial_id:
                    if self.paused_at is not None:
                        elapsed = time.time() - self.paused_at
                        for field in ("opened", "start", "entered", "finished"):
                            if self.trial.get(field) is not None:
                                self.trial[field] += elapsed
                        self.paused_at = None
                    self.lease = time.monotonic()
                return
            command_id = data["command_id"]
            if command_id in self.seen:
                return
            self.error = ""
            if data["kind"] == "start":
                if time.monotonic()-self.last_odom > 1:
                    raise ValueError("No fresh /odom. Launch the Gazebo world first.")
                if math.hypot(self.pose[0], self.pose[1]) > .16:
                    raise ValueError("Reset the world before starting a trial. The robot must be at the handover station.")
                source = data["source"]
                self.decide = load_controller(source) if data["mode"] == MODES[1] else None
                self.trial = new_trial(data["mode"], data["scenario"], data.get("redesign"))
                self.trial["state"]["ros"] = True
                self.trial_id = data["trial_id"]
                self.distance = 0.
                self.reset_detected = False
                self.paused_at = None
            elif data.get("trial_id") != self.trial_id or self.trial is None:
                raise ValueError("The controller belongs to a different trial. Reset and start again.")
            elif data["kind"] == "event":
                incoming = data["event"]
                if incoming["kind"] == "TICK":
                    raise ValueError("Movement events come from live odometry.")
                if incoming["kind"] == "DRIVE":
                    self.pulse(incoming["linear"], incoming["angular"])
                else:
                    self.manual_until = 0.
                    self.velocity()
                    if incoming["kind"] == "READY" and self.trial["state"]["phase"] == "WAIT_READY" and time.time()-self.trial["entered"] >= 45:
                        self.log_event(event("TIMEOUT"))
                    self.update_manual_position()
                    self.log_event(incoming, data.get("source", "control"),
                                   data.get("intended", ""), data.get("transcript", ""))
            else:
                raise ValueError("Unknown ROS command.")
            self.lease = time.monotonic()
        except (ValueError, KeyError, TypeError, RuntimeError) as error:
            self.error = str(error)
            self.velocity()
        if "command_id" in locals():
            self.ack = command_id
            self.seen.add(command_id)
        self.publish_status()

    def update_manual_position(self):
        if self.trial["state"]["mode"] == MODES[0]:
            previous = self.trial["state"]["checkpoint_seen"]
            x, y, _ = self.pose
            cell = round(x)
            self.trial["state"]["position"] = cell if abs(x-cell) < .16 and abs(y) < .16 else -1
            checkpoint(self.trial["state"])
            if not previous and self.trial["state"]["checkpoint_seen"]:
                self.log_event(event("CHECKPOINT"))

    def manual(self, msg):
        if not self.trial:
            return
        self.pulse(msg.linear.x, msg.angular.z)

    def pulse(self, linear, angular):
        state = self.trial["state"]
        if state["mode"] != MODES[0] or state["phase"] != "EXECUTING" or state["waiting_for_change"]:
            self.velocity()
            return
        self.manual_velocity = (max(-.35, min(.35, linear)), max(-1., min(1., angular)))
        self.manual_until = time.monotonic() + .35
        self.lease = time.monotonic()
        self.log_event(event("MANUAL"), source="teleoperation")

    def tick(self):
        now = time.monotonic()
        if not self.trial:
            self.velocity()
            self.publish_status()
            return
        state = self.trial["state"]
        if self.reset_detected:
            self.velocity()
            self.error = "The robot or world was reset during this trial. Archive this attempt and start a new one."
            self.trial.setdefault("ros", {})["invalidated"] = True
        elif now-self.lease > 2 or now-self.last_odom > .6:
            self.velocity()
            if self.paused_at is None:
                self.paused_at = time.time()
        elif state["phase"] == "WAIT_READY":
            self.velocity()
            if time.time()-self.trial["entered"] > 45:
                self.log_event(event("TIMEOUT"))
        elif state["phase"] != "EXECUTING" or state["waiting_for_change"]:
            self.velocity()
        elif state["mode"] == MODES[0]:
            self.update_manual_position()
            if state["waiting_for_change"]:
                self.velocity()
            else:
                self.velocity(*(self.manual_velocity if now < self.manual_until else (0., 0.)))
        else:
            try:
                decision = self.decide(deepcopy(state), event("TICK")) if self.decide else "advance"
                if decision != "advance":
                    self.velocity()
                else:
                    self.navigate(now)
            except Exception as error:
                self.error = f"Controller error. {error}"
                self.velocity()
        self.publish_status()

    def navigate(self, now):
        state = self.trial["state"]
        position = state["position"]
        target = 0 if state["held"] else CUPS.get(state["target"], 0)
        next_position = position if position == target else position + (1 if target > position else -1)
        x, y, yaw = self.pose
        distance = math.hypot(next_position-x, y)
        if distance < .10:
            self.velocity()
            if now-self.last_tick > .25:
                # The state machine advances only after Gazebo odometry reaches the waypoint.
                self.log_event(event("TICK"))
                self.last_tick = now
            return
        angle = math.atan2(-y, next_position-x)
        error = math.atan2(math.sin(angle-yaw), math.cos(angle-yaw))
        self.velocity(min(.35, .8*distance) if abs(error) < .35 else 0., 1.8*error)

    def publish_status(self):
        self.sequence += 1
        payload = {"trial_id": self.trial_id, "trial": self.trial, "ack": self.ack,
                   "error": self.error, "pose": list(self.pose), "sequence": self.sequence,
                   "odom_age": time.monotonic()-self.last_odom, "lease_age": time.monotonic()-self.lease}
        self.status.publish(String(data=json.dumps(payload)))


def main():
    rclpy.init()
    node = Interaction()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.velocity()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
