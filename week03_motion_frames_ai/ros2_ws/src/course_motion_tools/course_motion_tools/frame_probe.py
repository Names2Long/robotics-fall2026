from __future__ import annotations
import math, time
from datetime import datetime, timezone
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener
from .common import atomic_json, output_dir

def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
def transform_point(transform,x,y):
    angle=yaw(transform.rotation); c=math.cos(angle); s=math.sin(angle)
    return {"x":transform.translation.x+c*x-s*y,"y":transform.translation.y+s*x+c*y}
def transform_dict(t): return {"translation":{"x":t.translation.x,"y":t.translation.y,"z":t.translation.z},"yaw":yaw(t.rotation)}
class Probe(Node):
    def __init__(self): super().__init__("course_frame_probe"); self.buffer=Buffer(); self.listener=TransformListener(self.buffer,self)
    def capture(self):
        scan=self.buffer.lookup_transform("base_link","base_scan",Time()).transform
        rear=self.buffer.lookup_transform("base_link","rear_camera_link",Time()).transform
        hall=self.buffer.lookup_transform("base_link","hall_camera",Time()).transform
        payload={"schema_version":2,"captured_at":datetime.now(timezone.utc).isoformat(),
                 "frames":["odom","base_link","base_scan","rear_camera_link","hall_camera"],
                 "frame_chain":["hall_camera","odom","base_link","base_scan","rear_camera_link"],
                 "transforms":{"base_scan_to_base_link":transform_dict(scan),
                    "rear_camera_to_base_link":transform_dict(rear),"hall_camera_to_base_link":transform_dict(hall)},
                 "point_prompts":{"hall_camera_point":"Transform point (0.5, 0.0, 0.0) from hall_camera to base_link."},
                 "transformed_points":{"scan_point_in_base":transform_point(scan,1.0,0.0),
                    "rear_camera_point_in_base":transform_point(rear,1.0,0.0),
                    "hall_camera_point_in_base":transform_point(hall,0.5,0.0)}}
        path=output_dir()/"frame_snapshot.json"; atomic_json(path,payload); return path
def main(args=None):
    rclpy.init(args=args); node=Probe(); deadline=time.monotonic()+10
    try:
        while rclpy.ok() and time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=0.2)
            try: path=node.capture(); node.get_logger().info(f"Saved {path}"); return
            except Exception: pass
        raise RuntimeError("Required transforms were not available")
    finally: node.destroy_node(); rclpy.shutdown()
if __name__=="__main__": main()
