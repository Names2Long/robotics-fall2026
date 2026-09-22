import math
import unittest
from simulation.walkthroughs import motion_samples, point_in_base, forward_command


class WalkthroughModels(unittest.TestCase):
    def test_each_run_starts_at_origin_and_straight_endpoint(self):
        for v, w in ((.2, 0), (0, .5), (.2, .5), (-.1, -.5)):
            self.assertEqual(motion_samples(v, w, 3)[0], [0, 0, 0])
        self.assertAlmostEqual(motion_samples(.2, 0, 5)[-1][0], 1)
        self.assertAlmostEqual(motion_samples(.2*.92, 0, 5)[-1][0], .92)

    def test_rotation_and_arc(self):
        x, y, a = motion_samples(0, .5, 3)[-1]
        self.assertEqual((x, y), (0, 0))
        self.assertAlmostEqual(a, 1.5)
        x, y, _ = motion_samples(.2, .5, 3)[-1]
        self.assertAlmostEqual(x, .4*math.sin(1.5))
        self.assertAlmostEqual(y, .4*(1-math.cos(1.5)))

    def test_fixed_target_changes_with_heading(self):
        self.assertEqual(point_in_base(2, 1, 1, 1, 0), (1, 0))
        x, y = point_in_base(2, 1, 1, 1, math.pi/2)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, -1)

    def test_teaching_example_boundary(self):
        self.assertEqual(forward_command(2.99), (.2, 0))
        self.assertEqual(forward_command(3), (0, 0))
        with self.assertRaises(ValueError):
            forward_command(0, .3)
        with self.assertRaises(ValueError):
            forward_command(0, duration=-1)
