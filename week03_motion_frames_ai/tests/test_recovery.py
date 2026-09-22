from datetime import datetime,timezone,timedelta
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
from unittest.mock import patch
import unittest
from lab.autosave import save,load_state,restore


class AutosaveRecovery(unittest.TestCase):
    def test_restore_previous_valid_copy(self):
        with tempfile.TemporaryDirectory() as directory,patch('lab.autosave.ROOT',Path(directory)):
            state={'responses':{'answer':'first'},'student':{},'stage':'mission_1','walkthrough.index':3}
            st=SimpleNamespace(session_state=state)
            path=save(st)
            state['responses']['answer']='second';state['stage']='mission_2';save(st)
            path.write_text('{incomplete',encoding='utf-8')
            restored=load_state()
            self.assertEqual(restored['responses']['answer'],'first')
            fresh=SimpleNamespace(session_state={});restore(fresh)
            self.assertEqual(fresh.session_state['stage'],'mission_1')
            self.assertEqual(fresh.session_state['walkthrough.index'],3)
            self.assertIn('previous saved copy',fresh.session_state['recovery_note'])

    def test_unreadable_state_does_not_look_like_new_student(self):
        with tempfile.TemporaryDirectory() as directory,patch('lab.autosave.ROOT',Path(directory)):
            path=save(SimpleNamespace(session_state={'responses':{},'student':{}}))
            path.write_text('bad',encoding='utf-8')
            self.assertIn('could not be read',load_state()['recovery_note'])


@unittest.skipUnless(importlib.util.find_spec('streamlit'),'Streamlit is not installed')
class PreflightUI(unittest.TestCase):
    def test_setup_and_old_checks_do_not_claim_live_ready(self):
        from streamlit.testing.v1 import AppTest
        result={'scope':'setup','ready':True,'checks':[],'captured_at':datetime.now(timezone.utc).isoformat()}
        with patch('pages.preflight.preflight',side_effect=lambda:result):
            app=AppTest.from_string('''
import streamlit as st
from lab.session import initialize
from pages.preflight import render
initialize(st)
render(st)
''').run()
            def continue_button(): return next(b for b in app.button if b.label=='Continue to Mission 1')
            self.assertTrue(continue_button().disabled)
            result['scope']='live';app.run();self.assertFalse(continue_button().disabled)
            result['captured_at']=(datetime.now(timezone.utc)-timedelta(minutes=10)).isoformat()
            app.run();self.assertTrue(continue_button().disabled)
