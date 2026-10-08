from __future__ import annotations


def initialize(st):
    defaults = {
        "stage": "intro", "student": {"name": "", "email": ""},
        "responses": {}, "completed_missions": [], "checked_evidence_ids": {},
        "evidence": {}, "tutorial_complete": {}, "prediction_locks": {},
        "visited_stages": ["intro"],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def response(st, key, default=""):
    return st.session_state.get("responses", {}).get(key, default)


def set_response(st, key, value):
    payload = dict(st.session_state.get("responses", {}))
    payload[key] = value
    st.session_state["responses"] = payload


def sync_widgets(st):
    responses = dict(st.session_state.get("responses", {}))
    student = dict(st.session_state.get("student", {}))
    for key in list(st.session_state):
        if key.startswith("field."):
            responses[key[6:]] = st.session_state[key]
        elif key.startswith("student."):
            student[key[8:]] = st.session_state[key]
    st.session_state["responses"] = responses
    st.session_state["student"] = student


def complete_mission(st, mission, evidence_id):
    completed = list(st.session_state["completed_missions"])
    if mission not in completed:
        completed.append(mission)
    st.session_state["completed_missions"] = completed
    ids = dict(st.session_state["checked_evidence_ids"])
    ids[mission] = evidence_id
    st.session_state["checked_evidence_ids"] = ids
