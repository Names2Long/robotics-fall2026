import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lab.autosave import load_state, save, submission_root
from lab.completion import current_signature, mission_status
from lab.evidence import Artifact, validate_map_bundle
from lab.final_reflection import write_final_reflection
from lab.session import initialize
from lab.submissions import export_files, manifest_current, save_mission, write_manifest


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        initialize(self)


class RecoverySubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.override = patch.dict(os.environ, {"WEEK06_SUBMISSION_DIR": self.temporary.name})
        self.override.start()
        self.addCleanup(self.override.stop)

    def test_corrupt_primary_recovers_backup_without_losing_corrupt_copy(self):
        st = FakeStreamlit()
        st.session_state["student"] = {"name": "Student", "email": "s@example.edu", "course_id": "123"}
        st.session_state["responses"]["tutorial_1.check"] = "Original saved answer"
        path = save(st)
        st.session_state["responses"]["tutorial_1.check"] = "Newer saved answer"
        save(st)
        path.write_text("{broken", encoding="utf-8")
        restored = load_state()
        self.assertTrue(restored["recovered_from_backup"])
        self.assertEqual(restored["responses"]["tutorial_1.check"], "Original saved answer")
        fresh = FakeStreamlit()
        fresh.session_state.update(restored)
        fresh.session_state["responses"]["tutorial_1.check"] = "Recovered and continued"
        save(fresh)
        self.assertEqual(load_state()["responses"]["tutorial_1.check"], "Recovered and continued")
        self.assertEqual(len(list(path.parent.glob("responses.unreadable.*.json"))), 1)

    def test_unreadable_both_copies_blocks_overwrite(self):
        path = submission_root() / "autosave/responses.json"
        path.parent.mkdir(parents=True)
        path.write_text("{broken", encoding="utf-8")
        path.with_suffix(".bak").write_text("{also broken", encoding="utf-8")
        self.assertTrue(load_state()["recovery_blocked"])
        st = FakeStreamlit()
        st.session_state["recovery_blocked"] = True
        with self.assertRaises(OSError):
            save(st)
        self.assertEqual(path.read_text(encoding="utf-8"), "{broken")

    def test_mission_hashes_and_manifest_detect_changes(self):
        st = FakeStreamlit()
        st.session_state["student"] = {"name": "Student", "email": "s@example.edu", "course_id": "123"}
        for mission in ("mission_1", "mission_2"):
            st.session_state["evidence"][mission] = {"checked": mission}
            signature = current_signature(st, mission)
            uploads = {
                "analysis.json": Artifact("analysis.json", b"{}"),
                "map.yaml": Artifact("map.yaml", b"image: map.pgm\nresolution: 0.05\n"),
                "map.pgm": Artifact("map.pgm", b"P2\n1 1\n255\n254\n"),
                "rviz_screenshot.png": Artifact("rviz.png", b"png"),
            }
            save_mission(mission, {"checked": mission}, st.session_state["responses"], uploads, state_signature=signature)
            st.session_state["checked_evidence_ids"][mission] = signature
        self.assertTrue(all(mission_status(st).values()))
        st.session_state["responses"]["final.synthesis"] = "evidence " * 210
        st.session_state["responses"]["final.course_reflection"] = "I learned about uncertainty."
        root = submission_root()
        (root / "final_synthesis.md").write_text(st.session_state["responses"]["final.synthesis"], encoding="utf-8")
        (root / "final_reflection.md").write_text(st.session_state["responses"]["final.course_reflection"], encoding="utf-8")
        write_manifest(st)
        self.assertTrue(manifest_current(st))
        retired = root / "mission_3"
        retired.mkdir()
        (retired / "old_trial.json").write_text("{}", encoding="utf-8")
        self.assertFalse(any("mission_3" in str(path) for path in export_files()))
        self.assertTrue(manifest_current(st))
        (root / "mission_1/map.pgm").write_bytes(b"changed")
        self.assertFalse(mission_status(st)["mission_1"])
        self.assertFalse(manifest_current(st))

    def test_map_bundle_checks_matching_pair(self):
        yaml = Artifact("map.yaml", b"image: map.pgm\nresolution: 0.05\n")
        image = Artifact("map.pgm", b"P2\n2 2\n255\n0 254 205 254\n")
        evidence = {"world_id": "turtlebot3_house", "map_image": "map.pgm", "metrics": {"width": 2, "height": 2, "resolution": .05, "known_fraction": .75}}
        metrics, error = validate_map_bundle(evidence, yaml, image)
        self.assertIsNone(error)
        self.assertAlmostEqual(metrics["known_fraction"], .75)
        _, error = validate_map_bundle({**evidence, "world_id": "turtlebot3_world"}, yaml, image)
        self.assertIn("TurtleBot3 House", error)
        _, error = validate_map_bundle(evidence, Artifact("map.yaml", b"image: different.pgm\nresolution: 0.05\n"), image)
        self.assertIn("does not match", error)

    def test_rechecking_mission_preserves_previous_artifacts_locally(self):
        uploads = {"analysis.json": Artifact("analysis.json", b"old analysis"),
                   "rviz_screenshot.png": Artifact("old.png", b"old image")}
        save_mission("mission_1", {"run": 1}, {}, uploads, state_signature="first")
        save_mission(
            "mission_1", {"run": 2}, {},
            {"analysis.json": Artifact("analysis.json", b"new analysis")},
            state_signature="second",
        )
        copies = list((submission_root() / "autosave/recovery").glob("mission_1.*/analysis.json"))
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0].read_bytes(), b"old analysis")
        self.assertEqual(len(list((submission_root() / "autosave/recovery").glob("mission_1.*/rviz_screenshot.png"))), 1)
        self.assertFalse((submission_root() / "mission_1/rviz_screenshot.png").exists())

    def test_mapping_change_invalidates_comparison_signature(self):
        st = FakeStreamlit()
        st.session_state["evidence"].update(mission_1={"map": "first"}, mission_2={"map": "second"})
        first_signature = current_signature(st, "mission_2")
        st.session_state["evidence"]["mission_1"] = {"map": "revised"}
        self.assertNotEqual(first_signature, current_signature(st, "mission_2"))

    def test_retired_stage_redirects_without_erasing_old_answers(self):
        st = FakeStreamlit()
        st.session_state["stage"] = "mission_3"
        st.session_state["checked_evidence_ids"]["mission_2"] = "saved"
        st.session_state["responses"].update({
            "tutorial_4.selected_map": "Mission 2",
            "tutorial_4.map_choice": "Mission 2 has more complete walls and better measured coverage.",
            "mission_3.knowing_where": "My earlier localization answer is preserved.",
        })
        save(st)
        restored = load_state()
        self.assertEqual(restored["stage"], "final")
        self.assertIn("tutorial_4.map_choice", restored["responses"])
        self.assertIn("mission_3.knowing_where", restored["responses"])
        self.assertIn("future lab module", restored["recovery_note"])

    def test_reflection_uses_submission_root(self):
        st = FakeStreamlit()
        st.session_state["responses"]["final.course_reflection"] = "A reflection on uncertainty."
        path = write_final_reflection(st)
        self.assertEqual(path.parent, submission_root())
        self.assertIn("A reflection on uncertainty.", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
