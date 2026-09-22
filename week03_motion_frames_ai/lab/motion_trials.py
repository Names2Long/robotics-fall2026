"""Bounded live execution and explicitly labeled teaching-model alternatives."""
from __future__ import annotations
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shlex
import signal
import subprocess
import uuid

from simulation.kinematics import SEQUENCES, Segment, integrate_segment, integrate_sequence, pose_error

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def modeled_trial(name, prediction_id):
    segments = SEQUENCES[name]
    pose = (0.0, 0.0, 0.0)
    samples = [list(pose)]
    for segment in segments:
        n = max(1, round(segment.duration * 30))
        for _ in range(n):
            pose = integrate_segment(*pose, Segment(segment.linear_x*.92, segment.angular_z*.93, segment.duration/n))
            samples.append(list(pose))
    observed = dict(zip(("x", "y", "theta"), pose))
    return {"sequence_id": name, "prediction_id": prediction_id, "trial_id": uuid.uuid4().hex,
            "captured_at": now(), "source": "modeled", "completed": True,
            "stop_sent": False, "modeled_stop": True, "live_verified": False,
            "model_description": "Ideal planar integration with 92% translation and 93% rotation; imposed teaching differences, not measured noise.",
            "start_pose": {"x": 0., "y": 0., "theta": 0.}, "end_pose": observed,
            "observed_pose": observed, "predicted_pose": integrate_sequence(segments),
            "samples": samples, "duration": sum(s.duration for s in segments),
            **pose_error(integrate_sequence(segments), observed)}


def run_live(name, prediction_id):
    if name not in SEQUENCES:
        raise ValueError("Unknown motion trial")
    if os.name != "posix" or not Path("/opt/ros/jazzy/setup.bash").exists():
        return None, "The live run needs the course ROS Docker environment. You can use the labeled model below."
    directory = ROOT / "runtime" / "evidence"
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "mission1_running.lock"
    import fcntl
    fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None, "Another trial is running. Wait for it to finish before retrying."
    trial_id = uuid.uuid4().hex
    output = directory / f"trial_{trial_id}.json"
    command = (f"source /opt/ros/jazzy/setup.bash && source {shlex.quote(str(ROOT / 'ros2_ws/install/setup.bash'))} && "
               f"export ROS_DOMAIN_ID=25 && python3 {shlex.quote(str(ROOT / 'scripts/run_mission1_trial.py'))} "
               f"{name} {trial_id} {shlex.quote(prediction_id)} {shlex.quote(str(output))}")
    try:
        proc = subprocess.Popen(["bash", "-lc", command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, start_new_session=True)
        try:
            log, _ = proc.communicate(timeout=65)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
            return None, "The trial timed out. Its motion and stop could not be verified. Keep the simulator stopped while recovering, or use modeled evidence."
        if proc.returncode != 0 or not output.exists():
            return None, "The live trial did not finish. " + log[-1800:]
        result = json.loads(output.read_text(encoding="utf-8"))
        if result.get("trial_id") != trial_id or result.get("prediction_id") != prediction_id:
            return None, "The evidence did not match this attempt. Retry or use the model."
        return result, ""
    except (OSError, ValueError) as error:
        return None, f"The live trial could not be read: {error}"
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
