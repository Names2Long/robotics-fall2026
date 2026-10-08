from dataclasses import dataclass

WORLD_ID = "turtlebot3_house"

@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    stages: tuple[str, ...]
    missions: tuple[str, ...]
    submission_directory: str = "student_submission"

LAB = LabConfig(
    id="week06_slam_localization",
    title="Week 6: SLAM and Mapping",
    stages=("intro", "tutorial_1", "tutorial_2", "preflight", "tutorial_3",
            "mission_1", "mission_2", "final"),
    missions=("mission_1", "mission_2"),
)
