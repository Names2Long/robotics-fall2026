import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest


@unittest.skipUnless(importlib.util.find_spec('streamlit'),'Streamlit is not installed')
class MissionTwoUI(unittest.TestCase):
    def test_ai_transform_route_save_and_stale_evidence(self):
        from streamlit.testing.v1 import AppTest
        from missions.mission_2 import REFLECTIONS,current_hash
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);submission=root/'student_submission'
            source=root/'ros2_ws/src/week03_camera_transform/week03_camera_transform/camera_transform.py'
            source.parent.mkdir(parents=True);source.write_text('# revised camera transform')
            result={}
            patches=(patch('lab.camera_ai.submission_root',return_value=submission),
                     patch('lab.submissions.submission_root',return_value=submission),
                     patch('lab.submissions.ROOT',root),patch('pages.mission_2.SOURCE',source),
                     patch('pages.mission_2.camera_evaluation',side_effect=lambda:result))
            with patches[0],patches[1],patches[2],patches[3],patches[4]:
                app=AppTest.from_string('''
import streamlit as st
from lab.session import initialize
from pages.mission_2 import render
initialize(st)
render(st)
''',default_timeout=25).run()
                def click(label):
                    button=next(b for b in app.button if b.label==label);self.assertFalse(button.disabled);button.click().run();self.assertFalse(app.exception)
                click('Use reference frame evidence')
                app.text_area(key='m2.frame_context').set_value('Robot sensors remain rigid while the hallway camera does not move with the robot.').run()
                for key in ('initial_prompt','initial_output','initial_source'):
                    app.text_area(key=f'm2.{key}').set_value('Original AI content').run()
                click('Preserve initial AI response')
                result.update(file_present=True,source_sha256=current_hash(source),unit_tests_passed=True,test_count=5,
                              source_differs_from_original=True,live_passed=True)
                for key in REFLECTIONS[1:]: app.text_area(key=f'm2.{key}').set_value('Evidence-based explanation of frames, AI revision, tests, and consequences.').run()
                click('Refresh camera test evidence')
                click('Check and save Mission 2')
                self.assertTrue((submission/'mission_2/source/week03_camera_transform/camera_transform.py').exists())
                click('Continue to Mission 3');self.assertEqual(app.session_state['stage'],'mission_3')
                source.write_text('# changed after evaluation')
                app.run();self.assertTrue(next(b for b in app.button if b.label=='Check and save Mission 2').disabled)
