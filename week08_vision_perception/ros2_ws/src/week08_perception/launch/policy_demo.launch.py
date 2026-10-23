from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import json
import os
from pathlib import Path
from evaluation.behavior import BehaviorConfig
from dataclasses import asdict


def generate_launch_description():
    root = Path(os.environ.get("WEEK08_SUBMISSION_DIR", str(Path(os.environ["WEEK08_LAB_ROOT"])/"student_submission")))
    evidence = root/"mission_3"/"evidence.json"
    config = asdict(BehaviorConfig())
    seed = {}
    if evidence.exists():
        saved = json.loads(evidence.read_text())
        config = asdict(BehaviorConfig(**saved["config"]))
        seed = saved.get("seed",{})
    print("Policy demo settings:", config)
    remaps = [("/perception/target", "/lab7/perception/target"),
              ("/student_cmd_vel", "/lab7/student_cmd_vel"),
              ("/cmd_vel", "/lab7/cmd_vel"),
              ("/perception/policy_state", "/lab7/policy_state")]
    return LaunchDescription([
        Node(package="week08_perception", executable="policy_demo", remappings=remaps,parameters=[{"seed_json":ParameterValue(json.dumps(seed),value_type=str)}]),
        Node(package="week08_perception", executable="target_behavior", remappings=remaps, parameters=[config]),
        Node(package="course_cmd_vel_guard", executable="guard", remappings=remaps),
    ])
