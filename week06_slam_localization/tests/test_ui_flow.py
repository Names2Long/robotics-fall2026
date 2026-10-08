import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class PreflightIdentityTests(unittest.TestCase):
    def test_lab_ends_after_second_mapping_mission(self):
        from app import PAGES, access_map
        from lab_config import LAB

        self.assertEqual(LAB.missions, ("mission_1", "mission_2"))
        self.assertEqual(LAB.stages[-3:], ("mission_1", "mission_2", "final"))
        self.assertNotIn("mission_3", PAGES)
        state = SimpleNamespace(session_state={
            "student": {"name": "Student", "email": "student@example.edu"},
            "tutorial_complete": {},
            "evidence": {},
        })
        with patch("app.preflight.is_current", return_value=False):
            self.assertTrue(access_map(state, {"mission_1": True, "mission_2": True})["final"])

    def test_existing_container_gets_stable_process_run_id(self):
        from pages.preflight import current_run_id, is_current

        with patch.dict(os.environ, {"COURSE_LAB_RUN_ID": ""}):
            first = current_run_id()
            self.assertEqual(first, current_run_id())
            self.assertTrue(is_current({"ready": True, "run_id": first}))
            self.assertFalse(is_current({"ready": True, "run_id": "earlier-launch"}))

    def test_tutorial_three_owns_mapping_and_rviz_launch(self):
        root = Path(__file__).resolve().parents[1]
        tutorial = (root / "pages" / "tutorials.py").read_text(encoding="utf-8")
        mission = (root / "pages" / "mission_1.py").read_text(encoding="utf-8")
        second = (root / "pages" / "mission_2.py").read_text(encoding="utf-8")
        self.assertIn("bash scripts/launch_mapping.sh", tutorial)
        self.assertIn("bash scripts/launch_rviz.sh", tutorial)
        self.assertIn("change **Keep** from 100 to **1**", tutorial)
        self.assertNotIn("bash scripts/launch_mapping.sh", mission)
        self.assertNotIn('\\nrviz2", language="bash"', mission)
        self.assertLess(second.index("bash scripts/reset_mapping.sh"), second.index("bash scripts/launch_mapping.sh"))


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit is not installed")
class StudentGuideUI(unittest.TestCase):
    def test_pgm_preview_renders(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_string(
            "import streamlit as st\n"
            "from lab.ui import show_map\n"
            "class Image:\n"
            "    def getvalue(self): return b'P5\\n2 1\\n255\\n\\x0a\\xfe'\n"
            "show_map(st, Image(), 'Test map')\n"
        ).run()
        self.assertFalse(app.exception, str(app.exception))

    def test_intro_tutorial_navigation_and_restart(self):
        from streamlit.testing.v1 import AppTest

        source = Path(__file__).resolve().parents[1] / "app.py"
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"WEEK06_SUBMISSION_DIR": directory}), patch.object(sys, "argv", [str(source)]):
            app = AppTest.from_file(str(source), default_timeout=30).run()
            self.assertFalse(app.exception)
            for key, value in (
                ("student.name", "Test Student"),
                ("student.email", "student@example.edu"),
            ):
                app.text_input(key=key).set_value(value).run()
            self.assertFalse(any("Course ID" in widget.label for widget in app.text_input))
            app.button(key="page.next").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["stage"], "tutorial_1")
            self.assertFalse(any(key.startswith("field.tutorial_") for key in app.session_state))
            app.slider(key="t1.heading_bias").set_value(10).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state["t1.history"]), 2)
            app.slider(key="t1.moves").set_value(6).run()
            self.assertEqual(len(app.session_state["t1.history"]), 3)
            app.button(key="page.next").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["stage"], "tutorial_2")
            app.button(key="page.back").click().run()
            self.assertEqual(app.session_state["stage"], "tutorial_1")
            app.button(key="page.next").click().run()
            app.slider(key="t2.endpoint").set_value(8).run()
            for control in ("t2.ray_count", "t2.limit", "t2.sparse_count", "t2.free_count", "t2.hit_count"):
                self.assertTrue(app.slider(key=control))
            self.assertTrue(app.select_slider(key="t2.cell_size"))
            app.button(key="page.next").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["stage"], "preflight")
            self.assertTrue(app.button(key="page.next").disabled)
            restarted = AppTest.from_file(str(source), default_timeout=30).run()
            self.assertFalse(restarted.exception)
            self.assertEqual(restarted.session_state["stage"], "preflight")
            self.assertEqual(restarted.session_state["student"]["name"], "Test Student")
            self.assertTrue(restarted.session_state["tutorial_complete"]["tutorial_2"])

    def test_previous_final_page_remains_revisitable_when_evidence_stales(self):
        from streamlit.testing.v1 import AppTest
        from lab.autosave import save
        from lab.session import initialize

        source = Path(__file__).resolve().parents[1] / "app.py"
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"WEEK06_SUBMISSION_DIR": directory}
        ), patch.object(sys, "argv", [str(source)]):
            st = SimpleNamespace(session_state={})
            initialize(st)
            st.session_state["stage"] = "mission_1"
            st.session_state["visited_stages"] = ["intro", "mission_1", "final"]
            save(st)
            app = AppTest.from_file(str(source), default_timeout=30).run()
            self.assertFalse(app.exception)
            self.assertFalse(app.button(key="nav.final").disabled)
            app.button(key="nav.final").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["stage"], "final")

    def test_old_preflight_does_not_unlock_next_launch(self):
        from streamlit.testing.v1 import AppTest
        from lab.autosave import save
        from lab.session import initialize

        source = Path(__file__).resolve().parents[1] / "app.py"
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            "WEEK06_SUBMISSION_DIR": directory, "COURSE_LAB_RUN_ID": "new-launch",
        }), patch.object(sys, "argv", [str(source)]):
            st = SimpleNamespace(session_state={})
            initialize(st)
            st.session_state["stage"] = "preflight"
            st.session_state["evidence"]["preflight"] = {"ready": True, "run_id": "old-launch"}
            save(st)
            app = AppTest.from_file(str(source), default_timeout=30).run()
            self.assertFalse(app.exception, str(app.exception))
            self.assertTrue(app.button(key="page.next").disabled)
            self.assertFalse(app.file_uploader)

    def test_all_guided_tutorials_are_visual_and_have_no_answer_boxes(self):
        from streamlit.testing.v1 import AppTest
        from lab.autosave import save
        from lab.session import initialize

        source = Path(__file__).resolve().parents[1] / "app.py"
        for stage in ("tutorial_1", "tutorial_2", "tutorial_3"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory, patch.dict(
                os.environ, {"WEEK06_SUBMISSION_DIR": directory}
            ), patch.object(sys, "argv", [str(source)]):
                st = SimpleNamespace(session_state={})
                initialize(st)
                st.session_state["stage"] = stage
                save(st)
                app = AppTest.from_file(str(source), default_timeout=30).run()
                self.assertFalse(app.exception, str(app.exception))
                self.assertFalse(app.text_area)
                self.assertTrue(app.button(key="page.next"))

    def test_each_mission_and_final_page_render_without_ros(self):
        from streamlit.testing.v1 import AppTest
        from lab.autosave import save
        from lab.evidence import evidence_id
        from lab.session import initialize

        source = Path(__file__).resolve().parents[1] / "app.py"
        first = {"strategy": "perimeter_then_interior", "duration_minutes": 7,
                 "metrics": {"known_fraction": .5, "resolution": .05}, "quality_score": 65}
        second = {"strategy": "room_by_room", "duration_minutes": 7,
                  "metrics": {"known_fraction": .6, "resolution": .05}, "quality_score": 70}
        for stage in ("mission_1", "mission_2", "final"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory, patch.dict(
                os.environ, {"WEEK06_SUBMISSION_DIR": directory}
            ), patch.object(sys, "argv", [str(source)]):
                st = SimpleNamespace(session_state={})
                initialize(st)
                st.session_state["stage"] = stage
                st.session_state["student"] = {"name": "Test", "email": "test@example.edu"}
                st.session_state["evidence"].update(preflight={"ready": True}, mission_1=first, mission_2=second)
                st.session_state["tutorial_complete"] = {
                    "tutorial_1": True, "tutorial_2": True, "tutorial_3": True,
                }
                for activity, context in (
                    ("mission_1.route", {"world": "turtlebot3_house", "run": 1}),
                    ("mission_2.strategy", {"first_evidence_id": evidence_id(first), "world": "turtlebot3_house"}),
                ):
                    st.session_state["prediction_locks"][activity] = {
                        "context_signature": evidence_id(context), "text": "A saved prediction before the trial."
                    }
                save(st)
                app = AppTest.from_file(str(source), default_timeout=30).run()
                self.assertFalse(app.exception, str(app.exception))


if __name__ == "__main__":
    unittest.main()
