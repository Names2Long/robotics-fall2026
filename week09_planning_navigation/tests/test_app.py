import os
from pathlib import Path
import tempfile
import unittest
import json
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from planning.core import EXPERIMENT_VERSION


class AppTests(unittest.TestCase):
    def test_five_playground_activities(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WEEK09_SUBMISSION_DIR':folder}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
            app.button(key='navigation1').click().run(timeout=30)
            self.assertFalse(app.exception)
            app.button(key='toy_show_plan').click().run(timeout=30)
            self.assertFalse(app.exception)
            app.button(key='tutorial_next').click().run(timeout=30)
            app.slider(key='toy_neighbor_row').set_value(3).run(timeout=30)
            self.assertFalse(app.exception)
            app.button(key='tutorial_next').click().run(timeout=30)
            self.assertFalse(app.exception)
            before = app.session_state['demo_frame']
            app.button(key='demo_step').click().run(timeout=30)
            self.assertEqual(app.session_state['demo_frame'],before+1)
            app.button(key='demo_play').click().run(timeout=30)
            self.assertTrue(app.session_state['demo_playing'])
            app.button(key='demo_play').click().run(timeout=30)
            self.assertFalse(app.session_state['demo_playing'])
            app.button(key='demo_end').click().run(timeout=30)
            self.assertEqual(app.session_state['demo_frame'],len(app.session_state['demo_trace']['frames'])-1)
            app.selectbox(key='demo_method').select('iddfs').run(timeout=30)
            self.assertFalse(app.exception)
            app.button(key='tutorial_next').click().run(timeout=30)
            self.assertFalse(app.exception)
            app.select_slider(key='weighted_entry_cost').set_value(1.2).run(timeout=30)
            app.button(key='tutorial_next').click().run(timeout=30)
            self.assertFalse(app.exception)
            app.radio(key='teaching_radius').set_value('0.30 m').run(timeout=30)
            self.assertFalse(app.exception)
            app.button(key='tutorial_back').click().run(timeout=30)
            self.assertEqual(app.session_state['settings']['planning_activity'],3)

    def test_individual_small_check_uses_saved_student_code(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WEEK09_SUBMISSION_DIR':folder}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
            app.button(key='navigation3').click().run(timeout=30)
            source = Path(folder)/'mission_1/planners.py'
            self.assertTrue(source.exists())
            self.assertFalse(any(b.label=='Save Python source' for b in app.button))
            source.write_text('def bfs(ctx):\n    return [ctx.start] if ctx.start == ctx.goal else []\n')
            app.button(key='run_small_check').click().run(timeout=30)
            self.assertFalse(app.exception)
            result = app.session_state['evidence']['small_check']
            self.assertEqual(result['case'],'Start equals goal')
            self.assertTrue(result['check_passed'])
            self.assertTrue((Path(folder)/'mission_1/latest_small_check.json').exists())

    def test_measured_trial_page_and_charts(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WEEK09_SUBMISSION_DIR':str(Path(folder)/'submission')}):
            trial = Path(folder)/'runtime/trials/unit_fixture'
            trial.mkdir(parents=True)
            fixture = dict(schema=2,experiment_version=EXPERIMENT_VERSION,mission='2',run_id='unit_fixture',map='open',planner='bfs',
                seed=0,condition='baseline',status='succeeded',planning_s=.1,elapsed_s=2,distance_m=.2,
                path=[[-3.875,-2.875],[-3.625,-2.875]],trajectory=[{'x':-3.875,'y':-2.875,'t':0},{'x':-3.625,'y':-2.875,'t':2}])
            (trial/'result.json').write_text(json.dumps(fixture))
            from lab import application
            with patch.object(application,'ROOT',Path(folder)):
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
                app.button(key='navigation4').click().run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(app.dataframe)
                next(b for b in app.button if b.label=='Retain this checkpoint for my analysis').click().run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue((Path(folder)/'submission/mission_2/route_inspection.json').exists())

    def test_all_four_offline_maps_are_visible(self):
        from planning.experiments import cases
        from planning.core import reference_path
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WEEK09_SUBMISSION_DIR':folder}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
            rows = []
            for name,(grid,start,goal) in cases().items():
                path = reference_path(grid,start,goal)
                rows.append(dict(map=name,planner='bfs',status='succeeded' if path else 'no_path',path=path))
            app.session_state['evidence'] = {'offline_draft':{'rows':rows}}
            app.button(key='navigation3').click().run(timeout=30)
            self.assertFalse(app.exception)
            self.assertFalse(any(s.label=='Inspect search paths' for s in app.selectbox))

    def test_social_sliders_and_single_archive(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WEEK09_SUBMISSION_DIR':folder}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
            app.button(key='navigation5').click().run(timeout=30)
            app.slider(key='social_1.gain').set_value(.2).run(timeout=30)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.slider),6)
            self.assertFalse(any(s.key=='social_map' for s in app.selectbox))
            next(b for b in app.button if b.label=='Save field settings for robot trials').click().run(timeout=30)
            fields = json.loads((Path(folder)/'mission_3/potential_fields.json').read_text())
            self.assertEqual(fields['social_1']['human_gain'],.2)
            app.button(key='navigation6').click().run(timeout=30)
            next(b for b in app.button if b.label=='Save and prepare ZIP').click().run(timeout=30)
            self.assertFalse(app.exception)
            self.assertTrue(app.session_state['submission_zip'].startswith(b'PK'))
            self.assertFalse(any('draft' in b.label.lower() for b in app.button))

    def test_pages_and_resume(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WEEK09_SUBMISSION_DIR':folder}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
            self.assertFalse(app.exception)
            for index in range(1,7):
                app.button(key=f'navigation{index}').click().run(timeout=30)
                self.assertFalse(app.exception,msg=f'Page {index}')
                if index==3:
                    app.text_area(key='answer.mission_1.search').input('Preserve this analysis when revisiting.').run(timeout=30)
                    app.button(key='navigation4').click().run(timeout=30)
                    app.button(key='navigation3').click().run(timeout=30)
                    self.assertEqual(app.text_area(key='answer.mission_1.search').value,'Preserve this analysis when revisiting.')
            second = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
            self.assertFalse(second.exception)
            self.assertEqual(second.session_state['stage'],'final')


if __name__ == '__main__':
    unittest.main()
