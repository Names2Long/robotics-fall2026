import time
from pathlib import Path
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from week08_interfaces.msg import TargetObservation
from perception.learned import FrozenDetector, MODEL, annotate, suppress_duplicates


class LearnedDetector(Node):
    def __init__(self):
        super().__init__("learned_detector")
        self.declare_parameter("camera_topic", "/camera/image_raw")
        self.declare_parameter("model_path", str(MODEL))
        self.declare_parameter("confidence_threshold", .5)
        self.declare_parameter('nms_iou',.45)
        self.model = FrozenDetector(Path(self.get_parameter("model_path").value))
        self.bridge = CvBridge()
        self.observations = self.create_publisher(TargetObservation, "/perception/target", 10)
        self.annotated = self.create_publisher(Image, "/perception/annotated", 10)
        self.create_subscription(Image, self.get_parameter("camera_topic").value, self.on_image, qos_profile_sensor_data)

    def on_image(self, message):
        started = time.perf_counter()
        image = self.bridge.imgmsg_to_cv2(message, "bgr8")
        detections = suppress_duplicates(self.model.predict(image,suppress=False),float(self.get_parameter('nms_iou').value))
        threshold = float(self.get_parameter("confidence_threshold").value)
        accepted = [d for d in detections if d["confidence"] >= threshold]
        out = TargetObservation()
        out.header = message.header
        out.label = "cup"
        out.detected = bool(accepted)
        if accepted:
            best = accepted[0]
            x, y, w, h = best["bbox"]
            out.confidence = best["confidence"]
            out.bbox_x, out.bbox_y, out.bbox_width, out.bbox_height = map(int, (x, y, w, h))
            out.center_offset = float(2*(x+w/2)/image.shape[1]-1)
            out.area_fraction = float(w*h/(image.shape[0]*image.shape[1]))
        out.latency_ms = (time.perf_counter()-started)*1000
        self.observations.publish(out)
        annotated = self.bridge.cv2_to_imgmsg(annotate(image, detections, threshold), "bgr8")
        annotated.header = message.header
        self.annotated.publish(annotated)


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = LearnedDetector()
    try:
        while rclpy.ok(): rclpy.spin_once(node, timeout_sec=.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
