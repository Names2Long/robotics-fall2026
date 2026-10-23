import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from lab.session import initialize
from lab.autosave import save, load_state, submission_root
from lab.submissions import export, backup_bytes


class PersistenceTests(unittest.TestCase):
    def test_transient_replace_failure_retries(self):
        from lab.autosave import atomic
        original = Path.replace
        calls = []
        def replace_once(path, target):
            calls.append(path)
            if len(calls)==1: raise PermissionError("temporary scanner lock")
            return original(path,target)
        target = submission_root()/"retry.txt"
        with patch.object(Path,"replace",replace_once): atomic(target,"preserved")
        self.assertEqual(target.read_text(),"preserved")

    def test_old_evidence_draft_remains_exportable(self):
        self.st.session_state["evidence"]["mission_1"] = {"schema_version":1,"old_answers":"preserve"}
        export(self.st)
        self.assertEqual(json.loads((submission_root()/"mission_1/evidence.json").read_text())["old_answers"],"preserve")
    def setUp(self):
        target = Path(__file__).resolve().parents[1]/"runtime"/"test_scratch"
        target.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=target)
        self.env = patch.dict(os.environ, {"WEEK08_SUBMISSION_DIR": self.temp.name})
        self.env.start()
        self.st = SimpleNamespace(session_state={})
        initialize(self.st)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_restore_answers_stage_and_identity(self):
        self.st.session_state.update(stage="mission_2")
        self.st.session_state["field.mission_1.diagnosis"] = "My saved explanation"
        self.st.session_state["student.name"] = "Test learner"
        save(self.st)
        recovered = load_state()
        self.assertEqual(recovered["responses"]["mission_1.diagnosis"], "My saved explanation")
        self.assertEqual(recovered["stage"], "investigation")
        self.assertEqual(recovered['settings']['investigation_part'], 1)
        self.assertEqual(recovered["student"]["name"], "Test learner")

    def test_removed_setup_page_resumes_at_mission_2(self):
        self.st.session_state['stage'] = 'ros_setup'
        self.st.session_state['responses']['pillar_search.diagnosis'] = 'Preserved answer'
        save(self.st)
        restored = load_state()
        self.assertEqual(restored['stage'],'pillar_search')
        self.assertEqual(restored['responses']['pillar_search.diagnosis'],'Preserved answer')

    def test_corruption_recovers_backup(self):
        save(self.st)
        self.st.session_state["responses"]["x"] = "answer"
        path = save(self.st)
        path.write_text("broken", encoding="utf-8")
        self.assertTrue(load_state()["recovered"])
        path.with_suffix(".bak").unlink()
        self.assertTrue(load_state()["recovery_blocked"])
        with self.assertRaises(OSError): save(self.st)
        self.assertEqual(path.read_text(), "broken")

    def test_blank_edit_has_recovery_copy(self):
        self.st.session_state["responses"]["answer"] = "Original response"
        save(self.st)
        self.st.session_state["responses"]["answer"] = ""
        save(self.st)
        self.assertTrue(list((submission_root()/"autosave").glob("responses.recovery.*.json")))

    def test_draft_zip_contains_current_writing(self):
        self.st.session_state["responses"]["final.synthesis"] = "Current synthesis"
        export(self.st)
        with zipfile.ZipFile(io.BytesIO(backup_bytes())) as archive:
            self.assertEqual(archive.read("final_synthesis.md"), b"Current synthesis")
            manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(manifest["status"], "draft")
        with self.assertRaises(ValueError): export(self.st, final=True)
