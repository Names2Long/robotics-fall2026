from __future__ import annotations
import json, math, os, uuid
from datetime import datetime, timezone
from pathlib import Path
from lab_config import LAB

ROOT=Path(__file__).resolve().parents[1]
CONTENT_VERSION=2
STATE_KEYS=('student','responses','completed_missions','checked_evidence_ids','mission_2_attempts','mission_3_results','mission_3_attempts','mission_2_controls','mission_3_controls','prediction_locks','stage','visited_stages','walkthrough_index','reviewed_walkthroughs','identity_locked','legacy_evidence')

def submission_root():
    override=os.environ.get('WEEK05_SUBMISSION_DIR','').strip()
    if override:
        path=Path(override).expanduser()
        if not path.is_absolute(): raise ValueError('WEEK05_SUBMISSION_DIR must be an absolute path')
        return path
    return ROOT/LAB.submission_directory

def json_ready(value):
    if isinstance(value,float) and not math.isfinite(value):
        return {'__nonfinite__':'nan' if math.isnan(value) else 'inf' if value>0 else '-inf'}
    if isinstance(value,dict): return {k:json_ready(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [json_ready(v) for v in value]
    return value

def _decode(value):
    return float(value['__nonfinite__']) if set(value)=={'__nonfinite__'} else value

def read_json(path): return json.loads(Path(path).read_text(encoding='utf-8'),object_hook=_decode)

def _atomic(path,text):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temporary.write_text(text,encoding='utf-8');temporary.replace(path)
    finally:
        if temporary.exists(): temporary.unlink()

def write_json(path,payload): _atomic(path,json.dumps(json_ready(payload),indent=2,sort_keys=True,allow_nan=False))

def _usable(data):
    if not isinstance(data,dict) or not isinstance(data.get('responses'),dict) or not isinstance(data.get('student'),dict) or data.get('lab_id')!=LAB.id: return False
    if set(data['student'])!={'name','email','course_id'} or any(not isinstance(value,str) for value in data['student'].values()): return False
    if any(key in data and not isinstance(data[key],dict) for key in ('checked_evidence_ids','mission_3_results','mission_3_attempts','mission_2_controls','mission_3_controls','prediction_locks','legacy_evidence')): return False
    if any(key in data and not isinstance(data[key],list) for key in ('completed_missions','mission_2_attempts','visited_stages','reviewed_walkthroughs')): return False
    return data.get('stage','intro') in LAB.stages and data.get('walkthrough_index',0) in range(4)

def load_state():
    path=submission_root()/'autosave/responses.json'
    for candidate in (path,path.with_suffix('.bak')):
        try:
            data=read_json(candidate)
            if not _usable(data): continue
            if candidate!=path: data['recovery_note']='The latest autosave was unreadable. Your previous valid save was recovered.'
            if data.get('content_version',1)<CONTENT_VERSION:
                data['completed_missions']=[];data['checked_evidence_ids']={}
                data['legacy_evidence']={key:data.get(key) for key in ('mission_2_attempts','mission_3_results','mission_3_attempts') if data.get(key)}
                data['mission_2_attempts']=[];data['mission_3_results']={};data['mission_3_attempts']={}
                data['recovery_note']='Earlier answers were recovered and earlier experiments archived in your autosave. Record new experiments for the updated requirements; no files were erased.'
            return data
        except (OSError,ValueError,TypeError): pass
    if path.exists() or path.with_suffix('.bak').exists():
        return {'recovery_blocked':True,'recovery_note':'Saved work could not be read. No files have been overwritten. Back up student_submission and contact your instructor before continuing.'}
    return {}

def save(st):
    if st.session_state.get('recovery_blocked'): raise OSError('Autosave blocked to protect unreadable work.')
    payload={k:st.session_state[k] for k in STATE_KEYS if k in st.session_state}
    payload.update(schema_version=2,content_version=CONTENT_VERSION,lab_id=LAB.id,updated_at=datetime.now(timezone.utc).isoformat())
    path=submission_root()/'autosave/responses.json'
    if path.exists():
        previous=path.read_bytes()
        try:
            previous_data=read_json(path)
            if not _usable(previous_data): raise ValueError('Unreadable save structure')
            if {k:v for k,v in previous_data.items() if k!='updated_at'}=={k:v for k,v in payload.items() if k!='updated_at'} and (submission_root()/'student.json').is_file() and path.with_suffix('.md').is_file():
                return path
            _atomic(path.with_suffix('.bak'),previous.decode('utf-8'))
            removed={key for key,value in previous_data['responses'].items() if str(value).strip() and not str(payload.get('responses',{}).get(key,'')).strip()}
            if removed:
                archive=path.with_name('responses.recovery.'+uuid.uuid4().hex+'.json')
                _atomic(archive,previous.decode('utf-8'))
        except (ValueError,TypeError):
            archive=path.with_name('responses.unreadable.'+uuid.uuid4().hex+'.json')
            path.replace(archive)
    write_json(path,payload)
    lines=[f'# {LAB.title}','',*[f'- {k}: {v}' for k,v in payload.get('student',{}).items()]]
    for k,v in sorted(payload.get('responses',{}).items()): lines.extend(['',f'## {k}','',str(v)])
    _atomic(path.with_suffix('.md'),'\n'.join(lines)+'\n')
    write_json(submission_root()/'student.json',payload.get('student',{}));return path
