from __future__ import annotations
import json, os, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def succeeds(*command):
    try: return subprocess.run(command, capture_output=True, text=True, timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired): return False
def main():
    output = ROOT / "runtime" / "evidence"; output.mkdir(parents=True, exist_ok=True)
    checks = [
        {"check": "ROS distribution", "passed": os.environ.get("ROS_DISTRO") == "jazzy", "detail": os.environ.get("ROS_DISTRO", "not sourced")},
        {"check": "ros2 command", "passed": shutil.which("ros2") is not None, "detail": shutil.which("ros2") or "missing"},
        {"check": "ROS_DOMAIN_ID", "passed": os.environ.get("ROS_DOMAIN_ID") == "26", "detail": os.environ.get("ROS_DOMAIN_ID", "not set") + " (expected 26 for course launcher)"},
        {"check": "RViz command", "passed": shutil.which("rviz2") is not None, "detail": shutil.which("rviz2") or "missing"},
    ]
    for package in ("turtlebot3_gazebo", "turtlebot3_teleop", "slam_toolbox", "nav2_map_server", "course_slam_tools"):
        checks.append({"check": f"Package: {package}", "passed": succeeds("ros2", "pkg", "prefix", package), "detail": package})
    payload = {"schema_version": 2, "run_id": os.environ.get("COURSE_LAB_RUN_ID"), "captured_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "ready": all(item["passed"] for item in checks)}
    (output / "preflight.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for item in checks: print(f"{item['check']:<38} {'PASS' if item['passed'] else 'FAIL':<5} {item['detail']}")
    raise SystemExit(0 if payload["ready"] else 1)
if __name__ == "__main__": main()
