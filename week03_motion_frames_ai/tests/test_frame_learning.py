import math
import unittest
from lab.frame_learning import reference_snapshot,valid_snapshot


class FrameLearningTests(unittest.TestCase):
    def test_reference_contains_robot_and_environment_cameras(self):
        data=reference_snapshot();self.assertTrue(valid_snapshot(data))
        rear=data['transforms']['rear_camera_to_base_link']
        self.assertLess(rear['translation']['x'],0);self.assertAlmostEqual(rear['yaw'],math.pi)
        self.assertIn('hall_camera_to_base_link',data['transforms'])

    def test_snapshot_requires_complete_finite_transforms(self):
        data=reference_snapshot();data['transforms']['hall_camera_to_base_link']['yaw']=float('nan')
        self.assertFalse(valid_snapshot(data))
        self.assertFalse(valid_snapshot({'source':'live','captured_at':'today','frames':None}))
        self.assertFalse(valid_snapshot({}))
