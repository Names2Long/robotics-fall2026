"""Record individual observations. No score averaging across frames."""
import csv
import time
from pathlib import Path
import rclpy
from rclpy.node import Node
from week08_interfaces.msg import TargetObservation


class Recorder(Node):
    def __init__(self):
        super().__init__("observation_recorder")
        for name, value in (("condition", "normal"), ("expected", True), ("duration", 5.), ("output", "runtime/evidence/observations.csv")):
            self.declare_parameter(name, value)
        path = Path(self.get_parameter("output").value)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file = path.open("a", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.file, fieldnames=("capture_stamp", "condition", "expected", "detected", "confidence", "latency_ms", "center_offset", "area_fraction"))
        if path.stat().st_size == 0: self.writer.writeheader()
        self.started = time.monotonic()
        self.create_subscription(TargetObservation, "/perception/target", self.on_observation, 10)
        self.create_timer(.1, self.tick)

    def on_observation(self, message):
        row = {key: getattr(message, key) for key in ("detected", "confidence", "latency_ms", "center_offset", "area_fraction")}
        row.update(capture_stamp=message.header.stamp.sec+message.header.stamp.nanosec/1e9,
                   condition=self.get_parameter("condition").value, expected=self.get_parameter("expected").value)
        self.writer.writerow(row)
        self.file.flush()

    def tick(self):
        if time.monotonic()-self.started >= self.get_parameter("duration").value:
            self.file.close()
            rclpy.shutdown()


def main():
    rclpy.init()
    node = Recorder()
    try: rclpy.spin(node)
    finally:
        node.file.close()
        node.destroy_node()
