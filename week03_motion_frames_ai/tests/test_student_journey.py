"""Exercise the whole guide with reference evidence and real Python evaluation."""
import base64
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
import unittest
import zipfile
from types import SimpleNamespace

LAB_ROOT=Path(__file__).resolve().parents[1]
PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aXioAAAAASUVORK5CYII='


@unittest.skipUnless(importlib.util.find_spec('streamlit'),'Streamlit is not installed')
class StudentJourney(unittest.TestCase):
    def test_complete_reference_route_and_resume(self):
        from streamlit.testing.v1 import AppTest
        from missions import mission_1,mission_2,mission_3
        from lab.completion import mission_status
        from lab.submissions import submission_zip
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for folder in ('lab','scripts','ros2_ws/src/week03_pattern','ros2_ws/src/week03_camera_transform'):
                shutil.copytree(LAB_ROOT/folder,root/folder,ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copy2(LAB_ROOT/'lab_config.py',root/'lab_config.py')
            package=root/'ros2_ws/src/week03_pattern'
            camera_package=root/'ros2_ws/src/week03_camera_transform'
            camera_source=camera_package/'week03_camera_transform/camera_transform.py'
            camera_source.write_text('''def transform_camera_point(tf_buffer,point):
    if point.header.frame_id != "hall_camera": raise ValueError("wrong source")
    try: return tf_buffer.transform(point,"base_link")
    except Exception: return None
''',encoding='utf-8')
            # Test-only reference implementation; real starter remains unfinished.
            pattern=package/'week03_pattern/pattern.py'
            pattern.write_text('''import math
from dataclasses import dataclass
@dataclass(frozen=True)
class Segment:
    linear_x: float
    angular_z: float
    duration: float
def build_pattern(name):
    if name=='l_path': return [Segment(.1,0,4),Segment(0,.5,math.pi),Segment(.1,0,4)]
    if name=='alternating_arcs': return [Segment(.15,w,math.pi/2) for w in (.5,-.5,.5,-.5)]
    if name=='rounded_rectangle':
        result=[]
        for d in (.4,.25,.4,.25): result.extend([Segment(.1,0,d/.1),Segment(.075,.5,math.pi)])
        return result
    raise ValueError(name)
''',encoding='utf-8')
            (package/'test/test_student_pattern.py').write_text('''import os,unittest
from week03_pattern.pattern import build_pattern
from week03_pattern.checks import shape_ok,command_at
class StudentTests(unittest.TestCase):
    def test_geometry(self):
        name=os.environ['WEEK03_ASSIGNED_PATTERN'];self.assertTrue(shape_ok(name,build_pattern(name)))
    def test_stop(self):
        s=build_pattern(os.environ['WEEK03_ASSIGNED_PATTERN']);self.assertEqual(command_at(s,sum(x.duration for x in s)),(0,0))
''',encoding='utf-8')
            with patch('lab.autosave.ROOT',root),patch('lab.submissions.ROOT',root),patch('lab.evidence.ROOT',root),patch('lab.completion.SOURCE_ROOT',package),patch('lab.completion.CAMERA_SOURCE',camera_source),patch('pages.mission_2.SOURCE',camera_source),patch('pages.mission_3.SOURCE_ROOT',package):
                app=AppTest.from_string('from app import run_streamlit_app\nrun_streamlit_app()',default_timeout=30).run()
                def click(label):
                    button=next(b for b in app.button if b.label==label)
                    self.assertFalse(button.disabled,label);button.click().run();self.assertFalse(app.exception)
                def fill(key,text): app.text_area(key=key).set_value(text).run();self.assertFalse(app.exception)
                next(t for t in app.text_input if t.label=='Full name').set_value('Test Student').run()
                next(t for t in app.text_input if t.label=='Hunter email').set_value('test@example.test').run()
                click('Begin')
                for i,keys in enumerate((('forward','turn','arc','stop'),('equal','left_turn','right_turn','opposite'),(),('ideal_measure','changed_measure'),())):
                    for key in keys: app.button(key=key).click().run()
                    if i==2: app.slider[0].set_value(-.8).run();click('Use reference snapshot for this walkthrough')
                    if i==4: click('Inspect the proposed code');click('Run the decision and boundary tests')
                    click('Mark reviewed')
                    if i<4: click('Next walkthrough')
                click('Continue to environment preflight')
                app.text_input(key='environment.issue').set_value('Simulator unavailable in this test').run()
                click('Continue with reference activities')
                # AppTest cannot upload files; inject the same saved payload as a PNG upload.
                app.session_state['responses']['mission_1.sketch']={'mime':'image/png','data':PNG}
                for name in ('straight','turn_then_drive','arc'):
                    fill('m1.description.'+name,'My original predicted path and orientation.')
                    click('Save prediction');app.button(key='model.'+name).click().run()
                    fill('m1.mission_1.compare.'+name,'The imposed speed change explains the modeled difference.')
                    if name!='arc': click('Save analysis and continue')
                for key in mission_1.REFLECTIONS: fill('m1.mission_1.'+key,'My explanation and a measurable criterion using evidence.')
                click('Check and save Mission 1');click('Continue to Mission 2')
                click('Use reference frame evidence')
                fill('m2.frame_context','The robot sensors remain rigid while the hallway camera stays in the environment.')
                for key in ('initial_prompt','initial_output','initial_source'): fill('m2.'+key,'Preserved initial AI camera-transform content.')
                click('Preserve initial AI response')
                camera_result={'file_present':True,'source_sha256':mission_2.current_hash(camera_source),'unit_tests_passed':True,
                               'test_count':5,'source_differs_from_original':True,'live_passed':False}
                evidence=root/'runtime/evidence';evidence.mkdir(parents=True,exist_ok=True)
                (evidence/'camera_evaluation.json').write_text(json.dumps(camera_result),encoding='utf-8')
                for key in mission_2.REFLECTIONS[1:]: fill('m2.'+key,'The frame, AI revision, and test evidence explain the expected result and safe fallback.')
                app.checkbox[0].check().run();fill('m2.live_issue','No simulator in this reference-route test.')
                click('Check and save Mission 2');click('Continue to Mission 3')
                fill('m3.specification','Sequence, speeds, stopping, and measurable expected results.');click('Save specification')
                for key in ('original_prompt','original_output','original_source'): fill('m3.'+key,'Preserved original AI content before revision.')
                click('Preserve original AI interaction')
                evaluation=subprocess.run([sys.executable,str(root/'scripts/evaluate_ai_pattern.py')],cwd=root,capture_output=True,text=True,timeout=45)
                self.assertEqual(evaluation.returncode,0,evaluation.stdout+evaluation.stderr)
                click('Refresh test evidence')
                for key in mission_3.REFLECTIONS: fill('m3.'+key,'My documented review, revisions, tests, and limitations.')
                app.checkbox[0].check().run();fill('m3.live_issue','No simulator; live path and stop are unverified.')
                click('Check and save Mission 3');click('Continue to final submission')
                current_status=mission_status(SimpleNamespace(session_state=app.session_state))
                self.assertTrue(all(current_status.values()),(current_status,app.session_state['checked_evidence_ids'],
                    json.loads((root/'student_submission/mission_2/submission.json').read_text())['evidence']['evidence_id'],
                    sorted(str(p.relative_to(root)) for p in (root/'student_submission/mission_2').rglob('*') if p.is_file())))
                fill('final.synthesis.widget','A robot should communicate its intention and respect pedestrians. '*12)
                fill('field.final.course_reflection','I learned to connect motion evidence with human expectations.')
                click('Save reflection and update word count');click('Prepare submission')
                archive=zipfile.ZipFile(io.BytesIO(submission_zip()))
                self.assertIn('synthesis.md',archive.namelist());self.assertIn('final_reflection.md',archive.namelist())
                manifest=json.loads(archive.read('manifest.json'))
                self.assertEqual(len(manifest['live_verification_pending']),5)
                self.assertFalse(any(n.startswith('autosave/') for n in archive.namelist()))
                resumed=AppTest.from_string('from app import run_streamlit_app\nrun_streamlit_app()',default_timeout=30).run()
                self.assertEqual(resumed.session_state['stage'],'final');self.assertFalse(resumed.exception)
                self.assertTrue(all(mission_status(SimpleNamespace(session_state=resumed.session_state)).values()))
                # Editing source must invalidate final readiness, even after restart.
                pattern.write_text(pattern.read_text()+'\n# changed after evaluation\n')
                resumed.run();self.assertFalse(mission_status(SimpleNamespace(session_state=resumed.session_state))['mission_3'])
                self.assertTrue(next(b for b in resumed.button if b.label=='Prepare submission').disabled)
