"""Run the assignment preserved in the AI record, with a process deadline."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import json
import uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from lab.ai_log import load_lock


def main():
    lock=load_lock()
    if not lock or not lock.get('integrity_valid'): raise SystemExit('Preserve your AI interaction in the guide first')
    attempt=uuid.uuid4().hex
    directory=ROOT/'runtime/evidence';directory.mkdir(parents=True,exist_ok=True)
    (directory/'pattern_attempt.json').write_text(json.dumps({'attempt_id':attempt}),encoding='utf-8')
    env=dict(os.environ,ROS_DOMAIN_ID='25',WEEK03_ATTEMPT_ID=attempt,WEEK03_SOURCE_ROOT=str(ROOT/'ros2_ws/src/week03_pattern'),
             WEEK03_EVIDENCE_DIR=str(ROOT/'runtime/evidence'))
    process=subprocess.Popen([sys.executable,'-m','week03_pattern.pattern_node','--ros-args','-p',f"pattern:={lock['pattern']}"],
                             env=env,cwd=ROOT,start_new_session=True)
    try:
        code=process.wait(timeout=80)
        if code==0:
            evaluation=subprocess.run([sys.executable,str(ROOT/'scripts/evaluate_ai_pattern.py')],cwd=ROOT,env=env)
            return evaluation.returncode
        return code
    except (subprocess.TimeoutExpired,KeyboardInterrupt):
        os.killpg(process.pid,signal.SIGINT)
        try: process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait()
        print('Run interrupted or timed out. Inspect the saved evidence and simulator before retrying.')
        return 1


if __name__=='__main__': raise SystemExit(main())
