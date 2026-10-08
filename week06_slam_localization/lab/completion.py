"""Current-evidence checks shared by navigation and final submission."""
import hashlib

from lab.autosave import CONTENT_VERSION, read_json, submission_root
from lab.evidence import evidence_id
from lab_config import LAB


def current_signature(st, mission):
    responses = {key: value for key, value in st.session_state["responses"].items() if key.startswith(mission + ".")}
    predictions = {
        key: value for key, value in st.session_state.get("prediction_locks", {}).items()
        if key.startswith(mission + ".")
    }
    evidence = st.session_state["evidence"].get(mission)
    context = None
    if mission == "mission_2":
        context = st.session_state["evidence"].get("mission_1")
    return evidence_id(CONTENT_VERSION, mission, st.session_state["student"].get("email"), context, evidence, responses, predictions)


def saved_matches(mission, signature):
    root = submission_root() / mission
    try:
        record = read_json(root / "submission.json")
        hashes = record["artifact_hashes"]
        if record.get("lab_id") != LAB.id or record.get("state_signature") != signature:
            return False
        if not isinstance(hashes, dict) or not {"explanation.md", "evidence.json"}.issubset(hashes):
            return False
        if mission in ("mission_1", "mission_2") and not {"map.yaml", "map.pgm"}.issubset(hashes):
            return False
        if mission in ("mission_1", "mission_2") and not any(name.startswith("rviz_screenshot.") for name in hashes):
            return False
        return all(
            (root / name).is_file() and hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
            for name, digest in hashes.items()
        )
    except (OSError, ValueError, TypeError, KeyError):
        return False


def mission_status(st):
    return {
        mission: bool(
            st.session_state["checked_evidence_ids"].get(mission) == current_signature(st, mission)
            and saved_matches(mission, current_signature(st, mission))
        )
        for mission in LAB.missions
    }


def refresh_completion(st):
    status = mission_status(st)
    st.session_state["completed_missions"] = [mission for mission, valid in status.items() if valid]
    return status
