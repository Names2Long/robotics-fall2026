from dataclasses import dataclass

@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    stages: tuple[str, ...]
    missions: tuple[str, ...]
    submission_directory: str = "student_submission"

LAB = LabConfig(
    id="week08_vision_perception",
    title="Lab 7: Computer Vision and Learned Perception (Week 8)",
    stages=("intro", "preflight", "concepts", "investigation", "pillar_search", "line_following", "final"),
    # Evidence keys remain stable to preserve saved work from earlier revisions.
    missions=("mission_1", "mission_2", "pillar_search", "line_following"),
)
