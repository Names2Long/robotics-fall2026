from __future__ import annotations

import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from lab.autosave import submission_root


def assigned_pattern(course_id: str) -> str:
    options = ("rounded_rectangle", "l_path", "alternating_arcs")
    digest = hashlib.sha256(course_id.strip().lower().encode("utf-8")).digest()
    return options[digest[0] % len(options)]


def lock_original(course_id: str, specification: str, prompt: str, output: str, original_source: str | None = None) -> dict[str, str]:
    target = submission_root() / "mission_3" / "ai"
    target.mkdir(parents=True, exist_ok=True)
    if (target / "original_output.txt").exists():
        raise FileExistsError("The original AI output has already been locked")
    metadata = {
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "pattern": assigned_pattern(course_id),
        "specification_sha256": hashlib.sha256(specification.encode("utf-8")).hexdigest(),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }
    (target / "specification.txt").write_text(specification, encoding="utf-8")
    (target / "original_prompt.txt").write_text(prompt, encoding="utf-8")
    (target / "original_output.txt").write_text(output, encoding="utf-8")
    if original_source is not None:
        (target / "original_source.py").write_text(original_source, encoding="utf-8")
        metadata["source_sha256"] = hashlib.sha256(original_source.encode("utf-8")).hexdigest()
    (target / "lock.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def load_lock() -> dict[str, str]:
    directory = submission_root() / "mission_3" / "ai"
    path = directory / "lock.json"
    if not path.exists():
        return {}
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(metadata,dict): raise ValueError('Invalid AI record')
    except (OSError,ValueError):
        return {'integrity_valid':False,'error':'The AI record could not be read. Restore it from your saved copy.'}
    files = {
        "specification_sha256": directory / "specification.txt",
        "prompt_sha256": directory / "original_prompt.txt",
        "output_sha256": directory / "original_output.txt",
    }
    if metadata.get("source_sha256"):
        files["source_sha256"] = directory / "original_source.py"
    metadata["integrity_valid"] = all(
        file.exists()
        and hashlib.sha256(file.read_text(encoding="utf-8").encode("utf-8")).hexdigest() == metadata.get(key)
        for key, file in files.items()
    )
    return metadata


def write_diff(final_source: Path) -> Path:
    ai_dir = submission_root() / "mission_3" / "ai"
    original_path = ai_dir / "original_source.py"
    if not original_path.exists():
        original_path = ai_dir / "original_output.txt"
    if not original_path.exists():
        raise FileNotFoundError("Lock the original AI output first")
    original = original_path.read_text(encoding="utf-8").splitlines(keepends=True)
    final = final_source.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(original, final, fromfile="original_ai_output", tofile="final_pattern.py"))
    path = ai_dir / "ai_to_final.diff"
    path.write_text(diff or "# No textual difference detected.\n", encoding="utf-8")
    return path
