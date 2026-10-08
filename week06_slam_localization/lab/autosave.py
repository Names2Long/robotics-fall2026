"""Recoverable, versioned progress storage for the Week 6 guide."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from lab_config import LAB

ROOT = Path(__file__).resolve().parents[1]
CONTENT_VERSION = 5
STATE_KEYS = (
    "stage", "student", "responses", "completed_missions", "checked_evidence_ids",
    "evidence", "tutorial_complete", "prediction_locks", "visited_stages",
)


def submission_root() -> Path:
    override = os.environ.get("WEEK06_SUBMISSION_DIR", "").strip()
    if override:
        path = Path(override).expanduser()
        if not path.is_absolute():
            raise ValueError("WEEK06_SUBMISSION_DIR must be an absolute path")
        return path
    return ROOT / LAB.submission_directory


def _atomic(path: Path, data: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        if isinstance(data, bytes):
            temporary.write_bytes(data)
        else:
            temporary.write_text(data, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path: Path, payload: dict) -> None:
    _atomic(path, json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _usable(data: object) -> bool:
    if not isinstance(data, dict) or data.get("lab_id") != LAB.id:
        return False
    if not isinstance(data.get("student"), dict) or not isinstance(data.get("responses"), dict):
        return False
    if any(not isinstance(data["student"].get(key), str) for key in ("name", "email")):
        return False
    for key in ("checked_evidence_ids", "evidence", "tutorial_complete", "prediction_locks"):
        if key in data and not isinstance(data[key], dict):
            return False
    for key in ("completed_missions", "visited_stages"):
        if key in data and not isinstance(data[key], list):
            return False
    return True


def load_state() -> dict:
    path = submission_root() / "autosave" / "responses.json"
    backup = path.with_suffix(".bak")
    for candidate in (path, backup):
        try:
            data = read_json(candidate)
            if not _usable(data):
                continue
            if candidate == backup:
                data["recovery_note"] = "The latest autosave was unreadable; an earlier valid save was recovered."
                data["recovered_from_backup"] = True
            if data.get("stage") == "concepts":
                data["stage"] = "tutorial_1"
            if data.get("stage") in ("tutorial_4", "tutorial_5", "mission_3"):
                data["stage"] = "final" if "mission_2" in data.get("checked_evidence_ids", {}) else "mission_2"
                data["recovery_note"] = "The localization section was moved to a future lab module. Your earlier answers and files were preserved. Lab 6 now ends after Mission 2."
            if data.get("stage") not in LAB.stages:
                data["stage"] = "intro"
            if data.get("content_version", 1) < CONTENT_VERSION:
                # Keep all existing answers and files. Updated checks must be run again.
                data["completed_missions"] = []
                data["checked_evidence_ids"] = {}
                data["recovery_note"] = (
                    "Earlier answers and evidence were restored. Recheck each mission against the new requirements; "
                    "your previous files have not been removed."
                )
            return data
        except (OSError, ValueError, TypeError):
            continue
    if path.exists() or backup.exists():
        return {
            "recovery_blocked": True,
            "recovery_note": "Saved work could not be read. Nothing has been overwritten. Back up student_submission and ask the instructor for help.",
        }
    return {}


def save(st) -> Path:
    if st.session_state.get("recovery_blocked"):
        raise OSError("Autosave blocked to protect unreadable work")
    payload = {key: st.session_state[key] for key in STATE_KEYS if key in st.session_state}
    payload.update(
        schema_version=2, content_version=CONTENT_VERSION, lab_id=LAB.id,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    path = submission_root() / "autosave" / "responses.json"
    if path.exists():
        previous = path.read_bytes()
        try:
            prior = json.loads(previous)
            if not _usable(prior):
                raise ValueError("Invalid autosave structure")
            if all(prior.get(key) == payload.get(key) for key in STATE_KEYS) and (
                path.with_suffix(".md").exists() and (submission_root() / "student.json").exists()
            ):
                return path
            _atomic(path.with_suffix(".bak"), previous)
            removed = [
                key for key, value in prior["responses"].items()
                if str(value).strip() and not str(payload.get("responses", {}).get(key, "")).strip()
            ]
            if removed:
                _atomic(path.with_name("responses.recovery." + uuid.uuid4().hex + ".json"), previous)
        except (ValueError, TypeError):
            if not st.session_state.get("recovered_from_backup"):
                # Never replace unreadable work with a fresh blank save.
                raise OSError("Existing autosave is unreadable; preserve it before continuing")
            _atomic(path.with_name("responses.unreadable." + uuid.uuid4().hex + ".json"), previous)
            st.session_state["recovered_from_backup"] = False
    write_json(path, payload)
    lines = [f"# {LAB.title}", ""]
    lines += [f"- {key}: {value}" for key, value in payload.get("student", {}).items()]
    for key, value in sorted(payload.get("responses", {}).items()):
        lines += ["", f"## {key}", "", str(value)]
    _atomic(path.with_suffix(".md"), "\n".join(lines) + "\n")
    write_json(submission_root() / "student.json", payload.get("student", {}))
    return path
