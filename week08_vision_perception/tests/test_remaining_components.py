import unittest
from dataclasses import replace
import numpy as np
from perception.student_code import REFERENCE, check_implementation, expression
from perception.classical import process, Settings
from perception.dataset import samples, tuning_image
from evaluation.metrics import iou, localization_metrics
from evaluation.behavior import BehaviorConfig, Policy, evaluate_sequences


class RemainingComponentsTests(unittest.TestCase):
    def test_student_code_drives_pipeline(self):
        check_implementation(REFERENCE)
        a = process(tuning_image(),Settings(),REFERENCE)
        b = process(tuning_image())
        self.assertTrue(np.array_equal(a["raw_mask"],b["raw_mask"]))
        self.assertEqual(a["bbox"],b["bbox"])
        with self.assertRaises(ValueError): check_implementation({**REFERENCE,"hsv":"image"})
        with self.assertRaises(ValueError): expression("__import__('os').getcwd()",{})

    def test_matched_negatives_and_independent_sources(self):
        items = {r["image_id"]:r for r in samples()}
        self.assertEqual(len(items),31)
        self.assertFalse(np.array_equal(items["normal_absent"]["image"],items["rotated_absent"]["image"]))
        self.assertFalse(np.array_equal(items["normal_absent"]["image"],items["glare_absent"]["image"]))
        self.assertEqual(sum(r["condition"] == "independent" for r in items.values()),2)
        self.assertTrue(all(r["reference_box"] is not None for r in items.values() if r["expected"]))

    def test_wrong_box_does_not_pass_localization(self):
        self.assertEqual(iou([0,0,10,10],[0,0,10,10]),1)
        row = {"expected":True,"detected":True,"bbox":[40,40,10,10],"reference_box":[0,0,10,10]}
        metrics = localization_metrics([row])
        self.assertEqual((metrics["box_tp"],metrics["box_fp"],metrics["box_fn"]),(0,1,1))

    def test_area_goal_overrides_search_rule(self):
        policy = Policy(BehaviorConfig(transition_rule="'SEARCH'"))
        result = policy.step({"detected":False,"confidence":.1,"center_offset":0.,"area_fraction":.4},.1,1)
        self.assertEqual((result["linear_x"],result["angular_z"]),(0.,0.))

    def test_steering_and_instability_are_exercised(self):
        result = evaluate_sequences(BehaviorConfig())
        steer = [r for r in result["timeline"] if r["scenario"] == "steering"]
        self.assertTrue(any(r["angular_z"] > 0 for r in steer))
        self.assertTrue(any(r["angular_z"] < 0 for r in steer))
        self.assertTrue(any(r["linear_x"] > 0 for r in steer))
        unstable = [r for r in result["timeline"] if r["scenario"] == "unstable_center" and .6 <= r["time"] < 1.6]
        self.assertTrue(all(r["state"] == "STOP" for r in unstable))

    def test_student_rule_changes_action_but_not_safety(self):
        config = BehaviorConfig(transition_rule="'SEARCH' if usable else 'STOP'")
        policy = Policy(config)
        obs = {"detected":True,"confidence":.9,"center_offset":0.,"area_fraction":.1}
        for i in range(3): result = policy.step(obs,.1,i)
        self.assertEqual(result["state"],"SEARCH")
        self.assertEqual(policy.step(obs,3.,4)["angular_z"],0)
        forced = Policy(replace(config,transition_rule="'APPROACH'"))
        self.assertEqual(forced.step({**obs,"detected":False},.1,5)["linear_x"],0)
        with self.assertRaises(ValueError): BehaviorConfig(transition_rule="'RUN'")
