import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perception.experiments import run, validate, csv_bytes


def main():
    parser = argparse.ArgumentParser(description="Evaluate the fixed shared image collection")
    parser.add_argument("--method", choices=("classical", "learned"), required=True)
    parser.add_argument("--settings", type=Path, help="Classical Settings JSON")
    parser.add_argument("--selected-threshold", type=float, default=.5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text()) if args.settings else None
    evidence = run(args.method, settings)
    if args.method == "learned": evidence["selected_threshold"] = args.selected_threshold
    checked = validate(evidence, args.method)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    args.output.with_suffix(".csv").write_bytes(csv_bytes(evidence))
    print(json.dumps(checked["metrics"], indent=2))


if __name__ == "__main__": main()
