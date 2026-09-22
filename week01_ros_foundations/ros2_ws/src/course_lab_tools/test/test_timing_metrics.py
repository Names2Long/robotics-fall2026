import unittest

import rclpy

from course_lab_tools.timed_twist import TimedTwist, timing_metrics


class TimingMetricsTests(unittest.TestCase):
    def test_timing_metrics_compare_requested_and_actual_duration(self):
        metrics = timing_metrics(3.0, 10.0, 13.04, -0.2)
        self.assertAlmostEqual(metrics["actual_command_duration"], 3.04)
        self.assertAlmostEqual(metrics["duration_error"], 0.04)
        self.assertAlmostEqual(metrics["expected_linear_travel"], 0.6)
        self.assertAlmostEqual(metrics["commanded_path_length"], 0.6)

    def test_timing_metrics_preserve_missing_timestamps(self):
        metrics = timing_metrics(2.0, None, None, 0.1)
        self.assertIsNone(metrics["actual_command_duration"])
        self.assertIsNone(metrics["duration_error"])
        self.assertAlmostEqual(metrics["expected_linear_travel"], 0.2)
        self.assertAlmostEqual(metrics["commanded_path_length"], 0.2)

    def test_trial_lifecycle_finishes_without_timer_callback(self):
        rclpy.init()
        node = TimedTwist()
        try:
            node.latest_pose = {"x": 1.0, "y": 2.0, "theta": 0.0}
            node.begin()
            node.publish_motion()
            node.latest_pose = {"x": 1.2, "y": 2.0, "theta": 0.1}
            node.publish_stop()
            node.finish()
            result = node.result()
            self.assertTrue(result["completed"])
            self.assertTrue(result["stop_sent"])
            self.assertEqual(result["start_pose"]["x"], 1.0)
            self.assertEqual(result["end_pose"]["x"], 1.2)
        finally:
            node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()
