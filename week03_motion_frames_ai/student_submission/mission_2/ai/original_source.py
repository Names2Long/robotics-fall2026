import rclpy

from rclpy.node import Node
from geometry_msgs.msg import PointStamped
from tf2_ros import Buffer, TransformListener
from tf2_geometry_msgs import do_transform_point


class PointTransformer(Node):
    def __init__(self):
        super().__init__('point_transformer')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def transform_point(self, point):
        try:
            transform = self.tf_buffer.lookup_transform(
                'base_link',
                'hall_camera',
                rclpy.time.Time()
            )

            transformed_point = do_transform_point(point, transform)
            return transformed_point

        except Exception as e:
            self.get_logger().error(f'Transform failed: {e}')
            return None