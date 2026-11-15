from dataclasses import dataclass


@dataclass(frozen=True)
class LabConfig:
    submission_directory: str = "student_submission"


LAB = LabConfig()
