import json
import os
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from lab_config import LAB

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("stage", "student", "responses", "completed_missions", "checked_evidence_ids", "evidence", "settings", "history")


def submission_root():
    override = os.environ.get("WEEK08_SUBMISSION_DIR")
    if override and not Path(override).is_absolute():
        raise ValueError("WEEK08_SUBMISSION_DIR must be absolute")
    return Path(override) if override else ROOT / LAB.submission_directory


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_bytes(value if isinstance(value, bytes) else value.encode("utf-8"))
        # Cloud-sync and virus scanners can briefly hold a Windows destination open.
        for attempt in range(5):
            try:
                temporary.replace(path)
                break
            except PermissionError:
                if attempt == 4: raise
                time.sleep(.05 * (2 ** attempt))
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path, value):
    atomic(path, json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def usable(data):
    return (isinstance(data, dict) and data.get("lab_id") == LAB.id and
            all(isinstance(data.get(k), dict) for k in ("student", "responses", "evidence")) and
            isinstance(data.get("settings",{}),dict) and isinstance(data.get("history",[]),list) and
            isinstance(data.get("completed_missions", []), list))


def load_state():
    path = submission_root() / "autosave" / "responses.json"
    for candidate in (path, path.with_suffix(".bak")):
        try:
            value = json.loads(candidate.read_text(encoding="utf-8"))
            if not usable(value): continue
            value["student"] = {k: str(value["student"].get(k, "")) for k in ("name", "email")}
            if value.get("stage") in ('mission_1','mission_2'):
                value.setdefault('settings', {})['investigation_part'] = 0 if value['stage'] == 'mission_1' else 1
                value['stage'] = 'investigation'
            if value.get('stage') == 'ros_setup': value['stage'] = 'pillar_search'
            if value.get("stage") not in LAB.stages: value["stage"] = "intro"
            if value.get("schema_version", 1) < 2:
                value["completed_missions"] = []
                value["recovery_note"] = "Earlier answers were preserved. Re-run the updated experiments before finalizing."
            if candidate != path:
                value["recovered"] = True
                value["recovery_note"] = "Recovered the previous valid save. The unreadable file will be preserved."
            return value
        except (OSError, ValueError, TypeError):
            continue
    if path.exists() or path.with_suffix(".bak").exists():
        return {"recovery_blocked": True, "recovery_note": "Saved work is unreadable. Saving is blocked to preserve it. Download a backup and contact the instructor."}
    return {}


def save(st):
    if st.session_state.get("recovery_blocked"):
        raise OSError("Saved work needs recovery before new changes can be written")
    from lab.session import sync_widgets
    sync_widgets(st)
    data = {key: st.session_state[key] for key in KEYS}
    data.update(schema_version=2, lab_id=LAB.id, updated_at=datetime.now(timezone.utc).isoformat())
    path = submission_root() / "autosave" / "responses.json"
    if path.exists():
        previous = path.read_bytes()
        try:
            old = json.loads(previous)
            if not usable(old): raise ValueError("Invalid saved structure")
            if all(old.get(key) == data.get(key) for key in KEYS): return path
            atomic(path.with_suffix(".bak"), previous)
            if any(str(v).strip() and not str(data["responses"].get(k, "")).strip() for k, v in old["responses"].items()):
                atomic(path.with_name("responses.recovery."+uuid.uuid4().hex+".json"), previous)
        except (ValueError, TypeError):
            if not st.session_state.get("recovered"):
                raise OSError("Existing saved work is unreadable and will not be overwritten")
            atomic(path.with_name("responses.unreadable."+uuid.uuid4().hex+".json"), previous)
            st.session_state["recovered"] = False
    write_json(path, data)
    text = ["# Lab 7 saved answers", ""]
    for key, value in data["responses"].items(): text.extend(["## "+key, str(value), ""])
    atomic(path.with_suffix(".md"), "\n".join(text))
    write_json(submission_root()/"student.json", data["student"])
    return path
