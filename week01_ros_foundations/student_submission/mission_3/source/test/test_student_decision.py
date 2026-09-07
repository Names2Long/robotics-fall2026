
import unittest

from week01_behavior.decision import decide_velocity


class StudentDecisionTest(unittest.TestCase):
    def test_robot_stops_at_boundary(self):
        speed = decide_velocity(0.5, 0.5, 0.08)
        self.assertEqual(speed, 0.0)


if __name__ == "__main__":
    unittest.main()
