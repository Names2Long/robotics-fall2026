import ast
from pathlib import Path
import unittest

from geometry_msgs.msg import PointStamped
from tf2_ros import TransformException
from week03_camera_transform.camera_transform import transform_camera_point


class FakeBuffer:
    def __init__(self,fail=False): self.fail=fail;self.calls=[]
    def transform(self,point,target_frame,**kwargs):
        self.calls.append((point.header.frame_id,target_frame))
        if self.fail: raise TransformException("transform unavailable")
        result=PointStamped();result.header.frame_id=target_frame
        result.point.x=-point.point.y+1.0;result.point.y=point.point.x-0.5;result.point.z=point.point.z
        return result


def point(frame="hall_camera"):
    value=PointStamped();value.header.frame_id=frame;value.point.x=.5;value.point.y=.25;return value


class CameraTransformTests(unittest.TestCase):
    def test_uses_camera_as_source_and_body_as_target(self):
        buffer=FakeBuffer();result=transform_camera_point(buffer,point())
        self.assertEqual(buffer.calls,[("hall_camera","base_link")]);self.assertEqual(result.header.frame_id,"base_link")

    def test_uses_buffer_result_including_rotation(self):
        result=transform_camera_point(FakeBuffer(),point())
        self.assertAlmostEqual(result.point.x,.75);self.assertAlmostEqual(result.point.y,0.)

    def test_rejects_wrong_source_frame(self):
        with self.assertRaises(ValueError): transform_camera_point(FakeBuffer(),point("base_link"))

    def test_unavailable_transform_returns_none(self):
        self.assertIsNone(transform_camera_point(FakeBuffer(True),point()))

    def test_source_does_not_publish_motion(self):
        source=Path(__file__).parents[1]/"week03_camera_transform/camera_transform.py"
        tree=ast.parse(source.read_text(encoding="utf-8"));calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertFalse(any(getattr(c.func,"attr","")=="create_publisher" for c in calls))
        self.assertNotIn("/cmd_vel",source.read_text(encoding="utf-8"))


if __name__=="__main__": unittest.main()
