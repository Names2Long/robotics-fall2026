import copy,hashlib,json,os,tempfile,unittest,zipfile,io
from pathlib import Path
from unittest.mock import patch
from fixtures import valid_state
from lab.autosave import save,load_state,submission_root,read_json,write_json
from lab.completion import current_check,refresh_completion
from lab.session import complete_mission
from lab.submissions import save_mission,write_manifest,manifest_current,submission_zip
from lab.final_reflection import write_final_reflection

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.environment=patch.dict(os.environ,{'WEEK05_SUBMISSION_DIR':self.directory.name});self.environment.start();self.addCleanup(self.environment.stop)

    def save_all(self,st):
        with patch('lab.submissions.png_bytes',return_value=b'test-only image'):
            for mission in ('mission_1','mission_2','mission_3'):
                check,signature,evidence=current_check(st,mission);self.assertTrue(check.passed)
                save_mission(mission,evidence,st.session_state['responses'],state_signature=signature,rows=[{'sample':0,'value':2}],figure=object() if mission!='mission_3' else None)
                complete_mission(st,mission,signature)
        save(st)

    def test_resume_preserves_page_controls_selected_attempt_and_history(self):
        st=valid_state();save(st);restored=load_state()
        for key in ('stage','mission_2_controls','mission_3_controls','mission_3_attempts','responses'): self.assertEqual(restored[key],st.session_state[key])
        path=submission_root()/'autosave/responses.json';first=path.read_bytes();save(st);self.assertEqual(first,path.read_bytes())

    def test_corrupt_primary_recovers_backup_and_preserves_unreadable_file(self):
        st=valid_state();save(st);st.session_state['responses']['note']='new';save(st)
        path=submission_root()/'autosave/responses.json';path.write_text('{broken')
        recovered=load_state();self.assertIn('recovery_note',recovered);self.assertNotIn('note',recovered['responses'])
        st.session_state.update(recovered);save(st)
        self.assertTrue(list(path.parent.glob('responses.unreadable.*.json')))

    def test_no_valid_save_blocks_without_overwriting(self):
        path=submission_root()/'autosave/responses.json';path.parent.mkdir();path.write_text('{broken')
        data=load_state();self.assertTrue(data['recovery_blocked'])
        st=valid_state();st.session_state.update(data)
        with self.assertRaises(OSError): save(st)
        self.assertEqual(path.read_text(),'{broken')

    def test_legacy_answers_retained_but_old_completion_requires_recheck(self):
        st=valid_state();save(st);path=submission_root()/'autosave/responses.json';data=read_json(path);data['content_version']=1;write_json(path,data)
        restored=load_state();self.assertEqual(restored['responses'],data['responses']);self.assertEqual(restored['completed_missions'],[])
        self.assertEqual(restored['legacy_evidence']['mission_2_attempts'],data['mission_2_attempts'])
        self.assertEqual(restored['mission_2_attempts'],[])

    def test_structurally_invalid_primary_preserves_previous_valid_backup(self):
        st=valid_state();save(st);st.session_state['responses']['note']='new';save(st)
        path=submission_root()/'autosave/responses.json';backup=path.with_suffix('.bak').read_bytes()
        path.write_text('[]');st.session_state.update(load_state());save(st)
        self.assertEqual(path.with_suffix('.bak').read_bytes(),backup)
        self.assertTrue(list(path.parent.glob('responses.unreadable.*.json')))

    def test_changed_submission_evidence_invalidates_completion(self):
        st=valid_state();self.save_all(st)
        path=submission_root()/'mission_1/submission.json';payload=read_json(path)
        payload['evidence']['metrics']['bias']=100;write_json(path,payload)
        self.assertFalse(refresh_completion(st)['mission_1'])

    def test_changes_invalidate_only_affected_mission_and_export(self):
        st=valid_state();self.save_all(st)
        self.assertTrue(all(refresh_completion(st).values()))
        st.session_state['responses']['mission_1.more_samples']=''
        status=refresh_completion(st);self.assertFalse(status['mission_1']);self.assertTrue(status['mission_2']);self.assertTrue(status['mission_3'])
        with self.assertRaises(ValueError): write_manifest(st)

    def test_manifest_zip_hashes_and_stale_or_missing_artifacts(self):
        st=valid_state();self.save_all(st)
        (submission_root()/'final_synthesis.md').write_text('# Final synthesis\n\n'+st.session_state['responses']['final.synthesis'])
        write_final_reflection(st);write_manifest(st)
        self.assertTrue(manifest_current(st))
        with zipfile.ZipFile(io.BytesIO(submission_zip(st))) as archive:
            manifest=json.loads(archive.read('manifest.json'))
            for name,digest in manifest['files'].items(): self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(),digest)
            self.assertFalse(any(name.endswith('.bak') for name in archive.namelist()))
        st.session_state['responses']['final.course_reflection']='Changed reflection.';self.assertFalse(manifest_current(st))
        (submission_root()/'mission_2/measurements.csv').unlink();self.assertFalse(refresh_completion(st)['mission_2'])

    def test_nonfinite_metrics_are_standard_json_and_round_trip(self):
        path=submission_root()/'metrics.json';write_json(path,{'delay':float('inf')})
        self.assertNotIn('Infinity',path.read_text());self.assertEqual(read_json(path)['delay'],float('inf'))
