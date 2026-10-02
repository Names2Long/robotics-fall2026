import os,tempfile,unittest,subprocess,sys,socket,time
from urllib.request import urlopen
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from fixtures import valid_state,PREDICTION
from lab.autosave import save,read_json
from lab.completion import mission_status
from lab.submissions import manifest_current

APP=Path(__file__).resolve().parents[1]/'app.py'

class StudentJourneyTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.environment=patch.dict(os.environ,{'WEEK05_SUBMISSION_DIR':self.folder.name});self.environment.start()
        self.arguments=patch('sys.argv',[str(APP)]);self.arguments.start()
    def tearDown(self):
        self.arguments.stop();self.environment.stop();self.folder.cleanup()
    def run_app(self):
        app=AppTest.from_file(str(APP),default_timeout=30).run()
        self.assertFalse(app.exception);return app
    def click(self,app,label):
        next(b for b in app.button if b.label==label).click().run()
        self.assertFalse(app.exception)
    def test_new_student_walkthrough_navigation_and_restart(self):
        app=self.run_app()
        for key,value in [('name','Student'),('email','student@example.test'),('course_id','new-student')]:
            app.text_input(key='identity.'+key).set_value(value)
        app.run();self.click(app,'Begin walkthroughs')
        for index in range(4):
            self.click(app,'Mark reviewed')
            if index<3: self.click(app,'Next walkthrough')
        self.click(app,'Previous walkthrough');self.click(app,'Next walkthrough')
        self.click(app,'Continue to Mission 1')
        app.text_area(key='field.mission_1.prediction_draft').set_value(PREDICTION).run()
        self.click(app,'Save prediction for these settings')
        app.text_input(key='field.mission_1.mean').set_value('2.1').run()
        resumed=self.run_app()
        self.assertEqual(resumed.session_state['stage'],'mission_1')
        self.assertEqual(resumed.text_input(key='field.mission_1.mean').value,'2.1')
        self.click(resumed,'Back');self.click(resumed,'Back')
        self.assertTrue(resumed.text_input(key='identity.course_id').disabled)
    def test_all_mission_pages_save_export_and_stale_controls(self):
        state=valid_state();state.session_state['stage']='mission_1'
        state.session_state['responses']['mission_1.prediction_draft']=PREDICTION
        save(state);app=self.run_app();self.click(app,'Save prediction for these settings')
        self.click(app,'Check and save Mission 1');self.click(app,'Continue to Mission 2')
        self.click(app,'Check and save Mission 2');self.click(app,'Continue to Mission 3')
        self.click(app,'Check and save Mission 3');self.click(app,'Continue to submission')
        self.click(app,'Prepare submission')
        manifest=read_json(Path(self.folder.name)/'manifest.json')
        self.assertTrue(manifest)
        self.assertTrue(all(mission_status(type('State',(),{'session_state':app.session_state})()).values()))
        resumed=self.run_app();self.assertEqual(resumed.session_state['stage'],'final')
        self.assertTrue(manifest_current(type('State',(),{'session_state':resumed.session_state})()))
        self.click(resumed,'Decide')
        resumed.slider(key='control.Warehouse.margin').set_value(.45).run()
        self.assertFalse(resumed.session_state['completed_missions'] and 'mission_3' in resumed.session_state['completed_missions'])
        self.assertTrue(any('earlier settings' in w.value for w in resumed.warning))
    def test_record_controlled_experiments_and_predicted_policy_revisions(self):
        state=valid_state();state.session_state['stage']='mission_2'
        state.session_state['mission_2_attempts']=[]
        state.session_state['responses']['mission_2.selected']=0
        state.session_state['mission_3_results']={};state.session_state['mission_3_attempts']={};state.session_state['mission_3_controls']={}
        save(state);app=self.run_app()
        configs=[('Moving average',w,.25) for w in (3,7,11)]+[('Median',3,w) for w in (.25,.5,.75)]
        for method,window,weight in configs:
            app.selectbox(key='control.m2.method').set_value(method)
            app.slider(key='control.m2.window').set_value(window)
            app.slider(key='control.m2.weight_a').set_value(weight)
            app.run();app.text_area(key='field.mission_2.prediction_draft').set_value(PREDICTION).run()
            self.click(app,'Save prediction for these settings');self.click(app,'Record this configuration')
        self.assertEqual(len(app.session_state['mission_2_attempts']),6)
        self.click(app,'Decide')
        for context,margin in [('Warehouse',.15),('Assistive',.25)]:
            app.button(key='baseline.'+context).click().run();self.assertFalse(app.exception)
            app.text_area(key='field.mission_3.'+context+'.prediction_draft').set_value(PREDICTION).run()
            app.button(key='predict.mission_3.'+context).click().run()
            app.button(key='test.'+context).click().run()
            app.slider(key='control.'+context+'.margin').set_value(margin).run()
            self.assertTrue(app.button(key='test.'+context).disabled)
            app.button(key='predict.mission_3.'+context).click().run()
            app.button(key='test.'+context).click().run();self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state['mission_3_attempts'][context]),2)
            self.assertEqual(len(app.session_state['mission_3_results'][context]['traces']),7)
    def test_corrupt_save_does_not_get_replaced(self):
        path=Path(self.folder.name)/'autosave/responses.json';path.parent.mkdir();path.write_text('broken')
        app=self.run_app();self.assertTrue(app.error)
        self.assertEqual(path.read_text(),'broken')

    def test_real_streamlit_server_starts_and_answers_health_check(self):
        with socket.socket() as available:
            available.bind(('127.0.0.1',0));port=available.getsockname()[1]
        process=subprocess.Popen([sys.executable,'-m','streamlit','run',str(APP),'--global.developmentMode=false','--server.headless=true','--server.address=127.0.0.1','--server.port='+str(port),'--browser.gatherUsageStats=false'],cwd=APP.parent,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+20;healthy=False
            while time.monotonic()<deadline and process.poll() is None:
                try:
                    with urlopen(f'http://127.0.0.1:{port}/_stcore/health',timeout=1) as response:
                        healthy=response.status==200 and response.read()==b'ok'
                    if healthy: break
                except OSError: time.sleep(.1)
            if not healthy and process.poll() is not None:
                self.fail(process.stdout.read().decode('utf-8',errors='replace'))
            self.assertTrue(healthy,'Streamlit did not become healthy within 20 seconds')
        finally:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill();process.wait(timeout=5)
            process.stdout.close()

if __name__=='__main__': unittest.main()
