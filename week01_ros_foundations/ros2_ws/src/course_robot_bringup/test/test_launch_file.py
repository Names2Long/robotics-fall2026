from pathlib import Path


def test_week01_launch_file_is_installed_from_source() -> None:
    launch_file = Path(__file__).resolve().parents[1] / "launch" / "week01.launch.py"
    source = launch_file.read_text(encoding="utf-8")
    assert "course_cmd_vel_guard" in source
    assert "course_evidence_collector" in source
    assert "turtlebot3_world.launch.py" in source
