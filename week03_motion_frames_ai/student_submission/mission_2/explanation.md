# Mission 2

## Frame Context

The rear-camera transform stays fixed because the rear camera is attached to the robot, so its position relative to the base_link doesnt change. The hallway camera is fixed within the environment, so as the robot moves, its position relative to base_link also changes.

## Initial Prompt

Write a ROS 2 python code that converts a point detected by a hallway camera into the robots base_link frame.

Here is some background info:

Using reference frame evidence captured or created at 2026-09-22T02:16:23.120272+00:00.

Relationship

x (m)

y (m)

z (m)

yaw (rad)

LiDAR relative to robot body

0.2000

0.0000

0.1400

0.0000

Rear camera relative to robot body

-0.1800

0.0000

0.2200

3.1420

Fixed hallway camera relative to robot body

-1.5000

0.5000

1.2000

-1.5710

 
The two robot-mounted sensor relationships remain fixed. The hallway-camera relationship changes as the robot moves because the camera remains in the environment while base_link moves.

## Initial Output

You can use ROS 2 TF2 to transform a PointStamped from the hallway camera frame into the robot's base_link frame. The TF buffer stores the transforms between frames, and do_transform_point applies the transform to the point.

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

The input point should be a PointStamped containing coordinates from the hallway camera. The code looks up the transform from hall_camera to base_link and applies it to produce the point in the robot's coordinate frame.

## Initial Source

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

## Snapshot

{'source': 'reference', 'captured_at': '2026-09-22T02:16:23.120272+00:00', 'description': 'Instructor-defined frame geometry. No live ROS transforms were measured.', 'frames': ['odom', 'base_link', 'base_scan', 'rear_camera_link', 'hall_camera'], 'transforms': {'base_scan_to_base_link': {'translation': {'x': 0.2, 'y': 0.0, 'z': 0.14}, 'yaw': 0.0}, 'rear_camera_to_base_link': {'translation': {'x': -0.18, 'y': 0.0, 'z': 0.22}, 'yaw': 3.141592653589793}, 'hall_camera_to_base_link': {'translation': {'x': -1.5, 'y': 0.5, 'z': 1.2}, 'yaw': -1.5707963267948966}}}

## Initial Analysis

The first response assumes PointStamped is already in the hall_camera frame, but it doesnt check the header.frame_id. It codes hall_camera as the source and base_link as the target. It also uses the latest available transform instead of the point timestamp, which could be inaccurate if the robot has moved. The code creates its own TF buffer instead of using a supplied buffer and catches all exceptions rather than specifically handling a unavailable transform. It does not hard code any position offsets or publish to any robot motion topics, which is good.

## Improved Changes

The improved prompt makes the requirements more specific. It says the source frame must be hall_camera and the target frame must be base_link, and it requires checking the points header.frame_id. It also says to use the timestamp stored in the PointStamped instead of just using the latest transform. The TF buffer also should be used, so no transform offsets should be hard coded. If the transform is unavailable, the function should return None instead of crashing or trying to move the robot, and it should not create publishers or send velocity commands.

## Live Pending

True

## Synthesis

The initial AI response assumed the point was already in the hall_camera frame and used the latest available transform instead of the points timestamp. The improved prompt made the program check that the source frame is hall_camera, transform the point into base_link, use the supplied TF buffer, and return None if the transform is unavailable. If the wrong transform were used, the robot could think a person or object is in the wrong location, which could cause unsafe movement around people. The tests that check the camera source, body target, and rotated coordinates help detect this problem. If transform data is unavailable, the robot should not move based on that point and should safely return None until valid transform data is available.

## Live Issue

The five course tests passed successfully. However when I ran the evaluator with --live the live hall_camera to base_link transform was not verified. The live check returned "passed: false" and the transformed point was null. I tried the live evaluator while using hall_camera as the source and base_link as the target. The live TF transform still remains unverified, possibly because the required transform was not available at that moment. But im not sure.
