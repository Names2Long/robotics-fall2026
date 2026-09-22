"""Validation and reference data for the Lab 3 frame activities."""
from __future__ import annotations
from datetime import datetime,timezone
import math

TRANSFORM_KEYS=("base_scan_to_base_link","rear_camera_to_base_link","hall_camera_to_base_link")


def reference_snapshot():
    return {"source":"reference","captured_at":datetime.now(timezone.utc).isoformat(),
            "description":"Instructor-defined frame geometry. No live ROS transforms were measured.",
            "frames":["odom","base_link","base_scan","rear_camera_link","hall_camera"],
            "transforms":{
                "base_scan_to_base_link":{"translation":{"x":.20,"y":0.,"z":.14},"yaw":0.},
                "rear_camera_to_base_link":{"translation":{"x":-.18,"y":0.,"z":.22},"yaw":math.pi},
                "hall_camera_to_base_link":{"translation":{"x":-1.5,"y":.5,"z":1.2},"yaw":-math.pi/2}}}


def valid_snapshot(snapshot):
    if not isinstance(snapshot,dict) or snapshot.get("source") not in ("live","reference") or not snapshot.get("captured_at"):
        return False
    frames=snapshot.get("frames")
    if not isinstance(frames,list) or not {"odom","base_link","base_scan","rear_camera_link","hall_camera"}.issubset(frames):
        return False
    try:
        for key in TRANSFORM_KEYS:
            item=snapshot["transforms"][key]
            values=(item["yaw"],*(item["translation"][axis] for axis in ("x","y","z")))
            if not all(math.isfinite(float(v)) for v in values): return False
    except (KeyError,TypeError,ValueError): return False
    return True
