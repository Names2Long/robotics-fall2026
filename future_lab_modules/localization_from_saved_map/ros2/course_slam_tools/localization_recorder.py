from __future__ import annotations
import json, math, time
from pathlib import Path
import rclpy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


def summarize_samples(samples):
    if not samples:
        return {"sample_count": 0, "duration": 0, "convergence_time": None,
                "final_covariance": None, "settled_position_spread": None, "pose_jump": None,
                "reference_available": False, "final_position_error": None,
                "final_heading_error": None, "false_confident_samples": None,
                "correct_convergence_time": None}
    settled = samples[-20:]
    cx = sum(row["x"] for row in settled) / len(settled)
    cy = sum(row["y"] for row in settled) / len(settled)
    spread = math.sqrt(sum((row["x"] - cx) ** 2 + (row["y"] - cy) ** 2 for row in settled) / len(settled))
    jumps = [math.hypot(b["x"] - a["x"], b["y"] - a["y"]) for a, b in zip(samples, samples[1:])]
    metrics = {
        "sample_count": len(samples), "duration": samples[-1]["time"] - samples[0]["time"],
        "convergence_time": next((row["time"] for row in samples if row["covariance_trace"] <= .5), None),
        "final_covariance": samples[-1]["covariance_trace"], "settled_position_spread": spread,
        "pose_jump": max(jumps, default=0.0),
    }
    referenced = [row for row in samples if all(key in row for key in ("reference_x", "reference_y", "reference_yaw"))]
    if len(referenced) >= max(20, math.ceil(.8 * len(samples))) and referenced[-1] is samples[-1]:
        errors = [(row["time"], math.hypot(row["x"] - row["reference_x"], row["y"] - row["reference_y"]),
                   abs(math.atan2(math.sin(row["yaw"] - row["reference_yaw"]), math.cos(row["yaw"] - row["reference_yaw"]))),
                   row["covariance_trace"]) for row in referenced]
        metrics.update(reference_available=True, final_position_error=errors[-1][1],
                       final_heading_error=errors[-1][2],
                       false_confident_samples=sum(cov <= .5 and distance > .5 for _, distance, _, cov in errors),
                       correct_convergence_time=next(
                           (errors[index + 2][0] for index in range(len(errors) - 2)
                            if all(distance <= .30 and heading <= .25 for _, distance, heading, _ in errors[index:index + 3])),
                           None))
    else:
        metrics.update(reference_available=False, final_position_error=None,
                       final_heading_error=None, false_confident_samples=None,
                       correct_convergence_time=None)
    return metrics

class Recorder(Node):
    def __init__(self):
        super().__init__("localization_recorder")
        for name, default in (("condition", "good_initial_pose"), ("duration", 30.0), ("output", "localization.json")): self.declare_parameter(name, default)
        self.started = time.monotonic(); self.samples = []; self.raw_scans = 0; self.used_scans = 0
        self.reference = None
        self.create_subscription(PoseWithCovarianceStamped, "/amcl_pose", self.on_pose, 10)
        self.create_subscription(PoseStamped, "/course_reference_pose", self.on_reference, 10)
        self.create_subscription(LaserScan, "/scan", lambda _: setattr(self, "raw_scans", self.raw_scans + 1), qos_profile_sensor_data)
        self.create_subscription(LaserScan, "/scan_degraded", lambda _: setattr(self, "used_scans", self.used_scans + 1), qos_profile_sensor_data)
        self.create_timer(.25, self.tick)
    def on_pose(self, msg):
        q = msg.pose.pose.orientation; yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)); covariance = msg.pose.covariance
        row = {"time": time.monotonic() - self.started, "x": msg.pose.pose.position.x, "y": msg.pose.pose.position.y, "yaw": yaw, "covariance_trace": covariance[0] + covariance[7] + covariance[35]}
        # Compare only poses certified in the same map frame; world-frame Gazebo
        # coordinates cannot be subtracted from AMCL's map-frame estimate.
        if msg.header.frame_id == "map" and self.reference is not None and self.reference["received_at"] + .5 >= time.monotonic():
            row.update(reference_x=self.reference["x"], reference_y=self.reference["y"], reference_yaw=self.reference["yaw"])
        self.samples.append(row)
    def on_reference(self, msg):
        if msg.header.frame_id != "map": return
        q = msg.pose.orientation
        self.reference = {"x": msg.pose.position.x, "y": msg.pose.position.y,
                          "yaw": math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)),
                          "received_at": time.monotonic()}
    def tick(self):
        if time.monotonic() - self.started < float(self.get_parameter("duration").value): return
        condition = str(self.get_parameter("condition").value); valid = self.samples
        metrics = summarize_samples(valid)
        metrics["scan_retention"] = self.used_scans / max(1, self.raw_scans) if condition == "degraded_sensor" else 1.0
        payload = {"schema_version": 2, "condition": condition, "metrics": metrics, "samples": valid,
                   "reference_note": "Map-frame reference received" if metrics.get("reference_available") else
                   "No certified map-frame reference; covariance is not position error."}
        path = Path(str(self.get_parameter("output").value)); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.get_logger().info(f"Saved {path}"); rclpy.shutdown()
def main():
    rclpy.init(); node = Recorder()
    try: rclpy.spin(node)
    finally: node.destroy_node()
