from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab_config import LAB


ROOT = Path(__file__).resolve().parents[1]
CONTENT_VERSION = 2


def submission_root() -> Path:
    override = os.environ.get("WEEK03_SUBMISSION_DIR", "").strip()
    if override:
        path = Path(override).expanduser()
        if not path.is_absolute():
            raise ValueError("WEEK03_SUBMISSION_DIR must be an absolute path")
        return path
    return ROOT / LAB.submission_directory


def load_state() -> dict[str, Any]:
    path = submission_root() / "autosave" / "responses.json"
    for candidate in (path,path.with_suffix('.bak')):
        try:
            data=json.loads(candidate.read_text(encoding='utf-8'))
            if not isinstance(data,dict) or not isinstance(data.get('responses'),dict):
                continue
            if candidate!=path:
                data['recovery_note']='The latest autosave could not be read. Your previous saved copy was restored.'
            return data
        except (OSError,ValueError):
            pass
    return {'recovery_note':'Saved progress could not be read. Keep the existing files and contact your instructor.'} if path.exists() else {}


def _atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def save(st) -> Path:
    payload = {
        "schema_version": 1,
        "content_version": CONTENT_VERSION,
        "lab_id": LAB.id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "student": dict(st.session_state.get("student", {})),
        "responses": dict(st.session_state.get("responses", {})),
        "completed_missions": list(st.session_state.get("completed_missions", [])),
        "checked_evidence_ids": dict(st.session_state.get("checked_evidence_ids", {})),
        "stage": st.session_state.get('stage','intro'),
        "walkthrough_index": st.session_state.get('walkthrough.index',0),
        "visited_stages": st.session_state.get('visited_stages',['intro']),
    }
    path = submission_root() / "autosave" / "responses.json"
    serialized=json.dumps(payload,indent=2,sort_keys=True)
    if path.exists():
        try:
            previous=path.read_text(encoding='utf-8')
            json.loads(previous)
            _atomic(path.with_suffix('.bak'),previous)
        except (OSError,ValueError):
            pass
    _atomic(path, serialized)
    lines = [f"# {LAB.title}", "", "## Student", ""]
    for key, value in payload["student"].items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    for key, value in sorted(payload["responses"].items()):
        if key=='mission_1.sketch':
            value='Sketch image retained in the JSON autosave and exported with Mission 1.'
        lines.extend(["", f"## {key}", "", str(value)])
    _atomic(path.with_suffix(".md"), "\n".join(lines) + "\n")
    (submission_root() / "student.json").write_text(json.dumps(payload["student"], indent=2), encoding="utf-8")
    return path


def restore(st):
    if st.session_state.get('_progress_loaded'):
        return
    st.session_state['_progress_loaded']=True
    data=load_state()
    if data and int(data.get('content_version',0))<CONTENT_VERSION:
        responses=dict(data.get('responses',{}));responses.pop('walkthrough.completed',None)
        data['responses']=responses;data['completed_missions']=[];data['checked_evidence_ids']={}
        data['stage']='concepts';data['walkthrough_index']=0
        data['recovery_note']='The Lab 3 activities were updated. Your written work was retained, but revised walkthroughs and missions must be checked again.'
    for key in ('responses','student','completed_missions','checked_evidence_ids','visited_stages'):
        if key in data:
            st.session_state[key]=data[key]
    if data.get('stage') in LAB.stages:
        st.session_state['stage']=data['stage']
    index=data.get('walkthrough_index',0)
    st.session_state['walkthrough.index']=index if isinstance(index,int) and 0<=index<5 else 0
    if data.get('recovery_note'):
        st.session_state['recovery_note']=data['recovery_note']
