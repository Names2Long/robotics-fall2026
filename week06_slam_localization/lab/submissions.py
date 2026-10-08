"""Versioned mission artifacts and verifiable final exports."""
from __future__ import annotations

import hashlib
import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from lab.autosave import _atomic, read_json, save, submission_root, write_json
from lab.evidence import evidence_id
from lab_config import LAB


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_mission(mission, evidence, responses, uploads=(), *, state_signature=None):
    """Write checked artifacts first and the identifying submission record last.

    uploads is a mapping from stable, role-based destination names to Artifact objects.
    A failed write cannot make the mission appear complete.
    """
    target = submission_root() / mission
    target.mkdir(parents=True, exist_ok=True)
    previous_names = set()
    if (target / "submission.json").exists():
        try:
            previous_names = set(read_json(target / "submission.json").get("artifact_hashes", {}))
        except (OSError, ValueError, TypeError):
            pass
        recovery = submission_root() / "autosave" / "recovery" / (mission + "." + uuid.uuid4().hex)
        for old in target.iterdir():
            if old.is_file() and not old.name.endswith(".tmp"):
                _atomic(recovery / old.name, old.read_bytes())
    lines = [f"# {mission.replace('_', ' ').title()}", ""]
    for key, value in sorted(responses.items()):
        if key.startswith(mission + "."):
            lines.extend([f"## {key.split('.', 1)[1].replace('_', ' ').title()}", "", str(value), ""])
    artifacts = {
        "explanation.md": "\n".join(lines).encode("utf-8"),
        "evidence.json": json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False).encode("utf-8"),
    }
    items = uploads.items() if isinstance(uploads, dict) else (
        (f"upload_{index:02d}_{Path(item.name).name}", item) for index, item in enumerate(uploads, 1)
    )
    for name, item in items:
        if item is None:
            continue
        if Path(name).name != name or name in ("", ".", ".."):
            raise ValueError("Unsafe artifact destination")
        artifacts[name] = item.getvalue()
    for name, data in artifacts.items():
        _atomic(target / name, data)
    payload = {
        "schema_version": 2, "lab_id": LAB.id, "mission_id": mission,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "state_signature": state_signature, "evidence": evidence,
        "artifact_hashes": {name: _digest(data) for name, data in artifacts.items()},
    }
    write_json(target / "submission.json", payload)
    for name in previous_names - artifacts.keys():
        if Path(name).name == name and name not in ("", ".", "..", "submission.json"):
            (target / name).unlink(missing_ok=True)
    return target


def export_files():
    root = submission_root()
    names = {
        "student.json", "autosave/responses.json", "autosave/responses.md",
        "final_synthesis.md", "final_reflection.md",
    }
    for mission in LAB.missions:
        record_path = root / mission / "submission.json"
        if not record_path.is_file():
            continue
        names.add(f"{mission}/submission.json")
        try:
            record = read_json(record_path)
            names.update(
                f"{mission}/{name}" for name in record.get("artifact_hashes", {})
                if Path(name).name == name
            )
        except (OSError, ValueError, TypeError):
            continue
    return sorted(root / name for name in names if (root / name).is_file())


def write_manifest(st):
    from lab.completion import mission_status

    status = mission_status(st)
    if not all(status.values()):
        raise ValueError("Recheck and save every changed mission before export")
    if not all(str(st.session_state["student"].get(key, "")).strip() for key in ("name", "email")):
        raise ValueError("Student identity is incomplete")
    responses = st.session_state["responses"]
    if not 200 <= len(str(responses.get("final.synthesis", "")).split()) <= 300:
        raise ValueError("Final synthesis must contain 200–300 words")
    if not 1 <= len(str(responses.get("final.course_reflection", "")).split()) <= 300:
        raise ValueError("Reflection must contain 1–300 words")
    save(st)
    root = submission_root()
    required = ("student.json", "autosave/responses.json", "autosave/responses.md",
                "final_synthesis.md", "final_reflection.md")
    if not all((root / name).is_file() for name in required):
        raise ValueError("Required submission files are missing")
    files = {path.relative_to(root).as_posix(): _digest(path.read_bytes()) for path in export_files()}
    path = root / "manifest.json"
    write_json(path, {
        "schema_version": 2, "lab_id": LAB.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "student": dict(st.session_state["student"]),
        "mission_signatures": dict(st.session_state["checked_evidence_ids"]),
        "response_signature": evidence_id(dict(responses)),
        "files": files,
    })
    return path


def manifest_current(st):
    from lab.completion import mission_status

    try:
        data = read_json(submission_root() / "manifest.json")
        if not all(mission_status(st).values()):
            return False
        if data.get("student") != dict(st.session_state["student"]):
            return False
        if data.get("mission_signatures") != dict(st.session_state["checked_evidence_ids"]):
            return False
        if data.get("response_signature") != evidence_id(dict(st.session_state["responses"])):
            return False
        root = submission_root()
        files = {path.relative_to(root).as_posix(): _digest(path.read_bytes()) for path in export_files()}
        return files == data.get("files")
    except (OSError, ValueError, TypeError, KeyError):
        return False


def submission_zip(st):
    if not manifest_current(st):
        raise ValueError("Prepare a fresh submission before downloading")
    root = submission_root()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [*export_files(), root / "manifest.json"]:
            archive.write(path, path.relative_to(root).as_posix())
    return output.getvalue()
