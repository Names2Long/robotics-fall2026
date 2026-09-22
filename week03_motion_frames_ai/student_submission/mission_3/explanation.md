# Mission 3

## Specification

I intend to make four forward arcs with a radius of 0.30 m, turning + 45, - 45, + 45, and - 45. I will use a linear speed of 0.15 m/s and an angular speed of  +/- 0.50 rad/s, which hopefully gives me a radius of 0.30 m. Each arc will last about 1.5 seconds. I will then stop between each arc and send a final zero velocity command at the end. The pattern is successful if each arc turns about 0.785 radians, keeps a radius close to 0.30 m, stays within the speed limits, and the robot finishes facing approximately its original direction.

## Saved Specification

I intend to make four forward arcs with a radius of 0.30 m, turning + 45, - 45, + 45, and - 45. I will use a linear speed of 0.15 m/s and an angular speed of  +/- 0.50 rad/s, which hopefully gives me a radius of 0.30 m. Each arc will last about 1.5 seconds. I will then stop between each arc and send a final zero velocity command at the end. The pattern is successful if each arc turns about 0.785 radians, keeps a radius close to 0.30 m, stays within the speed limits, and the robot finishes facing approximately its original direction.

## Assigned Pattern

alternating_arcs

## Original Prompt

This is a ROS 2 Jazzy Python package. Implement only build_pattern(pattern_name: str) -> list[Segment] for 'alternating_arcs' in the existing pattern.py.

My intended motion is four forward arcs with a radius of 0.30 m, turning + 45, - 45, + 45, and - 45. I want to use a linear speed of 0.15 m/s and an angular speed of +/- 0.50 rad/s. Each arc should turn about 0.785 radians, remain within the speed limits, and the robot should finish facing approximately its original direction.

The course provided pattern_node.py calls this function, publishes the returned segments repeatedly through /student_cmd_vel, and sends the final zero command.

Use the existing Segment class with linear_x (m/s), angular_z (rad/s), and duration (s)

Return the ordered segments for the assigned specification and raise ValueError for an unknown pattern name

Stay within 0.22 m/s, 0.80 rad/s, 30 seconds per segment, and 60 seconds total.

Do not replace the wrapper or course checks.

Explain your assumptions and propose tests for the segment order, arc radius, turn angles, speed limits, and final heading.

## Original Output

The alternating-arcs pattern can be created using four forward arc segments. For an arc radius of 0.30 m with a linear speed of 0.15 m/s, the required angular speed is:

angular speed = linear speed / radius = 0.15 / 0.30 = 0.50 rad/s

Each turn is 45 degrees, which is about 0.785 radians. The required duration of each arc is:

duration = angle / angular speed = 0.785 / 0.50 = about 1.57 seconds

Positive angular velocity turns left and negative angular velocity turns right. Therefore, the four angular velocities should be +0.50, -0.50, +0.50, and -0.50 rad/s. The total heading change is zero, so the robot should finish facing its initial direction.

I assume the existing Segment class is already defined in pattern.py and that the course wrapper handles publishing commands and sending the final zero-velocity command.

import math


def build_pattern(pattern_name: str) -> list[Segment]:
    if pattern_name != "alternating_arcs":
        raise ValueError(f"Unknown pattern: {pattern_name}")

    linear_speed = 0.15
    angular_speed = 0.50
    turn_angle = math.pi / 4
    duration = turn_angle / angular_speed

    return [
        Segment(linear_x=linear_speed, angular_z=angular_speed, duration=duration),
        Segment(linear_x=linear_speed, angular_z=-angular_speed, duration=duration),
        Segment(linear_x=linear_speed, angular_z=angular_speed, duration=duration),
        Segment(linear_x=linear_speed, angular_z=-angular_speed, duration=duration),
    ]

I would test that:
1. build_pattern("alternating_arcs") returns exactly four segments.
2. All four segments have a positive linear speed of 0.15 m/s.
3. The angular velocity signs occur in the order +, -, +, -.
4. Each arc has a radius of abs(linear_x / angular_z) = 0.30 m.
5. Each segment turns about 0.785 radians using angular_z * duration.
6. All linear and angular speeds stay within the course limits.
7. All durations are positive and below 30 seconds, and the total duration is below 60 seconds.
8. The sum of the four heading changes is approximately 0 radians, so the robot finishes facing its initial direction.
9. An unknown pattern name raises ValueError.

