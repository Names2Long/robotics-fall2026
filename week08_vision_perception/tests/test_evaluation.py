import unittest
from dataclasses import replace
from evaluation.behavior import BehaviorConfig, Policy, evaluate_sequences
from evaluation.metrics import evaluate_rows, threshold_sweep


class EvaluationTests(unittest.TestCase):
    def test_threshold_uses_individual_scores(self):
        rows = [{"condition": "normal", "expected": True, "detected": True, "confidence": .9},
                {"condition": "normal", "expected": True, "detected": True, "confidence": .1},
                {"condition": "distractor", "expected": False, "detected": True, "confidence": .4}]
        result = evaluate_rows(rows, .5)
        self.assertEqual((result["tp"], result["fp"], result["fn"]), (1, 0, 1))
        self.assertEqual(result["recall"], .5)
        self.assertIsNone(evaluate_rows([], .5)["precision"])

    def test_invalid_data_is_not_silently_scored(self):
        with self.assertRaises(ValueError):
            evaluate_rows([{"condition": "normal", "expected": "false", "detected": True}])

    def test_confirmation_counts_new_captures(self):
        policy = Policy(BehaviorConfig())
        obs = {"detected": True, "confidence": .9, "center_offset": 0., "area_fraction": .1}
        for _ in range(10): self.assertEqual(policy.step(obs, .1, 1)["state"], "STOP")
        policy.step(obs, .1, 2)
        self.assertGreater(policy.step(obs, .1, 3)["linear_x"], 0)
        self.assertEqual(policy.step(obs, 2., 4)["linear_x"], 0)
        self.assertEqual(policy.step(obs, -.1, 5)["linear_x"], 0)
        self.assertEqual(policy.step(obs, .1, 6)["linear_x"], 0)

    def test_scenarios_expose_confident_false_target(self):
        result = evaluate_sequences(BehaviorConfig())
        self.assertTrue(result["safety_invariants_passed"])
        rows = {row["scenario"]: row for row in result["summaries"]}
        self.assertGreater(rows["false_target"]["incorrect_approach_steps"], 0)
        self.assertEqual(len(rows), 10)
        alternating = [row for row in result["timeline"] if row["scenario"] == "alternating" and .7 <= row["time"] < 1.6]
        self.assertTrue(all(row["linear_x"] == 0 for row in alternating))

    def test_confirmation_introduces_measurable_delay(self):
        fast = evaluate_sequences(BehaviorConfig(confirmation_frames=1))["summaries"][0]
        slow = evaluate_sequences(BehaviorConfig(confirmation_frames=5))["summaries"][0]
        self.assertGreater(slow["initial_action_delay_s"], fast["initial_action_delay_s"])

    def test_invalid_policy_rejected(self):
        with self.assertRaises(ValueError): BehaviorConfig(stale_after=float("nan"))
        with self.assertRaises(ValueError): BehaviorConfig(approach_linear=4.)
