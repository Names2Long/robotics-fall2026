import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit is not installed")
class MissionOneUI(unittest.TestCase):
    def test_prediction_backup_save_and_continue(self):
        from streamlit.testing.v1 import AppTest
        from missions.mission_1 import REFLECTIONS
        app=AppTest.from_string('''
import streamlit as st
from lab.session import initialize
from pages.mission_1 import render
initialize(st)
st.session_state['responses'].setdefault('mission_1.sketch', {'mime':'image/png','data':'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aXioAAAAASUVORK5CYII='})
render(st)
''',default_timeout=25).run()
        self.assertFalse(app.exception)
        for name in ('straight','turn_then_drive','arc'):
            self.assertFalse(any(b.key==f'model.{name}' for b in app.button))
            app.text_area(key=f'm1.description.{name}').set_value('I predict a path and an unchanged heading.').run()
            next(b for b in app.button if b.label=='Save prediction').click().run()
            self.assertFalse(app.exception)
            app.button(key=f'model.{name}').click().run()
            self.assertFalse(app.exception)
            app.text_area(key=f'm1.mission_1.compare.{name}').set_value('My heading was wrong; the modeled path changes orientation.').run()
        for key in REFLECTIONS:
            app.text_area(key=f'm1.mission_1.{key}').set_value('A specific explanation using the trial evidence.').run()
        with tempfile.TemporaryDirectory() as directory, patch('lab.submissions.submission_root', return_value=Path(directory)):
            save=next(b for b in app.button if b.label=='Check and save Mission 1')
            self.assertFalse(save.disabled)
            save.click().run()
            self.assertFalse(app.exception)
            self.assertTrue((Path(directory)/'mission_1/prediction_sketch.png').exists())
            payload=(Path(directory)/'mission_1/submission.json').read_text()
            self.assertIn('live_verification_pending',payload)
            self.assertIn('modeled',payload)
            next(b for b in app.button if b.label=='Continue to Mission 2').click().run()
            self.assertEqual(app.session_state['stage'],'mission_2')
