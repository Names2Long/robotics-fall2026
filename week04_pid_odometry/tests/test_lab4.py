from __future__ import annotations

import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zipfile


LAB_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = LAB_ROOT / "app.py"
TEST_OUTPUT = tempfile.TemporaryDirectory(prefix="lab4-tests-")
os.environ["LAB4_SUBMISSIONS_DIR"] = TEST_OUTPUT.name

SPEC = importlib.util.spec_from_file_location("week04_lab_app", APP_PATH)
assert SPEC and SPEC.loader
app = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = app
SPEC.loader.exec_module(app)


def valid_m1() -> dict:
    return {
        "activityComplete": True,
        "params": {"kp1": 6, "ki1": 0.5, "kd1": 1, "kp2": 6, "ki2": 0.5, "kd2": 1},
        "metrics": {"posesHeld": 3, "posesRequired": 3},
    }


def valid_m2() -> dict:
    return {
        "passed": True,
        "maxError": 2.5,
        "finalError": 1.0,
        "params": {"forwardScale": 0.05, "strafeScale": 0.05},
    }


def valid_m3() -> dict:
    return {
        "drove": True,
        "passed": True,
        "route": [[0.5, 0.1], [1.15, 0.35], [1.15, 1.05], [1.95, 1.05], [1.55, 2.05]],
        "trace": [[0, 0, 0, 0, 0, 0, 0], [1, 1, 1, 0, 1, 1, 0]],
        "metrics": {
            "mission_waypoints_reached": 4,
            "mission_waypoint_total": 4,
            "min_pedestrian_gap": 0.35,
            "safe_radius": 0.28,
            "mean_tracking_error": 0.04,
            "mean_tracking_limit": 0.05,
            "max_tracking_error": 0.09,
            "max_tracking_limit": 0.10,
        },
    }


class ValidationTests(unittest.TestCase):
    def test_mission_validators_accept_good_results(self) -> None:
        self.assertTrue(app.validate_mission_1_result(valid_m1())[0])
        self.assertTrue(app.validate_mission_2_result(valid_m2())[0])
        self.assertTrue(app.validate_mission_3_result(valid_m3())[0])

    def test_mission_validators_reject_client_pass_without_evidence(self) -> None:
        self.assertFalse(app.validate_mission_1_result({"activityComplete": True})[0])
        self.assertFalse(app.validate_mission_2_result({"passed": True, "maxError": 3.1})[0])
        unsafe = valid_m3()
        unsafe["metrics"]["min_pedestrian_gap"] = 0.10
        self.assertFalse(app.validate_mission_3_result(unsafe)[0])

    def test_route_coordinate_parser(self) -> None:
        route = app.parse_route_coordinates(app.ACCESSIBLE_ROUTE_EXAMPLE)
        self.assertGreaterEqual(len(route), 4)
        with self.assertRaises(ValueError):
            app.parse_route_coordinates("1.0\n2.0, 3.0")

    def test_changed_evidence_invalidates_that_mission_and_later_work(self) -> None:
        original_streamlit = app.st
        app.st = SimpleNamespace(session_state={
            "mission_progress": list(app.MISSION_ORDER),
            "m1_passed": True,
            "m2_passed": True,
            "m2_result": valid_m2(),
            "m3_passed": True,
            "m3_result": valid_m3(),
        })
        try:
            app.invalidate_mission_and_following("mission_2")
            self.assertEqual(["mission_1"], app.st.session_state["mission_progress"])
            self.assertIsNone(app.st.session_state["m2_passed"])
            self.assertIsNone(app.st.session_state["m3_passed"])
            self.assertNotIn("m2_result", app.st.session_state)
            self.assertNotIn("m3_result", app.st.session_state)
        finally:
            app.st = original_streamlit

    def test_final_archive_contains_versioned_manifest(self) -> None:
        archive_bytes = app.build_final_submission_zip(
            {
                "mission_1": {"csv_files": {}, "figures": {}, "activity_gifs": {}},
                "mission_2": {"csv_files": {}, "figures": {}, "activity_gifs": {}},
                "mission_3": {"csv_files": {}, "figures": {}, "activity_gifs": {}},
            },
            {mission: {"analysis": "complete"} for mission in app.MISSION_ORDER},
            {"final_reflection": "A short reflection."},
            {"name": "Test Student", "student_id": "test@example.edu", "section": "01"},
        )
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            self.assertIn("manifest.json", archive.namelist())
            self.assertIn("submission.json", archive.namelist())
            self.assertIn("final_reflection.md", archive.namelist())


class StreamlitFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from streamlit.testing.v1 import AppTest

        cls.AppTest = AppTest

    def setUp(self) -> None:
        self.test_output = tempfile.TemporaryDirectory(prefix="lab4-ui-test-")
        os.environ["LAB4_SUBMISSIONS_DIR"] = self.test_output.name

    def tearDown(self) -> None:
        self.test_output.cleanup()

    def new_app(self):
        return self.AppTest.from_file(str(APP_PATH), default_timeout=25)

    def test_all_pages_and_missions_render(self) -> None:
        test_app = self.new_app()
        for stage in (
            "intro", "environment", "pid_concepts", "background",
            "pid_playground", "odom_background", "export",
        ):
            test_app.session_state["stage"] = stage
            test_app.run(timeout=25)
            self.assertEqual([], list(test_app.exception), stage)
        for mission in app.MISSION_ORDER:
            test_app.session_state["stage"] = "lab"
            test_app.session_state["mission_override"] = mission
            prediction_key = {
                "mission_1": "m1_prediction",
                "mission_2": "m2_prediction",
                "mission_3": "m3_prediction",
            }[mission]
            test_app.session_state[app.checkin_key(prediction_key, "note")] = "A saved prediction."
            test_app.run(timeout=25)
            self.assertEqual([], list(test_app.exception), mission)

    def test_intro_has_no_student_skip_button(self) -> None:
        test_app = self.new_app().run(timeout=25)
        labels = [button.label for button in test_app.button]
        self.assertIn("Check environment and begin", labels)
        self.assertNotIn("Skip to lab", labels)

    def test_final_save_stays_disabled_when_missions_are_incomplete(self) -> None:
        test_app = self.new_app()
        test_app.session_state["stage"] = "export"
        test_app.session_state[app.checkin_key("final_reflection", "note")] = "Reflection complete."
        test_app.session_state["export_student_name"] = "Test Student"
        test_app.session_state["export_student_id"] = "test@example.edu"
        test_app.run(timeout=25)
        save_buttons = [button for button in test_app.button if button.label == "Save complete submission folder"]
        self.assertEqual(1, len(save_buttons))
        self.assertTrue(save_buttons[0].disabled)

    def test_autosave_is_restored_in_a_new_session(self) -> None:
        response_key = app.checkin_key("background_compare", "note")
        first_session = self.new_app()
        first_session.session_state["stage"] = "background"
        first_session.session_state[response_key] = "My restored comparison."
        first_session.run(timeout=25)
        self.assertEqual([], list(first_session.exception))

        second_session = self.new_app().run(timeout=25)
        self.assertEqual([], list(second_session.exception))
        self.assertEqual("background", second_session.session_state["stage"])
        self.assertEqual(
            "My restored comparison.",
            second_session.session_state[response_key],
        )


if __name__ == "__main__":
    unittest.main()
