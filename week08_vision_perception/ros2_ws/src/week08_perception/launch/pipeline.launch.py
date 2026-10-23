"""Detector-only inspection. No command publisher or physical robot launch."""
import json
import os
from pathlib import Path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    root = Path(os.environ["WEEK08_LAB_ROOT"])
    submission = Path(os.environ.get("WEEK08_SUBMISSION_DIR",str(root/"student_submission")))
    mode,camera = LaunchConfiguration("mode"),LaunchConfiguration("camera_topic")
    classical = {"camera_topic":camera}
    learned = {"camera_topic":camera,"model_path":LaunchConfiguration("model_path")}
    if (submission/"mission_1/evidence.json").exists():
        data = json.loads((submission/"mission_1/evidence.json").read_text())
        classical.update(data["settings"])
        classical["implementation_json"] = ParameterValue(json.dumps(data.get("implementation") or {}),value_type=str)
    if (submission/"mission_2/evidence.json").exists():
        data = json.loads((submission/"mission_2/evidence.json").read_text())
        learned["confidence_threshold"] = float(data['selected_threshold'])
        learned['nms_iou'] = float(data.get('nms_iou',.45))
    return LaunchDescription([
        DeclareLaunchArgument("mode",default_value="classical"),
        DeclareLaunchArgument("camera_topic",default_value="/camera/image_raw"),
        DeclareLaunchArgument("model_path",default_value=str(root/"assets/models/detector.onnx")),
        Node(package="week08_perception",executable="classical_detector",parameters=[classical],
             condition=IfCondition(PythonExpression(["'",mode,"' == 'classical'"]))),
        Node(package="week08_perception",executable="learned_detector",parameters=[learned],
             condition=IfCondition(PythonExpression(["'",mode,"' == 'learned'"]))),
    ])
