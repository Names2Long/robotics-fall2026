import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from lab.preflight import robot_software_checks


class RobotPreflightTests(unittest.TestCase):
    def test_local_guide_does_not_claim_robot_readiness(self):
        with patch('lab.preflight.Path.is_file',return_value=False), patch('lab.preflight.subprocess.run') as process:
            rows = robot_software_checks()
        self.assertFalse(rows[0]['passed'])
        self.assertFalse(rows[0]['required'])
        process.assert_not_called()

    def test_installed_software_checked_without_launching_simulation(self):
        expected = [{'check':'Built workspace','passed':True,'required':True,'detail':'found'}]
        with patch('lab.preflight.Path.is_file',return_value=True), patch('lab.preflight.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(expected),stderr='')) as process:
            self.assertEqual(robot_software_checks(),expected)
        self.assertTrue(process.call_args.args[0][-1].endswith('check_software.sh'))

    def test_build_failure_is_required_and_actionable(self):
        with patch('lab.preflight.Path.is_file',return_value=True), patch('lab.preflight.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='Build first: colcon build --symlink-install',stderr='')):
            rows = robot_software_checks()
        self.assertFalse(rows[0]['passed'])
        self.assertTrue(rows[0]['required'])
        self.assertIn('Build first',rows[0]['detail'])
