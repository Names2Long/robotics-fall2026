import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class PackageTests(unittest.TestCase):
    def test_ros_package_and_entrypoints(self):
        root = Path(__file__).resolve().parents[1] / "ros2_ws" / "src" / "week09_nav_tools"
        self.assertEqual(ET.parse(root / "package.xml").getroot().findtext("name"), "week09_nav_tools")
        setup = (root / "setup.py").read_text(encoding="utf-8")
        for name in ("plan_probe", "navigate_probe", "social_monitor", "experiment_probe"): self.assertIn(name, setup)
        self.assertTrue((root / "launch" / "course_navigation.launch.py").exists())
        self.assertTrue((root / "launch" / "experiment.launch.py").exists())

    def test_experiment_uses_only_required_lifecycle_nodes(self):
        import ast
        root = Path(__file__).resolve().parents[1] / 'ros2_ws/src/week09_nav_tools'
        source = (root/'launch/experiment.launch.py').read_text()
        tree = ast.parse(source)
        helper = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='navigation_nodes')
        names = {n.value for n in ast.walk(helper) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
        self.assertTrue({'controller_server','planner_server','velocity_smoother','collision_monitor'} <= names)
        self.assertFalse({'bt_navigator','docking_server','route_server','waypoint_follower'} & names)
        self.assertIn('localization_launch.py',source)
        probe = (root/'week09_nav_tools/experiment_probe.py').read_text()
        for name in ('controller_server','planner_server','velocity_smoother','collision_monitor'):
            self.assertIn(f"self.wait_active('{name}')",probe)


if __name__ == "__main__": unittest.main()

