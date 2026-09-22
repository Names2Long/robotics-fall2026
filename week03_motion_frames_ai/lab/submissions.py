from __future__ import annotations

import json
import shutil
import hashlib
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab.autosave import submission_root, _atomic
from lab_config import LAB


ROOT = Path(__file__).resolve().parents[1]


def save_mission(mission_id: str, evidence: dict[str, Any], responses: dict[str, Any]) -> Path:
    target = submission_root() / mission_id
    target.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "lab_id": LAB.id,
        "mission_id": mission_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "evidence": evidence,
    }
    _atomic(target / "submission.json",json.dumps(payload,indent=2))
    _atomic(target / "latest_run.json",json.dumps(evidence,indent=2))
    prefix = f"{mission_id}."
    lines = [f"# {mission_id.replace('_', ' ').title()}", ""]
    for key, value in responses.items():
        if key.startswith(prefix):
            lines.extend([f"## {key[len(prefix):].replace('_', ' ').title()}", "", str(value), ""])
    _atomic(target / "explanation.md","\n".join(lines))
    return target


def snapshot_pattern_source() -> Path:
    source = ROOT / "ros2_ws" / "src" / "week03_pattern"
    target = submission_root() / "mission_3" / "source"
    target.mkdir(parents=True, exist_ok=True)
    for relative in (
        "package.xml",
        "setup.py",
        "setup.cfg",
        "week03_pattern/pattern.py",
        "week03_pattern/pattern_node.py",
        "test/test_pattern.py",
        "test/test_student_pattern.py",
        "week03_pattern/checks.py",
    ):
        source_file = source / relative
        if source_file.exists():
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination)
    for folder in ('week03_pattern','test'):
        for source_file in (source/folder).rglob('*.py'):
            destination=target/source_file.relative_to(source)
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source_file,destination)
    return target


def snapshot_camera_source() -> Path:
    source=ROOT/"ros2_ws/src/week03_camera_transform"
    target=submission_root()/"mission_2"/"source";target.mkdir(parents=True,exist_ok=True)
    for relative in ("package.xml","setup.py","setup.cfg","week03_camera_transform/camera_transform.py"):
        path=source/relative
        if path.exists():
            destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
    for path in (source/"week03_camera_transform").rglob("*.py"):
        destination=target/path.relative_to(source);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
    return target


def write_manifest(st) -> Path:
    root = submission_root()
    root.mkdir(parents=True, exist_ok=True)
    files = sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file() and path.name != "manifest.json" and 'autosave' not in path.relative_to(root).parts and path.suffix not in ('.tmp','.bak','.zip')
    )
    payload = {
        "schema_version": 1,
        "lab_id": LAB.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "student": dict(st.session_state.get("student", {})),
        "completed_missions": list(st.session_state.get("completed_missions", [])),
        "checked_evidence_ids": dict(st.session_state.get("checked_evidence_ids", {})),
        "files": files,
        "sha256": {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files},
    }
    path = root / "manifest.json"
    from lab.completion import verification_summary
    payload['verification']=verification_summary(st)
    payload['live_verification_pending']=[r['activity'] for r in payload['verification'] if not r['live_verified']]
    _atomic(path,json.dumps(payload,indent=2))
    return path


def submission_zip():
    root=submission_root();manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in [*manifest['files'],'manifest.json']:
            path=(root/name).resolve()
            if not path.is_relative_to(root.resolve()): raise ValueError('Invalid submission path')
            contents=path.read_bytes()
            if name!='manifest.json' and hashlib.sha256(contents).hexdigest()!=manifest['sha256'][name]:
                raise ValueError('Submission files changed. Prepare the submission again.')
            archive.writestr(name,contents)
    return buffer.getvalue()
