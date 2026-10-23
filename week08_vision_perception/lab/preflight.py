"""Explicit local preflight, scoped to this server launch."""
import importlib
import platform
import sys
import tempfile
import uuid
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from lab.autosave import submission_root

RUN_ID = uuid.uuid4().hex


def robot_software_checks():
    if not Path('/opt/ros/jazzy/setup.bash').is_file():
        return [{'check':'ROS software environment','passed':False,'required':False,
                 'detail':'Not verified by this local guide. Open the guide in the course ROS 2 environment and rerun preflight before Mission 2. Image activities can proceed here.'}]
    script = Path(__file__).resolve().parents[1]/'scripts/check_software.sh'
    try:
        result = subprocess.run(['bash',str(script)],capture_output=True,text=True,timeout=30)
        if result.returncode:
            raise ValueError((result.stdout+result.stderr).strip())
        rows = json.loads(result.stdout)
        if not rows: raise ValueError('No ROS software checks returned')
        return rows
    except (OSError,ValueError,subprocess.TimeoutExpired) as error:
        return [{'check':'ROS software and built workspace','passed':False,'required':True,'detail':str(error)}]


def is_current(report):
    return isinstance(report, dict) and report.get("run_id") == RUN_ID and report.get("ready") is True


def run_checks():
    checks = []
    def check(name, action):
        try:
            detail = action()
            checks.append({"check": name, "passed": True, "detail": str(detail), "required":True})
        except Exception as error:
            checks.append({"check": name, "passed": False, "detail": str(error), "required":True})
    def python_version():
        if sys.version_info < (3, 12):
            raise ValueError("Use Python 3.12 or newer for this lab")
        return platform.python_version() + " at " + sys.executable
    def image_check():
        from perception.dataset import tuning_image
        image = tuning_image()
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("The practice photograph must have three color channels")
        return f"Practice photograph loaded: {image.shape[1]} by {image.shape[0]} pixels"
    def model_check():
        from perception.learned import FrozenDetector
        from perception.dataset import tuning_image
        predictions = FrozenDetector().predict(tuning_image())
        return f"Checksum verified and inference ran: {len(predictions)} cup candidates"
    def writable():
        root = submission_root()
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=root) as target:
            target.write(b"lab7 preflight")
            target.flush()
        return str(root)
    check("Python version and interpreter", python_version)
    for label, module in (("Streamlit", "streamlit"), ("NumPy", "numpy"),
                          ("OpenCV", "cv2"), ("pandas", "pandas"), ("Pillow", "PIL")):
        check("Python package: " + label, lambda name=module: importlib.import_module(name).__version__)
    check("Practice photograph", image_check)
    check("Frozen model and real inference", model_check)
    def representations_check():
        from perception.representations import classify,segment
        from perception.dataset import tuning_image
        image = tuning_image()
        classes = classify(image)
        mask = segment(image)
        return f"Frozen classification and segmentation ran: {classes['top5'][0]['label']}, mask {mask.shape}"
    check('Classification and segmentation models',representations_check)
    def collection_check():
        from perception.experiments import run, validate
        evidence = run('learned')
        validate(evidence, 'learned')
        return f"All {len(evidence['rows'])} scenes checked. Model outputs cached for later activities"
    check('Shared images and prepared model outputs', collection_check)
    check("Submission folder is writable", writable)
    robot_checks = robot_software_checks()
    checks.extend(robot_checks)
    return {"run_id": RUN_ID, "captured_at": datetime.now(timezone.utc).isoformat(),
            "checks": checks, "robot_software_ready":all(row['passed'] for row in robot_checks),
            "ready": all(row["passed"] for row in checks if row.get('required',True))}
