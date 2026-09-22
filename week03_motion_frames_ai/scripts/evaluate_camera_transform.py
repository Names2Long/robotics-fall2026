"""Run course tests and, when available, verify the current live TF tree."""
from __future__ import annotations
import hashlib,json,math,os,re,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];PACKAGE=ROOT/"ros2_ws/src/week03_camera_transform"
SOURCE=PACKAGE/"week03_camera_transform/camera_transform.py";sys.path.insert(0,str(PACKAGE))
sys.path.insert(0,str(ROOT))
from lab.autosave import submission_root


def signature(): return hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.exists() else ""


def live_check():
    try:
        import rclpy
        from geometry_msgs.msg import PointStamped
        from rclpy.node import Node
        from tf2_ros import Buffer,TransformListener
        from week03_camera_transform.camera_transform import transform_camera_point
        rclpy.init();node=Node("camera_transform_evaluator");buffer=Buffer();listener=TransformListener(buffer,node)
        deadline=time.monotonic()+8;result=None;error=""
        while time.monotonic()<deadline and result is None:
            rclpy.spin_once(node,timeout_sec=.1)
            point=PointStamped();point.header.frame_id="hall_camera";point.header.stamp=node.get_clock().now().to_msg();point.point.x=.5
            try: result=transform_camera_point(buffer,point)
            except Exception as exc: error=f"{type(exc).__name__}: {exc}"
        valid=bool(result and result.header.frame_id=="base_link" and all(math.isfinite(v) for v in (result.point.x,result.point.y,result.point.z)))
        payload={"passed":valid,"source":"hall_camera","target":"base_link","point":None if not result else {"x":result.point.x,"y":result.point.y,"z":result.point.z},"error":error}
        node.destroy_node();rclpy.shutdown();return payload
    except Exception as exc: return {"passed":False,"error":f"{type(exc).__name__}: {exc}"}


def main():
    try:
        tests=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(PACKAGE/"test"),"-v"],cwd=PACKAGE,capture_output=True,text=True,timeout=30)
        output=tests.stdout+tests.stderr;passed=tests.returncode==0
    except subprocess.TimeoutExpired: output="Camera tests exceeded 30 seconds.";passed=False
    match=re.search(r"Ran (\d+) tests?",output);count=int(match.group(1)) if match else 0
    live=live_check() if "--live" in sys.argv else {"passed":False,"error":"Live check not requested"}
    original=submission_root()/"mission_2/ai/original_source.py"
    revised=bool(original.exists() and original.read_text(encoding="utf-8").strip()!=SOURCE.read_text(encoding="utf-8").strip())
    payload={"captured_at":datetime.now(timezone.utc).isoformat(),"source_sha256":signature(),"file_present":SOURCE.exists(),
             "unit_tests_passed":passed,"test_count":count,"unit_test_output":output,"live":live,"live_passed":live.get("passed",False)}
    payload["source_differs_from_original"]=revised
    target=ROOT/"runtime/evidence/camera_evaluation.json";target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix(".tmp");temp.write_text(json.dumps(payload,indent=2),encoding="utf-8");temp.replace(target)
    print(output);print(json.dumps(payload,indent=2));return 0 if passed else 1


if __name__=="__main__": raise SystemExit(main())
