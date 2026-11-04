"""One isolated student search. Invoked by offline_experiment.py, not by students."""
import importlib.util
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from planning.core import evaluate_student


def main():
    request = json.loads(sys.stdin.read())
    spec = importlib.util.spec_from_file_location('student_solution',request['source'])
    module = importlib.util.module_from_spec(spec)
    try:
        # Always execute the current file bytes. Timestamp/size-based .pyc
        # caches can otherwise reuse an older implementation after a quick
        # same-length editor change while the evidence hashes the new source.
        exec(compile(Path(request['source']).read_bytes(),request['source'],'exec'),module.__dict__)
        result = evaluate_student(getattr(module,request['planner']),request['grid'],tuple(request['start']),tuple(request['goal']))
    except Exception as exc:
        result = {'status':'implementation_error','error':f'{type(exc).__name__}: {exc}','path':[]}
    # A student print statement cannot corrupt the protocol: the parent reads the last line.
    print(json.dumps(result))


if __name__ == '__main__':
    main()
