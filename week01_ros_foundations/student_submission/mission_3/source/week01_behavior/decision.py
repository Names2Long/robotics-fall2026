"""Pure decision helpers for Mission 3.

Complete both functions. Keeping this logic independent of ROS makes it possible
to test safety decisions before running the simulated robot.
"""

from __future__ import annotations

import math

from collections.abc import Sequence


def front_distance(
    ranges: Sequence[float],
    angle_min: float,
    angle_increment: float,
    half_width_radians: float,
) -> float | None:
    """Return the nearest finite, positive reading in the front sector.

    Return ``None`` when the sector has no valid reading. Angles are measured in
    radians and the front direction is zero radians.
    """
    valid = []
    for index, distance in enumerate(ranges):
        angle = angle_min + index * angle_increment
        if abs(angle) <= half_width_radians and math.isfinite(distance) and distance > 0:
            valid.append(distance)
    if not valid:
        return None
    return min(valid)


def decide_velocity(
    distance: float | None,
    stop_distance: float,
    forward_speed: float,
) -> float:
    """Return a bounded forward velocity; missing data must produce a stop."""
    if distance is None:
        return 0.0
    if distance <= stop_distance:
        return 0.0
    return max(0.0, min(float(forward_speed), 0.18))
