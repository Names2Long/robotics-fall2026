"""Preserve Mission 2 AI output separately from the revised implementation."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime,timezone
from lab.autosave import submission_root


def lock_original(prompt,output,source):
    target=submission_root()/"mission_2"/"ai";target.mkdir(parents=True,exist_ok=True)
    if (target/"lock.json").exists(): raise FileExistsError("The Mission 2 AI output is already preserved")
    files={"prompt.txt":prompt,"original_output.txt":output,"original_source.py":source}
    metadata={"locked_at":datetime.now(timezone.utc).isoformat(),"hashes":{}}
    for name,value in files.items():
        (target/name).write_text(value,encoding="utf-8");metadata["hashes"][name]=hashlib.sha256(value.encode()).hexdigest()
    (target/"lock.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8");return metadata


def load_lock():
    target=submission_root()/"mission_2"/"ai";path=target/"lock.json"
    if not path.exists(): return {}
    try: metadata=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError): return {"integrity_valid":False}
    metadata["integrity_valid"]=all((target/name).exists() and hashlib.sha256((target/name).read_bytes()).hexdigest()==digest
                                     for name,digest in metadata.get("hashes",{}).items())
    return metadata
