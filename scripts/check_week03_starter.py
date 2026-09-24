"""Check that the Week 3 starter contains no generated student submission."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "week03_motion_frames_ai" / "student_submission"


def main() -> int:
    unexpected = sorted(
        path.relative_to(ROOT)
        for path in SUBMISSION.rglob("*")
        if path.is_file() and path.name != ".gitkeep"
    )
    if unexpected:
        print("Generated files are present in the Week 3 starter submission folder:")
        for path in unexpected:
            print(f"  {path}")
        return 1
    print("Week 3 starter submission folder contains no generated student work.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
