from __future__ import annotations

import importlib.util
import csv
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zipfile
from unittest.mock import patch


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
    def test_navigation_does_not_replace_saved_answers_with_hidden_widgets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lab4-save-test-") as folder:
            root = Path(folder)
            state = SimpleNamespace(session_state={
                "stage": "background",
                "_lab4_checkins": {"background_compare": "My original answer."},
            })
            with patch.object(app, "st", state), patch.object(app, "SUBMISSIONS_DIR", root), patch.object(app, "AUTOSAVE_DIR", root / "autosave"), patch.object(app, "AUTOSAVE_RESPONSES_FILE", root / "autosave" / "responses.json"), patch.object(app, "AUTOSAVE_PROGRESS_FILE", root / "autosave" / "progress.json"):
                app.autosave_responses_and_gifs()
                state.session_state["stage"] = "export"
                state.session_state.pop(app.checkin_key("background_compare", "note"), None)
                app.autosave_responses_and_gifs()
                saved = json.loads(app.AUTOSAVE_RESPONSES_FILE.read_text(encoding="utf-8"))
                self.assertEqual("My original answer.", saved["checkins"]["background_compare"])
                self.assertEqual("My original answer.", app.checkin_response("background_compare")["note"])

    def test_older_autosave_restores_and_unreadable_save_is_protected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lab4-recovery-test-") as folder:
            root = Path(folder)
            autosave = root / "autosave"
            autosave.mkdir()
            responses = autosave / "responses.json"
            responses.write_text(json.dumps({"schema_version": 1, "checkins": {"m1_prediction": "An earlier prediction."}, "identity": {"name": "Student"}}), encoding="utf-8")
            state = SimpleNamespace(session_state={})
            with patch.object(app, "st", state), patch.object(app, "SUBMISSIONS_DIR", root), patch.object(app, "AUTOSAVE_DIR", autosave), patch.object(app, "AUTOSAVE_RESPONSES_FILE", responses), patch.object(app, "AUTOSAVE_PROGRESS_FILE", autosave / "progress.json"):
                app.restore_autosave_if_available()
                self.assertEqual("An earlier prediction.", app.checkin_response("m1_prediction")["note"])
                self.assertEqual("Student", state.session_state["_lab4_identity"]["name"])
                responses.write_text("{broken", encoding="utf-8")
                state.session_state.clear()
                app.restore_autosave_if_available()
                self.assertTrue(state.session_state["_recovery_blocked"])
                app.autosave_responses_and_gifs()
                self.assertEqual("{broken", responses.read_text(encoding="utf-8"))

    def test_mission_progress_recovers_previous_valid_snapshot(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lab4-progress-test-") as folder:
            root = Path(folder)
            autosave = root / "autosave"
            autosave.mkdir()
            progress = autosave / "progress.json"
            progress.write_text("{broken", encoding="utf-8")
            progress.with_suffix(".bak").write_text(json.dumps({
                "schema_version": app.LAB_STATE_VERSION,
                "stage": "export",
                "mission_progress": list(app.MISSION_ORDER),
                "missions": {
                    mission: {"passed": True, "result": result}
                    for mission, result in zip(app.MISSION_ORDER, (valid_m1(), valid_m2(), valid_m3()))
                },
            }), encoding="utf-8")
            state = SimpleNamespace(session_state={})
            with patch.object(app, "st", state), patch.object(app, "SUBMISSIONS_DIR", root), patch.object(app, "AUTOSAVE_DIR", autosave), patch.object(app, "AUTOSAVE_RESPONSES_FILE", autosave / "responses.json"), patch.object(app, "AUTOSAVE_PROGRESS_FILE", progress):
                app.restore_autosave_if_available()
                self.assertEqual(list(app.MISSION_ORDER), state.session_state["mission_progress"])
                app.autosave_responses_and_gifs()
                self.assertTrue(list(autosave.glob("progress.unreadable.*.json")))
                self.assertEqual(list(app.MISSION_ORDER), json.loads(progress.read_text(encoding="utf-8"))["mission_progress"])

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

    def test_interactive_odometry_summary_exports_real_saved_measurements(self) -> None:
        result = valid_m2()
        result["params"] = {"forwardInPerTick": 0.05, "strafeInPerTick": 0.052}
        rows = list(csv.DictReader(io.StringIO(app.csv_for_odometry_activity(result))))
        self.assertEqual(1, len(rows))
        self.assertEqual("2.5", rows[0]["max_error_in"])
        self.assertEqual("1.0", rows[0]["final_error_in"])
        self.assertEqual("0.05", rows[0]["forward_in_per_tick"])
        self.assertEqual("0.052", rows[0]["strafe_in_per_tick"])
        with self.assertRaises(ValueError):
            app.csv_for_odometry_activity({"maxError": 1.0})

    def test_final_archive_accepts_a_saved_interactive_odometry_result(self) -> None:
        result = valid_m2()
        archive_bytes = app.build_final_submission_zip(
            {
                "mission_2": {
                    "params": result["params"],
                    "metrics": {"max_error_in": result["maxError"]},
                    "result": result,
                    "csv_files": {"odometry_test_summary.csv": app.csv_for_odometry_activity(result)},
                    "figures": {},
                    "activity_gifs": {},
                },
            },
            {"mission_2": {"analysis": "Complete"}},
            {"final_reflection": "Complete"},
            {"name": "Test Student", "student_id": "test@example.edu", "section": "01"},
        )
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            self.assertIn("mission_2/odometry_test_summary.csv", archive.namelist())
            self.assertNotIn("mission_2/odometry_run.csv", archive.namelist())
            rows = list(csv.DictReader(io.StringIO(
                archive.read("mission_2/odometry_test_summary.csv").decode("utf-8")
            )))
            self.assertEqual("2.5", rows[0]["max_error_in"])


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

    def test_export_page_accepts_a_restored_mission_2_dictionary(self) -> None:
        test_app = self.new_app()
        test_app.session_state["stage"] = "export"
        test_app.session_state["m2_result"] = valid_m2()
        test_app.session_state["m2_passed"] = True
        test_app.run(timeout=25)
        self.assertEqual([], list(test_app.exception))

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

    def test_completed_student_can_revisit_mission_and_save_missing_answer(self) -> None:
        autosave = Path(self.test_output.name) / "autosave"
        autosave.mkdir(parents=True)
        (autosave / "responses.json").write_text(json.dumps({
            "schema_version": app.LAB_STATE_VERSION,
            "checkins": {
                key: "A completed response with evidence."
                for key in app.ALL_CHECKIN_KEYS if key != "m1_prediction"
            },
            "identity": {"name": "Test Student", "student_id": "test@example.edu", "section": "01"},
        }), encoding="utf-8")
        (autosave / "progress.json").write_text(json.dumps({
            "schema_version": app.LAB_STATE_VERSION,
            "stage": "export",
            "mission_progress": list(app.MISSION_ORDER),
            "missions": {
                mission: {"passed": True, "result": result, "params": {}, "metrics": {}}
                for mission, result in zip(app.MISSION_ORDER, (valid_m1(), valid_m2(), valid_m3()))
            },
        }), encoding="utf-8")
        test_app = self.new_app().run(timeout=25)
        self.assertEqual([], list(test_app.exception))
        self.assertTrue(test_app.button(key="review_mission_1"))
        test_app.button(key="review_mission_1").click().run(timeout=25)
        self.assertEqual([], list(test_app.exception))
        self.assertEqual(list(app.MISSION_ORDER), test_app.session_state["mission_progress"])
        test_app.text_area(key=app.checkin_key("m1_prediction", "note")).set_value("My recovered prediction.").run(timeout=25)
        self.assertEqual("My recovered prediction.", test_app.session_state["_lab4_checkins"]["m1_prediction"])
        test_app.button(key="review_export").click().run(timeout=25)
        self.assertEqual([], list(test_app.exception))
        self.assertEqual(list(app.MISSION_ORDER), test_app.session_state["mission_progress"])
        save_button = next(button for button in test_app.button if button.label == "Save complete submission folder")
        self.assertFalse(save_button.disabled)
        save_button.click().run(timeout=25)
        self.assertEqual([], list(test_app.exception))
        saved = json.loads((autosave / "responses.json").read_text(encoding="utf-8"))
        self.assertEqual("My recovered prediction.", saved["checkins"]["m1_prediction"])


if __name__ == "__main__":
    unittest.main()
