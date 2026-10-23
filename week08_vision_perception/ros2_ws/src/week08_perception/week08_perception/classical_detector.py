from dataclasses import fields
import time
import json
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from week08_interfaces.msg import TargetObservation
from perception.classical import Settings, process


class ClassicalDetector(Node):
    def __init__(self):
        super().__init__("classical_detector")
        for field in fields(Settings): self.declare_parameter(field.name, field.default)
        self.declare_parameter("camera_topic", "/camera/image_raw")
        self.declare_parameter("implementation_json", "{}")
        self.bridge = CvBridge()
        self.observations = self.create_publisher(TargetObservation, "/perception/target", 10)
        self.images = {name: self.create_publisher(Image, "/perception/"+name, 10) for name in ("raw_mask", "mask", "contours", "annotated")}
        self.create_subscription(Image, self.get_parameter("camera_topic").value, self.on_image, qos_profile_sensor_data)
        self.get_logger().info("Classical detector ready for images")

    def on_image(self, message):
        started = time.perf_counter()
        image = self.bridge.imgmsg_to_cv2(message, "bgr8")
        try:
            settings = Settings(**{f.name: self.get_parameter(f.name).value for f in fields(Settings)})
            implementation = json.loads(self.get_parameter("implementation_json").value) or None
            if implementation:
                from perception.student_code import check_implementation
                check_implementation(implementation)
            result = process(image, settings, implementation)
        except ValueError as error:
            self.get_logger().error(str(error))
            return
        out = TargetObservation()
        out.header = message.header
        out.label = "cup"
        out.detected = result["detected"]
        out.confidence = float(out.detected)  # Binary rule score, not a probability.
        if result["bbox"]:
            x, y, w, h = result["bbox"]
            out.bbox_x, out.bbox_y, out.bbox_width, out.bbox_height = x, y, w, h
            out.center_offset = float(2*(x+w/2)/image.shape[1]-1)
            out.area_fraction = float(w*h/(image.shape[0]*image.shape[1]))
        out.latency_ms = (time.perf_counter()-started)*1000
        self.observations.publish(out)
        for name, publisher in self.images.items():
            converted = self.bridge.cv2_to_imgmsg(result[name], "mono8" if result[name].ndim == 2 else "bgr8")
            converted.header = message.header
            publisher.publish(converted)


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = ClassicalDetector()
    try:
        while rclpy.ok(): rclpy.spin_once(node, timeout_sec=.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
