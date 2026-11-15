"""Browser guide connection to the ROS interaction node."""
import json
import atexit
import threading
import time
from uuid import uuid4


class Client:
    def __init__(self):
        import rclpy
        from rclpy.context import Context
        from rclpy.executors import SingleThreadedExecutor
        from std_msgs.msg import String
        from sensor_msgs.msg import Image
        from rclpy.qos import qos_profile_sensor_data

        self.context = Context()
        rclpy.init(context=self.context)
        self.node = rclpy.create_node("lab10_guide_" + uuid4().hex[:8], context=self.context)
        self.publisher = self.node.create_publisher(String, "/lab10/input", 10)
        self.status = {}
        self.received = 0.
        self.image = None
        self.image_received = 0.
        self.lock = threading.Lock()
        self.node.create_subscription(String, "/lab10/status", self.receive, 10)
        self.node.create_subscription(Image, "/lab10/world_view", self.receive_image, qos_profile_sensor_data)
        self.executor = SingleThreadedExecutor(context=self.context)
        self.executor.add_node(self.node)
        self.thread = threading.Thread(target=self.executor.spin, daemon=True)
        self.thread.start()
        atexit.register(self.close)

    def close(self):
        if not self.context.ok():
            return
        self.executor.shutdown(timeout_sec=2)
        self.thread.join(timeout=2)
        self.node.destroy_node()
        self.context.try_shutdown()

    def receive(self, message):
        try:
            value = json.loads(message.data)
        except (ValueError, TypeError):
            return
        with self.lock:
            self.status = value
            self.received = time.monotonic()

    def receive_image(self, message):
        from cv_bridge import CvBridge
        from PIL import Image
        from io import BytesIO
        try:
            rgb = CvBridge().imgmsg_to_cv2(message, "rgb8")
            buffer = BytesIO()
            Image.fromarray(rgb).save(buffer, format="PNG")
            with self.lock:
                self.image = buffer.getvalue()
                self.image_received = time.monotonic()
        except (ValueError, RuntimeError) as error:
            self.node.get_logger().warning(f"Could not display the world camera. {error}")

    def snapshot(self):
        with self.lock:
            value = json.loads(json.dumps(self.status))
            value["connection_age"] = time.monotonic() - self.received
            return value

    def publish(self, payload):
        from std_msgs.msg import String
        self.publisher.publish(String(data=json.dumps(payload)))

    def command(self, payload, timeout=3.):
        command_id = uuid4().hex
        payload = {**payload, "command_id": command_id}
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.publish(payload)
            for _ in range(10):
                status = self.snapshot()
                if status.get("ack") == command_id:
                    if status.get("error"):
                        raise RuntimeError(status["error"])
                    return status
                time.sleep(.03)
        raise RuntimeError("The ROS controller did not acknowledge the command. Check Terminal 1 and the ROS environment.")


def client():
    import streamlit as st

    @st.cache_resource
    def connect():
        return Client()
    return connect()


def available():
    try:
        status = client().snapshot()
    except (ImportError, RuntimeError) as error:
        return {"ready": False, "reason": str(error)}
    status["ready"] = status.get("connection_age", 999) < 2 and status.get("odom_age", 999) < 1
    return status


def heartbeat(run):
    client().publish({"kind": "heartbeat", "trial_id": run["id"]})
    status = client().snapshot()
    if status.get("trial_id") != run["id"] or status.get("connection_age", 999) > 2:
        raise RuntimeError("This trial is no longer active in ROS. Archive it, reset the world, and start a fresh trial.")
    run["trial"] = status["trial"]
    return status


def send(run, incoming, source="control", intended="", transcript=""):
    status = client().command({
        "kind": "event", "trial_id": run["id"], "event": incoming,
        "source": source, "intended": intended, "transcript": transcript,
    })
    run["trial"] = status["trial"]
    return status
