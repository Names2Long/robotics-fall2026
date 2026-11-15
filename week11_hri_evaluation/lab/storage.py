"""Local progress and explicit submission files for the handover lab."""
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import time
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

LAB_DIR = Path(__file__).resolve().parents[1]


def root():
    return Path(os.environ.get("WEEK11_SUBMISSION_DIR", LAB_DIR / "student_submission")).resolve()


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_bytes(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def json_bytes(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def progress_path():
    return root() / ".lab10-progress.json"


def backup_path():
    return root() / ".lab10-progress.backup.json"


def decode_progress(content):
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("The progress record must contain an object.")
    return data


def load():
    primary = progress_path()
    backup = backup_path()
    if not primary.exists() and not backup.exists():
        return {}
    try:
        return decode_progress(primary.read_bytes())
    except (FileNotFoundError, ValueError):
        if not backup.exists():
            raise ValueError("The primary progress record is damaged and no backup is available.")
        data = decode_progress(backup.read_bytes())
        data["recovered_backup"] = True
        return data


def save(data):
    if data.get("active"):
        data["active"]["saved_at"] = time.time()
    encoded = json_bytes(data)
    path = progress_path()
    if path.exists():
        previous = path.read_bytes()
        if previous == encoded:
            return
        try:
            decode_progress(previous)
        except ValueError:
            atomic(root() / f".lab10-progress.{uuid4().hex}.damaged.json", previous)
        else:
            atomic(backup_path(), previous)
    atomic(path, encoded)


def archive(work, label, record):
    if record is not None:
        work.setdefault("history", []).append({"label": label, "record": record})


def resume_trial(run, now=None):
    """Exclude time away from the guide from movement and offer timers."""
    now = time.time() if now is None else now
    paused = max(0, now - run.get("saved_at", now))
    trial = run["trial"]
    for key in ("opened", "start", "entered", "finished"):
        if trial.get(key) is not None:
            trial[key] += paused
    run["last_tick"] = now
    run["saved_at"] = now


def planner_source():
    path = root() / "mission_1" / "controller.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output:
            output.write((LAB_DIR / "controller_starter.py").read_bytes())
    except FileExistsError:
        pass
    return path


def submission_files(data, synthesis, reflection):
    controller = planner_source()
    source = controller.read_text(encoding="utf-8-sig")
    if source != data["mission_1"]["source"]:
        raise ValueError("Run Mission 1 checks again for the edited controller.")
    files = {
        "mission_1/controller.py": controller.read_bytes(),
        "mission_1/checks.json": json_bytes(data["mission_1"]["checks"]),
        "mission_1/ros_trial.json": json_bytes(data["practice"]),
        "mission_1/guard_explanation.md": data["mission_1"]["explanation"].encode(),
        "mission_2/voice_trials.json": json_bytes(data["voice"]),
        "mission_2/redesign.json": json_bytes(data["redesign"]),
        "mission_2/retest.json": json_bytes(data["retest"]),
        "mission_2/analysis.md": data["voice_analysis"].encode(),
        "mission_3/mode_trials.json": json_bytes(data["modes"]),
        "technical_synthesis.md": synthesis.encode(),
        "final_reflection.md": reflection.encode(),
    }
    files["manifest.json"] = json_bytes({name: hashlib.sha256(value).hexdigest()
                                        for name, value in files.items()})
    return files


def bundle(files, prefix):
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(prefix + "/" + name, content)
    return buffer.getvalue()


def draft_backup(data):
    files = {".lab10-progress.json": json_bytes(data)}
    source = root() / "mission_1" / "controller.py"
    if source.exists():
        files["mission_1/controller.py"] = source.read_bytes()
    return bundle(files, "lab10_draft")


def export(files):
    for name, content in files.items():
        if name != "mission_1/controller.py":
            atomic(root() / name, content)


def export_current(files):
    return all((root() / name).is_file() and (root() / name).read_bytes() == content
               for name, content in files.items())
