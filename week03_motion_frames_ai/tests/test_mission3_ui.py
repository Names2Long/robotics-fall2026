import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest


@unittest.skipUnless(importlib.util.find_spec('streamlit'),'Streamlit is not installed')
class MissionThreeUI(unittest.TestCase):
    def test_preserve_review_save_with_pending_live(self):
        from streamlit.testing.v1 import AppTest
        from lab.ai_log import load_lock
        from missions.mission_3 import REFLECTIONS,current_hash
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'ros2_ws/src/week03_pattern'; output=root/'student_submission'
            for relative in ('week03_pattern/pattern.py','week03_pattern/pattern_node.py','test/test_student_pattern.py'):
                path=source/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# Revised implementation\n')
            result={}
            with patch('lab.ai_log.submission_root',return_value=output),patch('lab.submissions.submission_root',return_value=output),patch('lab.submissions.ROOT',root),patch('pages.mission_3.SOURCE_ROOT',source),patch('pages.mission_3.ai_evaluation',side_effect=lambda:result):
                app=AppTest.from_string('''
import streamlit as st
from lab.session import initialize
from pages.mission_3 import render
initialize(st)
render(st)
''',default_timeout=25).run()
                def click(label):
                    b=next(b for b in app.button if b.label==label);self.assertFalse(b.disabled);b.click().run();self.assertFalse(app.exception)
                app.text_area(key='m3.specification').set_value('Sequence, limits, stop, and expected distances.').run();click('Save specification')
                for key in ('original_prompt','original_output','original_source'):
                    app.text_area(key=f'm3.{key}').set_value('Original AI content').run()
                click('Preserve original AI interaction')
                lock=load_lock();self.assertTrue(lock['integrity_valid'])
                result.update(pattern=lock['pattern'],source_sha256=current_hash(source),unit_tests_passed=True,test_count=9,
                    shape_check_passed=True,commands_bounded=True,model_stop_passed=True,source_differs_from_original=True,
                    implementation_present=True,student_test_file_present=True,student_test_count=2,integration_passed=False)
                for key in REFLECTIONS:
                    app.text_area(key=f'm3.{key}').set_value('Evidence and explanation of this development decision.').run()
                app.checkbox[0].check().run()
                app.text_area(key='m3.live_issue').set_value('ROS unavailable; live path and stop remain unverified.').run()
                click('Check and save Mission 3')
                self.assertTrue((output/'mission_3/source/test/test_student_pattern.py').exists())
                self.assertTrue((output/'mission_3/ai/ai_to_final.diff').exists())
                click('Continue to final submission')
                self.assertEqual(app.session_state['stage'],'final')
