from lab_config import LAB

LABELS = {
    "intro": "Introduction", "tutorial_1": "Motion estimates", "tutorial_2": "Map representations",
    "preflight": "ROS preflight", "tutorial_3": "Read SLAM in RViz",
    "mission_1": "Build a map", "mission_2": "Compare strategies", "final": "Submit",
}


def current_stage(st):
    stage = st.session_state.get("stage", LAB.stages[0])
    return stage if stage in LAB.stages else LAB.stages[0]


def set_stage(st, stage):
    if stage not in LAB.stages:
        raise ValueError(f"Unknown stage: {stage}")
    from lab.autosave import save
    from lab.session import sync_widgets

    sync_widgets(st)
    previous = current_stage(st)
    st.session_state["stage"] = stage
    st.session_state["visited_stages"] = list(dict.fromkeys([*st.session_state.get("visited_stages", []), stage]))
    try:
        save(st)
    except OSError as error:
        st.session_state["stage"] = previous
        st.error(f"Could not save before navigating: {error}")
        return
    st.rerun()


def render_progress(st):
    stage = current_stage(st)
    index = LAB.stages.index(stage)
    st.progress((index + 1) / len(LAB.stages), text=f"{index + 1}/{len(LAB.stages)}: {LABELS[stage]}")
