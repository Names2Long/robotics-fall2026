import math
import unittest
from lab.motion_trials import modeled_trial
from missions.mission_1 import valid_run


class TrialEvidence(unittest.TestCase):
    def setUp(self):
        self.prediction={"id":"saved-prediction","saved_at":"2026-01-01T00:00:00+00:00"}

    def test_model_geometry_and_provenance(self):
        straight=modeled_trial("straight",self.prediction["id"])
        self.assertAlmostEqual(straight["observed_pose"]["x"],.45*.92)
        self.assertFalse(straight["stop_sent"])
        self.assertFalse(straight["live_verified"])
        self.assertTrue(valid_run(straight,self.prediction))
        turn=modeled_trial("turn_then_drive",self.prediction["id"])
        self.assertAlmostEqual(turn["observed_pose"]["theta"],math.pi/2*.93)
        self.assertAlmostEqual(math.hypot(turn["observed_pose"]["x"],turn["observed_pose"]["y"]),.3*.92)
        arc=modeled_trial("arc",self.prediction["id"])
        self.assertAlmostEqual(arc["observed_pose"]["theta"],1.6*.93)

    def test_old_or_unmatched_evidence_rejected(self):
        run=modeled_trial("straight","wrong")
        self.assertFalse(valid_run(run,self.prediction))
        run["prediction_id"]=self.prediction["id"]
        run["captured_at"]="2025-01-01T00:00:00+00:00"
        self.assertFalse(valid_run(run,self.prediction))

    def test_live_requires_observed_stop_and_finite_pose(self):
        run=modeled_trial("straight",self.prediction["id"])
        run["source"]="live"
        self.assertFalse(valid_run(run,self.prediction))
        run.update(stop_sent=True,stop_observed=True)
        self.assertTrue(valid_run(run,self.prediction))
        run["observed_pose"]["x"]=float("nan")
        self.assertFalse(valid_run(run,self.prediction))
