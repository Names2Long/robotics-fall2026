import io
import json
import hashlib
import zipfile
from datetime import datetime, timezone
from lab.autosave import atomic, save, submission_root, write_json
from lab.completion import readiness, QUESTIONS
from perception.experiments import csv_bytes, evidence_images, validate, signature


def store_run(st, mission, evidence):
    old = st.session_state["evidence"].get(mission)
    root = submission_root()/mission
    if old and old != evidence:
        write_json(root/"history"/(signature(old)+".json"), old)
        if mission == "mission_3":
            st.session_state["history"] = [*st.session_state["history"], {"config": old["config"], "summaries": old["result"]["summaries"]}][-10:]
    st.session_state["evidence"][mission] = evidence
    write_json(root/"evidence.json", evidence)
    if evidence.get("program"):
        atomic(root/"executed_code.py", evidence["program"] + "\n")
    if mission != "mission_3":
        atomic(root/"predictions.csv", csv_bytes(evidence))
        results = validate(evidence, evidence["method"])
        write_json(root/"metrics.json", results)
        from perception.reports import artifacts
        for name,data in artifacts(evidence,results): atomic(root/name,data)
        for name, data in evidence_images(evidence): atomic(root/name, data)
    save(st)


def export(st, final=False):
    save(st)
    checks = readiness(st.session_state)
    if final and not all(row["ready"] for row in checks):
        raise ValueError("Some items need attention. You can still download a draft")
    root = submission_root()
    write_json(root/"student.json",st.session_state["student"])
    # Never leave an old complete marker if rewriting artifacts fails partway through.
    write_json(root/"manifest.json", {"schema_version":2,"status":"draft","detail":"Export in progress"})
    required = []
    for mission, evidence in st.session_state["evidence"].items():
        if mission not in QUESTIONS: continue
        target = root/mission
        write_json(target/"evidence.json",evidence)
        required.append(target/"evidence.json")
        if mission in ('pillar_search','line_following'):
            from perception.robot_evidence import validate_bundle, artifacts as robot_artifacts
            try:
                summaries = validate_bundle(evidence,mission)
            except (ValueError,KeyError,TypeError):
                if final: raise
                continue
            write_json(target/'summary.json',summaries)
            required.append(target/'summary.json')
            for index,report in enumerate(evidence['reports']):
                for name,data in robot_artifacts(report):
                    path = target/f'attempt_{index+1}'/name
                    atomic(path,data)
                    required.append(path)
            continue
        if evidence.get("program"):
            atomic(target/"executed_code.py",evidence["program"] + "\n")
            required.append(target/"executed_code.py")
        if mission != "mission_3":
            # Recreate deleted or damaged artifacts from validated canonical evidence.
            try:
                results = validate(evidence,evidence["method"])
            except (ValueError,KeyError,TypeError):
                if final: raise
                # Drafts remain available when an older experiment needs rerunning.
                continue
            atomic(target/"predictions.csv",csv_bytes(evidence))
            write_json(target/"metrics.json",results)
            required.extend([target/"predictions.csv",target/"metrics.json"])
            from perception.reports import artifacts
            for name,data in artifacts(evidence,results):
                atomic(target/name,data)
                required.append(target/name)
            for name,data in evidence_images(evidence):
                atomic(target/name,data)
                required.append(target/name)
        else:
            write_json(target/"timeline.json",evidence["result"]["timeline"])
            required.append(target/"timeline.json")
    implementation = {k:v for k,v in st.session_state["responses"].items() if k.startswith("implementation.")}
    write_json(root/"student_implementation.json",implementation)
    for mission in QUESTIONS:
        lines = ["# "+mission, ""]
        for key, value in st.session_state["responses"].items():
            if key.startswith(mission+"."): lines.extend(["## "+key.split(".", 1)[1], value, ""])
        atomic(root/mission/"explanation.md", "\n".join(lines))
    for key, name in (("final.synthesis", "final_synthesis.md"), ("final.course_reflection", "final_reflection.md")):
        atomic(root/name, str(st.session_state["responses"].get(key, "")))
    required.extend([root/"student_implementation.json",root/"student.json",root/"final_synthesis.md",root/"final_reflection.md"])
    required.extend(root/mission/"explanation.md" for mission in QUESTIONS)
    if final and any(not path.is_file() or path.stat().st_size == 0 for path in required):
        raise ValueError("An expected submission file is missing or empty. Draft retained. Retry export after checking disk access")
    files = {str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in root.rglob("*") if p.is_file() and p.name != "manifest.json" and not p.name.endswith(".tmp")}
    write_json(root/"manifest.json", {"schema_version": 2, "status": "complete" if final else "draft",
               "created_at": datetime.now(timezone.utc).isoformat(), "checks": checks,
               "required_files": [str(p.relative_to(root)).replace("\\", "/") for p in required], "files_sha256": files})
    return root


def backup_bytes():
    buffer = io.BytesIO()
    root = submission_root()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and not path.name.endswith(".tmp"):
                    archive.write(path, str(path.relative_to(root)))
    return buffer.getvalue()


def write_manifest(st):
    return export(st, final=True)/"manifest.json"
