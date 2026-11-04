import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lab.evidence import Artifact
from lab.models import make_check
from lab.ui import include_screenshot

ROOT = Path(__file__).resolve().parents[1]


class SubmissionRegressions(unittest.TestCase):
    def test_submission_files_are_not_ignored_but_recovery_and_runtime_are(self):
        prefix = 'week06_slam_localization/'
        normal = [prefix+name for name in ('student_submission/student.json','student_submission/autosave/responses.json',
                  'student_submission/mission_1/map.pgm','student_submission/mission_2/rviz_screenshot.png',
                  'student_submission/final_reflection.md','student_submission/manifest.json')]
        ignored = [prefix+'student_submission/autosave/responses.bak',prefix+'runtime/maps/mission2/rviz.png']
        result = subprocess.run(['git','check-ignore','--no-index','--stdin','-z'],input='\0'.join(normal+ignored)+'\0',
                                text=True,capture_output=True,cwd=ROOT.parent)
        self.assertIn(result.returncode,(0,1),result.stderr)
        self.assertEqual(set(filter(None,result.stdout.split('\0'))),set(ignored))

    def test_screenshot_is_part_of_visible_mission_check(self):
        missing = include_screenshot(make_check('Ready',[]),None)
        self.assertFalse(missing.passed)
        self.assertEqual(missing.requirements[-1].actual,'Not found')
        present = include_screenshot(make_check('Ready',[]),Artifact('rviz.png',b'image'))
        self.assertTrue(present.passed)
        self.assertEqual(present.requirements[-1].actual,'rviz.png')

    def test_both_mission_buttons_follow_screenshot_check_and_saved_fallback(self):
        from streamlit.testing.v1 import AppTest
        first = {'strategy':'perimeter','duration_minutes':8,'metrics':{'known_fraction':.6}}
        second = {'strategy':'rooms','duration_minutes':18,'metrics':{'known_fraction':.7}}
        responses = {key:'Evidence-based response. '*10 for key in (
            'mission_1.limitations','mission_1.drift_and_revisit','mission_1.route.original_prediction',
            'mission_2.comparison','mission_2.map_choice','mission_2.strategy.original_prediction')}
        for mission,record,folder in (('mission_1',first,'mission1'),('mission_2',second,'mission2')):
            with self.subTest(mission=mission), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root/'assets').mkdir()
                shutil.copy2(ROOT/'assets/turtlebot3_house_plan.png',root/'assets/turtlebot3_house_plan.png')
                submission = root/'submission'
                source = ('import streamlit as st\nfrom lab.session import initialize\ninitialize(st)\n'
                          f'st.session_state["evidence"]["mission_1"] = {first!r}\n'
                          f'st.session_state["responses"].update({responses!r})\n'
                          f'from pages.{mission} import render\nrender(st)\n')
                pair = (Artifact('evidence.json',json.dumps(record).encode()),
                        Artifact('map.yaml',b'image: map.pgm\nresolution: 0.05\n'),
                        Artifact('map.pgm',b'P2\n1 1\n255\n254\n'))
                with patch.dict(os.environ,WEEK06_SUBMISSION_DIR=str(submission)), \
                     patch('pages.'+mission+'.ROOT',root), \
                     patch('pages.'+mission+'.prediction',return_value='Saved plan'), \
                     patch('pages.'+mission+'.runtime_map',return_value=pair), \
                     patch('pages.'+mission+'.validate_map_bundle',return_value=({'known_fraction':.7},None)):
                    app = AppTest.from_string(source,default_timeout=30).run()
                    self.assertFalse(app.exception)
                    button = lambda: next(b for b in app.button if b.label=='Check and save Mission '+mission[-1])
                    self.assertTrue(button().disabled)
                    rows = app.dataframe[-1].value
                    screenshot = rows[rows['Requirement']=='RViz screenshot is available'].iloc[0]
                    self.assertEqual(screenshot['Status'],'Not yet')
                    self.assertTrue(any('runtime/maps/'+folder+'/rviz.png' in item.value for item in app.info))
                    path = root/'runtime/maps'/folder/'rviz.png'
                    path.parent.mkdir(parents=True)
                    path.write_bytes(b'recorded screenshot')
                    app.run()
                    self.assertFalse(app.exception)
                    self.assertFalse(button().disabled)
                    button().click().run()
                    self.assertFalse(app.exception)
                    self.assertFalse(app.error)
                    self.assertTrue((submission/mission/'submission.json').is_file())
                    self.assertEqual((submission/mission/'rviz_screenshot.png').read_bytes(),b'recorded screenshot')
                    saved = submission/mission/'rviz_screenshot.png'
                    saved.parent.mkdir(parents=True,exist_ok=True)
                    path.replace(saved)
                    app.run()
                    self.assertFalse(app.exception)
                    self.assertFalse(button().disabled)
