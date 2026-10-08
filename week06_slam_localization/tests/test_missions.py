import unittest
from missions import mission_1, mission_2

class MissionTests(unittest.TestCase):
    def setUp(self):
        self.metrics = {"known_fraction": .55, "resolution": .05, "speckle_fraction": .02, "border_contact_fraction": .01}
    def test_map_missions(self):
        self.assertEqual(mission_1.REFLECTIONS, ("limitations", "drift_and_revisit"))
        self.assertEqual(mission_2.REFLECTIONS, ("comparison", "map_choice"))
        first = {"strategy": "perimeter", "duration_minutes": 7, "metrics": self.metrics, "quality_score": 70}
        second = {"strategy": "frontier", "duration_minutes": 4.5, "metrics": {**self.metrics, "known_fraction": .6}, "quality_score": 75}
        responses = {**{f"mission_1.{key}": "Evidence-based interpretation of ROS observations, map quality, limitations, and causes. " * 2 for key in mission_1.REFLECTIONS}, **{f"mission_2.{key}": "Controlled numerical and visual comparison with a careful claim about loop closure evidence. " * 2 for key in mission_2.REFLECTIONS}}
        responses["mission_1.route.original_prediction"] = "I will follow the perimeter, revisit a wall, and inspect the weakly observed center."
        responses["mission_2.strategy.original_prediction"] = "The second route may improve coverage but delay revisits."
        self.assertTrue(mission_1.evaluate(first, responses, True, True).passed); self.assertTrue(mission_2.evaluate(first, second, responses).passed)
        self.assertFalse(mission_2.evaluate(first, {**second, "duration_minutes": 0}, responses).passed)

        low_scoring_map = {**first, "metrics": {"known_fraction": .01, "resolution": .2}, "quality_score": 0}
        check = mission_1.evaluate(low_scoring_map, responses, True, True)
        self.assertTrue(check.passed)
        self.assertEqual({item.id for item in check.requirements}, {"files", "limitations", "drift_and_revisit", "route"})
        low_scoring_second_map = {**second, "metrics": {"known_fraction": .01, "resolution": .2}, "quality_score": 0}
        comparison_check = mission_2.evaluate(low_scoring_map, low_scoring_second_map, responses)
        self.assertTrue(comparison_check.passed)
        self.assertEqual({item.id for item in comparison_check.requirements}, {"runs", "strategies", "comparison", "map_choice", "prediction", "duration"})

    def test_comparison_table_uses_saved_map_metrics_and_recorded_time(self):
        from pages.mission_2 import comparison_rows

        first = {"duration_minutes": 8, "metrics": {"known_fraction": .5, "map_area_m2": 20, "speckle_fraction": .1}, "quality_score": 60}
        second = {"duration_minutes": 5, "metrics": {"known_fraction": .6, "map_area_m2": 20, "speckle_fraction": .05}, "quality_score": 70}
        rows = {row["Measure"]: row for row in comparison_rows(first, second)}
        self.assertEqual(rows["Known area (m²)"]["Mission 1"], 10)
        self.assertEqual(rows["Known area (m²)"]["Mission 2"], 12)
        self.assertEqual(rows["Elapsed time (min)"]["Mission 2 minus Mission 1"], -3)
        self.assertEqual(rows["Known area per minute (m²/min)"]["Mission 2"], 2.4)
if __name__ == "__main__": unittest.main()
