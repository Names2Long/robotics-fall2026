"""Atomic evidence storage, recoverable progress and portable submission exports."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import zipfile
import uuid

ROOT = Path(__file__).resolve().parents[1]


def submission_root():
    return Path(os.environ.get('WEEK09_SUBMISSION_DIR',str(ROOT/'student_submission'))).resolve()


def atomic_json(path,payload):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temporary.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    temporary.replace(path)


def load():
    path = submission_root()/'autosave/responses.json'
    if not path.exists():
        return {}
    for candidate in (path,path.with_suffix('.backup.json')):
        try:
            result = json.loads(candidate.read_text(encoding='utf-8'))
            if not isinstance(result,dict):
                raise ValueError('Progress must be an object')
            if result.get('schema_version') != 2:
                result['completed_missions'] = []
                result['evidence'] = {}
                result['stage'] = 'intro'
                result['migration_notice'] = 'Your earlier responses were preserved. The revised missions need new evidence.'
            if candidate != path:
                shutil.copy2(path,path.with_suffix('.damaged.json'))
                result['migration_notice'] = 'Recovered the previous backup. The damaged autosave was preserved.'
            return result
        except (OSError,ValueError):
            pass
    raise ValueError(f'Cannot read progress or its backup at {path}. Preserve these files and contact your instructor. Nothing was overwritten.')


def save(state):
    path = submission_root()/'autosave/responses.json'
    if path.exists():
        try:
            json.loads(path.read_text(encoding='utf-8'))
            shutil.copy2(path,path.with_suffix('.backup.json'))
        except (OSError,ValueError):
            pass
    payload = {key:state.get(key,default) for key,default in
               [('student',{}),('responses',{}),('evidence',{}),('completed_missions',[]),('stage','intro'),('settings',{})]}
    payload.update(schema_version=2,lab_id='week09_planning_navigation')
    atomic_json(path,payload)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_evidence(mission,evidence,responses):
    folder = submission_root()/mission
    atomic_json(folder/'checked_evidence.json',evidence)
    atomic_json(folder/'responses.json',{k:v for k,v in responses.items() if k.startswith(mission+'.')})


def export(state,complete=False):
    save(state)
    root = submission_root()
    manifest = dict(schema=2,status='complete' if complete else 'draft',student=state['student'],
                    completed_missions=state['completed_missions'],files={})
    for path in sorted(root.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.name != 'manifest.json' and not path.name.endswith(('.tmp','.backup.json','.damaged.json','.pyc','.pyo')):
            manifest['files'][str(path.relative_to(root)).replace('\\','/')] = sha(path)
    atomic_json(root/'manifest.json',manifest)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in [*manifest['files'],'manifest.json']:
            archive.write(root/name,arcname=f'student_submission/{name}')
    return buffer.getvalue()
