import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def test_robot_settings_import_navigation_and_restart(self):
        import shutil
        from test_live_vision import report_fixture
        scratch = ROOT/'runtime/test_scratch'
        scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            fake = Path(folder)
            (fake/'assets/robot_worlds').mkdir(parents=True)
            shutil.copy2(ROOT/'assets/robot_worlds/track.png',fake/'assets/robot_worlds/track.png')
            for kind,worlds in (('pillar_search',('pillars',)),('line_following',('practice','track'))):
                for world in worlds:
                    target = fake/'runtime/robot_runs'/kind/world/'run.json'
                    target.parent.mkdir(parents=True)
                    target.write_text(json.dumps(report_fixture(kind,world)))
            with patch.dict(os.environ,WEEK08_SUBMISSION_DIR=str(fake/'submission')), patch('pages.robot_missions.ROOT',fake):
                app = AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
                for kind,worlds in (('pillar_search',('pillars',)),('line_following',('practice','track'))):
                    app.button(key='nav.'+kind).click().run()
                    self.assertFalse(app.exception)
                    if kind=='line_following':
                        self.assertFalse(app.slider)
                        self.assertIn('GAIN = 0.08',app.text_area(key='code.line_following').value)
                    app.button(key=kind+'.save').click().run()
                    self.assertTrue((fake/'submission'/kind/'settings.json').exists())
                    if kind=='line_following': self.assertTrue((fake/'submission'/kind/'controller.py').exists())
                    for world in worlds:
                        path = fake/'runtime/robot_runs'/kind/world/'run.json'
                        prefix = kind if kind=='pillar_search' else kind+'.'+world
                        app.selectbox(key=prefix+'.attempt').select(path).run()
                        app.button(key=prefix+'.keep').click().run()
                        self.assertFalse(app.exception)
                    for area in app.text_area: area.set_value('The saved images and commands explain this attempt.')
                    app.run()
                fresh = AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
                self.assertFalse(fresh.exception)
                self.assertEqual(len(fresh.session_state['evidence']['line_following']['reports']),2)
                from lab.completion import mission_ready
                self.assertTrue(mission_ready(fresh.session_state,'pillar_search')[0])
                self.assertTrue(mission_ready(fresh.session_state,'line_following')[0])

    def test_complete_experiments_restart_and_export(self):
        scratch = ROOT/'runtime/test_scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory, patch.dict(os.environ, WEEK08_SUBMISSION_DIR=directory):
            app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=90).run()
            app.text_input(key='student.name').set_value('Test learner')
            app.text_input(key='student.email').set_value('test-id').run()
            def press(label):
                next(b for b in app.button if b.label == label).click().run()
                self.assertFalse(app.exception, label)
                self.assertFalse(app.error, label)
            app.button(key='nav.investigation').click().run()
            self.assertFalse(any(b.key == 'nav.mission_3' for b in app.button))
            press('Run detector on practice photograph')
            press('Lock settings and evaluate all images')
            for field in app.text_area: field.set_value('The mask and contour evidence explain the result on normal_1 and dim_1.')
            app.run()
            press('Continue to B. Learned representations')
            press('Load prepared model results')
            next(s for s in app.slider if s.label == 'Classification cup-score threshold').set_value(.2).run()
            app.button(key='learned.next').click().run()
            next(s for s in app.slider if s.label == 'NMS overlap threshold').set_value(.35).run()
            app.button(key='learned.next').click().run()
            next(s for s in app.slider if s.label == 'Segmentation foreground threshold').set_value(.6).run()
            app.button(key='learned.next').click().run()
            self.assertFalse(app.exception)
            press('Continue to C. Compare and choose')
            self.assertFalse(app.exception)
            self.assertTrue(any('Correct boxes' in list(table.value) for table in app.dataframe))
            app.selectbox[1].select('classical').run()
            press('Save detector comparison')
            saved = app.session_state['evidence']['mission_2']
            self.assertEqual(saved['classification_threshold'], .2)
            self.assertEqual(saved['segmentation_threshold'], .6)
            self.assertEqual(saved['nms_iou'], .35)
            self.assertEqual(saved['preferred_method'], 'classical')
            self.assertEqual(saved['comparison_conditions'], ['normal','dim','occluded'])
            for field in app.text_area: field.set_value('The condition counts and paired images support a limited recommendation. The foreground mask does not label mugs.')
            app.run()
            started = time.perf_counter()
            app.selectbox(key='comparison.image').select('dim_1').run()
            elapsed = time.perf_counter()-started
            print(f'\nPaired-scene AppTest rerender: {elapsed:.3f}s', flush=True)
            self.assertFalse(app.exception)
            from test_live_vision import report_fixture
            for kind,worlds in (('pillar_search',('pillars',)),('line_following',('practice','track'))):
                app.session_state['evidence'][kind] = {'kind':kind,'reports':[report_fixture(kind,w) for w in worlds]}
                for key in ('diagnosis','evidence') if kind == 'pillar_search' else ('comparison','limits'):
                    app.session_state['responses'][kind+'.'+key] = 'Recorded camera and command evidence support this explanation.'
            app.button(key='nav.final').click().run()
            self.assertEqual(len(app.text_area),2)
            self.assertFalse(any('Deployment Readiness Check' in x.value for x in app.subheader))
            for field in app.text_area: field.set_value('These controlled image tests support limited claims. Further camera, depth and safety tests are needed before deployment.')
            app.run()
            press('Finalize verified submission')
            manifest = json.loads((Path(directory)/'manifest.json').read_text())
            self.assertEqual(manifest['status'], 'complete')
            self.assertFalse(any(r['item'].startswith('deployment.') for r in manifest['checks']))
            self.assertNotIn('deployment_readiness.md',manifest['required_files'])
            self.assertFalse(any(r['item'] == 'mission_3' for r in manifest['checks']))
            for name in ('mission_1/executed_code.py','mission_1/images/dim_1_raw_mask.png',
                         'mission_2/images/normal_1_segmentation.png','mission_2/detection_pr.svg',
                         'mission_2/classification_predictions.csv','mission_2/segmentation_metrics.csv'):
                self.assertTrue((Path(directory)/name).is_file(), name)
            damaged = Path(directory)/'mission_1/images/dim_1_raw_mask.png'
            damaged.unlink()
            press('Finalize verified submission')
            self.assertTrue(damaged.is_file())
            fresh = AppTest.from_file(str(ROOT/'app.py'), default_timeout=60).run()
            self.assertFalse(fresh.exception)
            self.assertEqual(fresh.session_state['stage'], 'final')
            from lab.completion import readiness
            self.assertTrue(all(r['ready'] for r in readiness(fresh.session_state)))
            fresh.session_state['evidence']['mission_1']['settings']['min_area'] += 1
            self.assertFalse(all(r['ready'] for r in readiness(fresh.session_state)))

    def test_documented_scripts_work_from_another_directory(self):
        for name in ('evaluate_perception.py','evaluate_behavior.py'):
            result = subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/name), '--help'], cwd=tempfile.gettempdir(), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_navigation_and_restart_preserve_draft(self):
        target = ROOT/'runtime/test_scratch'
        target.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target) as directory, patch.dict(os.environ, WEEK08_SUBMISSION_DIR=directory):
            app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()
            self.assertFalse(app.exception)
            app.text_input(key='student.name').set_value('Test learner').run()
            app.button(key='nav.investigation').click().run()
            app.text_area(key='field.mission_1.diagnosis').set_value('I compared masks and contours.').run()
            app.button(key='nav.concepts').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.text_area), 0)
            app.button(key='nav.investigation').click().run()
            self.assertEqual(app.text_area(key='field.mission_1.diagnosis').value, 'I compared masks and contours.')
            fresh = AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()
            self.assertFalse(fresh.exception)
            self.assertEqual(fresh.session_state['stage'], 'investigation')
            self.assertEqual(fresh.text_area(key='field.mission_1.diagnosis').value, 'I compared masks and contours.')
            for stage in ('preflight','concepts','pillar_search','line_following','final','intro'):
                fresh.button(key='nav.'+stage).click().run()
                self.assertFalse(fresh.exception, stage)
