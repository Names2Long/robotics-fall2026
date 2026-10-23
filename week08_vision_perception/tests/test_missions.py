import copy
import unittest
from dataclasses import asdict
from perception.dataset import samples, tuning_image
from perception.classical import Settings, process
from perception.experiments import run, validate


class MissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.evidence = run("classical")

    def test_dim_changes_target_pixels(self):
        dim = next(x["image"] for x in samples() if x["image_id"] == "dim_1")
        self.assertLess(dim.mean(), tuning_image().mean()*.5)

    def test_intermediate_outputs_and_empty_mask(self):
        result = process(tuning_image(), Settings(min_area=1000000))
        self.assertFalse(result["detected"])
        self.assertIn("raw_mask", result)
        self.assertIn("contours", result)

    def test_duplicate_and_wrong_labels_rejected(self):
        bad = copy.deepcopy(self.evidence)
        bad["rows"][-1] = bad["rows"][0]
        with self.assertRaises(ValueError): validate(bad, "classical")
        bad = copy.deepcopy(self.evidence)
        bad["rows"][0]["expected"] = False
        with self.assertRaises(ValueError): validate(bad, "classical")

    def test_no_accuracy_gate(self):
        evidence = copy.deepcopy(self.evidence)
        for row in evidence["rows"]: row.update(detected=False, confidence=0.)
        result = validate(evidence, "classical")
        self.assertEqual(result["metrics"]["recall"], 0)