## Original Source

import math

def build_pattern(pattern_name: str) -> list[Segment]:
    if pattern_name != "alternating_arcs":
        raise ValueError(f"Unknown pattern: {pattern_name}")

    linear_speed = 0.15
    angular_speed = 0.50
    turn_angle = math.pi / 4
    duration = turn_angle / angular_speed

    return [
        Segment(linear_x=linear_speed, angular_z=angular_speed, duration=duration),
        Segment(linear_x=linear_speed, angular_z=-angular_speed, duration=duration),
        Segment(linear_x=linear_speed, angular_z=angular_speed, duration=duration),
        Segment(linear_x=linear_speed, angular_z=-angular_speed, duration=duration),
    ]

## Assumptions

The AI assumed the robot follows the commanded velocities exactly with constant speed and no wheel slip or acceleration delay. It used meters per second for linear velocity, radians per second for angular velocity, and seconds for duration. It assumed the robot body frame convention where positive X is forward and positive angular velocity turns left. Each segment uses 0.15 m/s linear speed,  +/- 0.50 rad/s angular speed, and about 1.57 seconds. The segment order is left, right, left, right. It also assumed the existing Segment class and course wrapper handle execution and the final stop.

## Problems

The calculations looked correct, so I checked the radius, angle, duration, speed limits, and final heading. The radius is 0.15 / 0.50 = 0.30 m, and each turn is about 0.50 × 1.57 = 0.785 rad, or 45 degrees. The four turns cancel out, so the final heading should match the starting heading. One thing is that the code does not include explicit zero velocity stops between the four arcs, even though my original specification mentioned stopping between arcs. I would verify whether intermediate stops are required before changing the four segment pattern. The course wrapper does send a final zero velocity command.

## Test Plan

Pattern behavior test would verify there are four segments in the order + 0.50, - 0.50, + 0.50, - 0.50 rad/s, each with 0.15 m/s forward speed and about 1.57 s duration. I expect each arc to have a 0.30 m radius, turn about 45 degrees, and for the total heading change to be approximately 0 radians.

Velocity limit test would check that every segment stays below 0.22 m/s linear speed and 0.80 rad/s angular speed. I expect all four segments to pass because they use 0.15 m/s and 0.50 rad/s.

Stop test would verify that after all segments finish, the wrapper sends zero linear and angular velocity. I expect the robot to stop completely at the end of the pattern.

## Modifications

I replaced the NotImplementedError with four Segment objects for the alternating arcs pattern. I used a linear speed of 0.15 m/s and angular speeds of + 0.50, - 0.50, + 0.50, and - 0.50 rad/s so each arc has a radius of 0.30 m. I set each duration to about 1.57 seconds so each arc turns approximately 45 degrees. I also added a ValueError for unknown pattern names. I did not add ROS publishing or a final stop because the course wrapper already handles those. I will use the pattern geometry tests, velocity limit tests, and stop test to verify these changes.

## Live Pending

False

## Evidence Analysis

The tests establish that my pattern has the correct structure, geometry, speed limits, and stopping behavior. All 9 automated tests passed, including my two student tests. The assigned geometry, command limits, stop decision, and live motion and stop checks also passed. This shows that the robot followed the required alternating arcs and stopped correctly after the pattern. However, these tests dont prove that the robot would behave exactly the same under different floor conditions, starting positions, or disturbances. An additional test I would do is repeat the live pattern several times from different starting positions and compare the checkpoint poses to see if the motion remains consistent.

## Ai Disclosure

I used Claude to help calculate the arc speeds and durations, write the build_pattern code, create the student tests, and troubleshoot issues when the evaluator initially failed. I personally reviewed the calculations for the 0.30 m radius, 45 degree turns, segment order, speed limits, and final heading. I also edited the files, ran the evaluator and ROS commands myself, and verified that all 9 tests passed and that the live motion and final stop passed.

## Live Issue


