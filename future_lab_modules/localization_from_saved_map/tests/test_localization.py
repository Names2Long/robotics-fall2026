import sys
import unittest
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
LAB_ROOT = MODULE_ROOT.parents[1] / "week06_slam_localization"
sys.path.insert(0, str(LAB_ROOT))
sys.path.insert(0, str(MODULE_ROOT))

from analysis.localization import localization_decision, summarize, trial_passes
from missions import mission_3


class DeferredLocalizationTests(unittest.TestCase):
    def test_summary_distinguishes_reference_error_from_covariance(self):
        rows = [
            {"time": i, "x": 1.0, "y": 0.0, "yaw": 0.0, "covariance_trace": 0.1,
             "reference_x": 0.0, "reference_y": 0.0, "reference_yaw": 0.0}
            for i in range(25)
        ]
        metrics = summarize(rows)
        self.assertEqual(metrics["sample_count"], 25)
        self.assertEqual(metrics["final_position_error"], 1.0)
        self.assertEqual(metrics["false_confident_samples"], 25)
        self.assertIn("SLOW", localization_decision({**metrics, "scan_retention": 1.0}, 0.5, 10.0))

    def test_four_documented_trials_pass_without_required_correct_outcome(self):
        base = {"sample_count": 40, "duration": 20, "convergence_time": 2,
                "final_covariance": 0.1, "settled_position_spread": 0.03,
                "pose_jump": 0.02, "scan_retention": 1.0}
        trials = {
            "good_initial_pose": {"metrics": base},
            "incorrect_initial_pose": {"metrics": {**base, "pose_jump": 0.5}},
            "ambiguous_location": {"metrics": {**base, "final_covariance": 0.2}},
            "degraded_sensor": {"metrics": {**base, "scan_retention": 0.5}},
        }
        responses = {
            f"mission_3.{key}": "An evidence-based interpretation of uncertainty and limitations. " * 3
            for key in mission_3.REFLECTIONS
        }
        for condition in mission_3.CONDITIONS:
            self.assertTrue(trial_passes(condition, trials[condition]["metrics"]))
            responses[f"mission_3.{condition}.original_prediction"] = "I predict a change in particle spread and convergence."
            responses[f"mission_3.{condition}.observation"] = "I compared particle spread and the displayed pose with independent visual evidence."
            responses[f"mission_3.{condition}.correctness"] = "Uncertain"
        responses["mission_3.policy_reasoning"] = "The rule should stop when evidence is weak and should request help when the estimate is uncertain. A concentrated estimate may still be wrong near people."
        self.assertTrue(mission_3.evaluate(trials, responses).passed)


if __name__ == "__main__":
    unittest.main()
