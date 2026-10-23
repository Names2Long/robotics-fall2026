import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.behavior import BehaviorConfig, evaluate_sequences


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--min-confidence", type=float, default=.6)
    parser.add_argument("--stop-area", type=float, default=.22)
    parser.add_argument("--stale-after", type=float, default=.6)
    parser.add_argument("--confirmation-frames", type=int, default=3)
    args = parser.parse_args()
    result = evaluate_sequences(BehaviorConfig(min_confidence=args.min_confidence, stop_area=args.stop_area,
                                               stale_after=args.stale_after, confirmation_frames=args.confirmation_frames))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summaries"], indent=2))


if __name__ == "__main__": main()
