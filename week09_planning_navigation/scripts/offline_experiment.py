"""Run: python scripts/offline_experiment.py --source student_submission/mission_1/planners.py"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from planning.experiments import run_offline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('runtime/offline.json'))
    args = parser.parse_args()
    result = run_offline(args.source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    for row in result['rows']:
        print(row['map'],row['planner'],row['status'],row.get('expanded'),row.get('planning_s'))
    print(f'Evidence saved to {args.output}')


if __name__ == '__main__':
    main()
