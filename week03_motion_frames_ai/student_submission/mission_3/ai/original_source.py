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