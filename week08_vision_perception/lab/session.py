from copy import deepcopy


def initialize(st):
    defaults = {"stage": "intro", "student": {"name": "", "email": ""}, "responses": {},
                "completed_missions": [], "checked_evidence_ids": {}, "evidence": {}, "settings": {}, "history": []}
    for key, value in defaults.items():
        st.session_state.setdefault(key, deepcopy(value))


def response(st, key, default=""):
    return st.session_state["responses"].get(key, default)


def set_response(st, key, value):
    st.session_state["responses"] = {**st.session_state["responses"], key: value}


def sync_widgets(st):
    for key in list(st.session_state):
        if key.startswith("field."):
            set_response(st, key[6:], st.session_state[key])
        elif key.startswith("student."):
            st.session_state["student"] = {**st.session_state["student"], key[8:]: st.session_state[key]}


def complete_mission(st, mission, evidence_id):
    st.session_state["completed_missions"] = list(dict.fromkeys([*st.session_state["completed_missions"], mission]))
    st.session_state["checked_evidence_ids"][mission] = evidence_id
