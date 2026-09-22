"""Revalidate saved submissions against current answers, code, and evidence."""
import json
from pathlib import Path
from lab.autosave import submission_root
from lab.ai_log import load_lock
from lab.camera_ai import load_lock as load_camera_lock
from lab.evidence import ai_evaluation,camera_evaluation,evidence_id
from missions import mission_1,mission_2,mission_3

SOURCE_ROOT=Path(__file__).resolve().parents[1]/'ros2_ws/src/week03_pattern'
CAMERA_SOURCE=Path(__file__).resolve().parents[1]/'ros2_ws/src/week03_camera_transform/week03_camera_transform/camera_transform.py'


def mission_status(st):
    responses=st.session_state.get('responses',{})
    checked=st.session_state.get('checked_evidence_ids',{})
    status={}
    for name in ('mission_1','mission_2','mission_3'):
        relevant={k:v for k,v in responses.items() if k.startswith(name+'.')}
        try:
            if name=='mission_1':
                current=evidence_id({k:v for k,v in relevant.items() if not k.startswith('mission_1.error.')})
                valid=mission_1.evaluate(list(responses.get('mission_1.results',{}).values()),responses).passed
            elif name=='mission_2':
                lock=load_camera_lock();result=camera_evaluation()
                current=evidence_id(result,lock,relevant,mission_2.current_hash(CAMERA_SOURCE))
                valid=mission_2.evaluate(result,lock,responses,CAMERA_SOURCE).passed
            else:
                lock=load_lock();result=ai_evaluation()
                current=evidence_id(result,lock,relevant,mission_3.current_hash(SOURCE_ROOT))
                valid=mission_3.evaluate(result,lock,responses,SOURCE_ROOT).passed
            saved=json.loads((submission_root()/name/'submission.json').read_text(encoding='utf-8'))
            valid=valid and current==checked.get(name)==saved.get('evidence',{}).get('evidence_id')
            # An exported source file must still match its working copy.
            if name in ('mission_2','mission_3') and valid:
                root=SOURCE_ROOT if name=='mission_3' else CAMERA_SOURCE.parents[1]
                folders=('week03_pattern','test') if name=='mission_3' else ('week03_camera_transform',)
                for folder in folders:
                    for source in (root/folder).rglob('*.py'):
                        copy=submission_root()/name/'source'/source.relative_to(root)
                        valid=valid and copy.read_bytes()==source.read_bytes()
            status[name]=bool(valid)
        except (OSError,ValueError,TypeError,KeyError):
            status[name]=False
    return status


def verification_summary(st):
    responses=st.session_state.get('responses',{})
    rows=[]
    for name in ('straight','turn_then_drive','arc'):
        source=responses.get('mission_1.results',{}).get(name,{}).get('source','missing')
        rows.append({'activity':'Mission 1: '+name.replace('_',' '),'evidence':source,'live_verified':source=='live'})
    source=responses.get('mission_2.snapshot',{}).get('source','missing');camera=camera_evaluation()
    rows.append({'activity':'Mission 2: frames and hallway camera','evidence':source+' snapshot; '+('live transform' if camera.get('live_passed') else 'transform tests; live pending'),'live_verified':bool(camera.get('live_passed'))})
    result=ai_evaluation()
    live=bool(result.get('integration_passed') and result.get('final_stop_verified'))
    rows.append({'activity':'Mission 3: program','evidence':'live' if live else 'code/model tests; live pending','live_verified':live})
    return rows
