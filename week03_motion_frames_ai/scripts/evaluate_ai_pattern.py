"""Evaluate current source; live verification is reported separately."""
import importlib
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'ros2_ws/src/week03_pattern'
sys.path[:0]=[str(ROOT),str(PACKAGE)]
from lab.ai_log import load_lock
from lab.autosave import submission_root
from week03_pattern.checks import validate, shape_ok, endpoint, command_at, source_hash


def model_report(name):
    try:
        segments=importlib.import_module('week03_pattern.pattern').build_pattern(name)
        validate(segments)
        return {'bounded':True,'shape':shape_ok(name,segments),'pose':endpoint(segments),
                'stop':command_at(segments,sum(s.duration for s in segments))==(0.,0.) and command_at([],0)==(0.,0.)}
    except Exception as error:
        return {'error':str(error)}


def main():
    lock=load_lock()
    if not lock or not lock.get('integrity_valid'):
        raise SystemExit('Preserve the original AI interaction in the guide first.')
    name=lock['pattern']; env=dict(os.environ,WEEK03_ASSIGNED_PATTERN=name)
    try:
        tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(PACKAGE/'test'),'-v'],
                             cwd=PACKAGE,env=env,capture_output=True,text=True,timeout=30)
        output=tests.stdout+tests.stderr; passed=tests.returncode==0
    except subprocess.TimeoutExpired:
        output='Tests exceeded 30 seconds. Check for an infinite loop.'; passed=False
    match=re.search(r'Ran (\d+) tests?',output); count=int(match.group(1)) if match else 0
    student_file=PACKAGE/'test/test_student_pattern.py';student_count=0
    if student_file.exists():
        try:
            tree=ast.parse(student_file.read_text(encoding='utf-8'))
            student_count=sum(isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_') for node in ast.walk(tree))
        except (OSError,SyntaxError): pass
    bounded=shape=stop=False; pose={}
    try:
        worker=subprocess.run([sys.executable,__file__,'--model',name],capture_output=True,text=True,timeout=10)
        model=json.loads(worker.stdout.strip().splitlines()[-1])
        bounded=model.get('bounded',False);shape=model.get('shape',False);pose=model.get('pose',{});stop=model.get('stop',False)
        if model.get('error'): output+='\nPattern check: '+model['error']
    except Exception as error:
        output+=f'\nPattern check: {error}'
    signature=source_hash(PACKAGE)
    run_path=ROOT/'runtime/evidence/pattern_run.json'
    try: run=json.loads(run_path.read_text(encoding='utf-8'))
    except (OSError,ValueError): run={}
    try: attempt=json.loads((ROOT/'runtime/evidence/pattern_attempt.json').read_text(encoding='utf-8'))
    except (OSError,ValueError): attempt={}
    live=bool(run.get('completed') and run.get('shape_observed') and run.get('final_stop_verified')
              and attempt.get('attempt_id') and run.get('attempt_id')==attempt.get('attempt_id')
              and run.get('pattern')==name and run.get('source_sha256')==signature)
    original=submission_root()/'mission_3/ai/original_source.py'
    changed=original.exists() and original.read_text(encoding='utf-8').strip()!=(PACKAGE/'week03_pattern/pattern.py').read_text(encoding='utf-8').strip()
    implementation=PACKAGE/'week03_pattern/pattern.py'
    payload={'captured_at':datetime.now(timezone.utc).isoformat(),'pattern':name,
             'source_sha256':signature,'unit_tests_passed':passed,'test_count':count,'unit_test_output':output,
             'implementation_present':implementation.exists(),'student_test_file_present':student_file.exists(),'student_test_count':student_count,
             'commands_bounded':bounded,'shape_check_passed':shape,'model_stop_passed':stop,
             'predicted_endpoint':pose,'integration_passed':live,'final_stop_verified':live,
             'source_differs_from_original':changed,'live_run':run}
    target=ROOT/'runtime/evidence/ai_evaluation.json'; target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix('.tmp');temp.write_text(json.dumps(payload,indent=2),encoding='utf-8');temp.replace(target)
    print(output);print(json.dumps(payload,indent=2))
    return 0 if passed and bounded and shape and stop else 1


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--model':
        print(json.dumps(model_report(sys.argv[2])));raise SystemExit(0)
    raise SystemExit(main())
