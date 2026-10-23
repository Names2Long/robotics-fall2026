import unittest,xml.etree.ElementTree as ET
from pathlib import Path
class PackageTests(unittest.TestCase):
    def test_ros_packages(self):
        root=Path(__file__).resolve().parents[1]/"ros2_ws"/"src"
        for name in ("week08_interfaces","week08_perception","course_cmd_vel_guard"):self.assertEqual(ET.parse(root/name/"package.xml").getroot().findtext("name"),name)
        self.assertTrue((root/"week08_interfaces"/"msg"/"TargetObservation.msg").exists());self.assertTrue((root/"week08_perception"/"launch"/"pipeline.launch.py").exists())
        self.assertEqual(ET.parse(root/"week08_interfaces"/"package.xml").getroot().findtext("export/build_type"), "ament_cmake")
        self.assertIn("std_msgs", [item.text for item in ET.parse(root/"week08_perception"/"package.xml").getroot().findall("exec_depend")])
if __name__=="__main__":unittest.main()
