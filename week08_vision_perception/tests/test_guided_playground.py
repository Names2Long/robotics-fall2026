import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class GuidedPlaygroundTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT/"runtime/test_scratch"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.env = patch.dict(os.environ, WEEK08_SUBMISSION_DIR=self.temp.name)
        self.env.start()
        self.app = AppTest.from_file(str(ROOT/"app.py"), default_timeout=60).run()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def press(self, key):
        self.app.button(key=key).click().run()
        self.assertFalse(self.app.exception)
        self.assertFalse(self.app.error)

    def test_steps_require_run_and_preserve_progress(self):
        self.press("nav.concepts")
        self.assertTrue(self.app.button(key="lesson.next").disabled)
        self.assertTrue(self.app.button(key="footer.next").disabled)
        self.assertEqual(len(self.app.text_area), 0)
        from pages.concepts import STEPS
        for step in range(len(STEPS)):
            self.assertEqual(self.app.session_state["settings"]["playground_progress"]["step"], step)
            self.assertTrue(self.app.button(key="lesson.next").disabled)
            self.press("lesson.run")
            self.assertFalse(self.app.button(key="lesson.next").disabled)
            from perception.dataset import tuning_image
            import numpy as np
            self.assertTrue(np.array_equal(self.app.session_state['lesson_output']['values']['image'], tuning_image()))
            if step == 8:
                previous = self.app.session_state["lesson_output"]["values"]["raw_mask"].copy()
                self.app.slider(key="lesson.value").set_value((200, 255)).run()
                self.assertTrue(self.app.button(key="lesson.next").disabled)
                self.assertIn("np.array([0, 70, 200])", self.app.code[0].value)
                self.press("lesson.run")
                current = self.app.session_state["lesson_output"]["values"]["raw_mask"]
                self.assertTrue((previous != current).any())
            if step in (9, 10, 11, 12):
                import cv2
                fixed = cv2.inRange(cv2.cvtColor(tuning_image(), cv2.COLOR_BGR2HSV), np.array([0,70,25]), np.array([35,255,180]))
                values = self.app.session_state['lesson_output']['values']
                self.assertTrue(np.array_equal(values['raw_mask'], fixed))
                for size in (1,3,9): self.assertIn('kernel_'+str(size), values)
            if step == 13:
                values = self.app.session_state['lesson_output']['values']
                for name in ('erosion','dilation','opening','closing'): self.assertIn(name,values)
            if step == 15:
                values = self.app.session_state['lesson_output']['values']
                self.assertNotEqual(values['box_center'], values['centroid'])
                self.assertEqual(values['detail'].ndim, 3)
            self.press("lesson.next")
        self.assertTrue(self.app.session_state["settings"]["playground_progress"]["finished"])
        self.assertFalse(self.app.button(key="footer.next").disabled)
        fresh = AppTest.from_file(str(ROOT/"app.py"), default_timeout=60).run()
        self.assertEqual(fresh.session_state["settings"]["playground_progress"]["step"], len(STEPS)-1)
        self.assertTrue(fresh.session_state["settings"]["playground_progress"]["finished"])
        self.app = fresh
        self.press("lesson.back")
        self.assertEqual(self.app.session_state["settings"]["playground_progress"]["step"], len(STEPS)-2)

    def test_mission_runs_complete_code_without_expression_fields(self):
        self.press("nav.investigation")
        self.assertTrue(next(b for b in self.app.button if b.label == "Lock settings and evaluate all images").disabled)
        self.assertFalse(any("implementation." in field.key for field in self.app.text_area))
        next(b for b in self.app.button if b.label == "Run detector on practice photograph").click().run()
        self.assertFalse(self.app.exception)
        shown = self.app.code[0].value
        next(b for b in self.app.button if b.label == "Lock settings and evaluate all images").click().run()
        self.assertFalse(self.app.exception)
        evidence = self.app.session_state["evidence"]["mission_1"]
        self.assertEqual(shown, evidence["program"])
        self.assertIsNone(evidence["implementation"])
        self.assertTrue((Path(self.temp.name)/"mission_1/executed_code.py").is_file())
        self.app.slider(key="classicalv").set_value((200, 255)).run()
        self.assertTrue(next(b for b in self.app.button if b.label == "Lock settings and evaluate all images").disabled)

    def test_preflight_runs_explicitly_and_rejects_old_launch(self):
        self.press("nav.preflight")
        self.assertTrue(self.app.button(key="footer.next").disabled)
        self.assertNotIn("preflight_report", self.app.session_state["settings"])
        self.press("preflight.run")
        report = self.app.session_state["settings"]["preflight_report"]
        self.assertTrue(report["ready"], report["checks"])
        self.assertFalse(self.app.button(key="footer.next").disabled)
        self.app.session_state["settings"]["preflight_report"]["run_id"] = "previous-server-launch"
        self.app.run()
        self.assertTrue(self.app.button(key="footer.next").disabled)
        self.assertTrue(any("earlier server launch" in item.value for item in self.app.info))

    def test_part_a_responses_gate_parts_b_and_c_without_selector(self):
        self.press('nav.investigation')
        self.assertFalse(self.app.radio)
        self.assertTrue(self.app.button(key='investigation.next').disabled)
        self.app.text_area(key='field.mission_1.diagnosis').set_value('A mask result.').run()
        self.assertTrue(self.app.button(key='investigation.next').disabled)
        self.app.text_area(key='field.mission_1.limitations').set_value('A limitation.').run()
        self.assertFalse(self.app.button(key='investigation.next').disabled)
        self.press('investigation.next')
        self.assertEqual(self.app.session_state['settings']['investigation_part'],1)
        self.press('investigation.back')
        self.app.text_area(key='field.mission_1.limitations').set_value(' ').run()
        self.app.session_state['settings']['investigation_part'] = 2
        self.app.run()
        self.assertEqual(self.app.session_state['settings']['investigation_part'],0)

    def test_old_collection_does_not_hide_saved_answers(self):
        from perception.experiments import run
        evidence = run('classical')
        evidence['dataset'] = 'earlier-collection'
        self.app.session_state['evidence']['mission_1'] = evidence
        self.app.session_state['responses']['mission_1.diagnosis'] = 'Earlier mask explanation'
        self.press('nav.investigation')
        self.assertEqual(self.app.text_area(key='field.mission_1.diagnosis').value, 'Earlier mask explanation')
        self.assertTrue(any('Earlier answers remain below' in item.value for item in self.app.info))
