from __future__ import annotations

from lab_config import LAB


LABELS = {
    "intro": "Introduction",
    "concepts": "Guided walkthroughs",
    "preflight": "Environment",
    "mission_1": "Predict motion",
    "mission_2": "Frames",
    "mission_3": "AI-assisted development",
    "final": "Submit",
}


def current_stage(st) -> str:
    stage = str(st.session_state.get("stage", LAB.stages[0]))
    return stage if stage in LAB.stages else LAB.stages[0]


def set_stage(st, stage: str) -> None:
    if stage not in LAB.stages:
        raise ValueError(f"Unknown stage: {stage}")
    st.session_state["stage"] = stage
    visited=list(st.session_state.get('visited_stages',['intro']))
    if stage not in visited: visited.append(stage)
    st.session_state['visited_stages']=visited
    st.session_state["scroll_to_top_pending"] = True
    st.rerun()


def render_progress(st) -> None:
    if st.session_state.pop("scroll_to_top_pending", False):
        st.html("""<script>
        function topOfGuide() {
          window.scrollTo({top:0,left:0,behavior:'instant'});
          document.querySelectorAll('[data-testid="stMain"], .main').forEach(e => e.scrollTop=0);
        }
        setTimeout(topOfGuide,30); setTimeout(topOfGuide,180);
        </script>""", unsafe_allow_javascript=True)
    stage = current_stage(st)
    index = LAB.stages.index(stage)
    st.progress((index + 1) / len(LAB.stages), text=f"{index + 1}/{len(LAB.stages)}: {LABELS[stage]}")
    visited=set(st.session_state.get('visited_stages',['intro']))|{stage}
    st.sidebar.caption('Return to any section you have opened. Recheck and save a mission after editing it.')
    for destination in LAB.stages:
        if st.sidebar.button(LABELS[destination],key=f'nav.{destination}',disabled=destination not in visited or destination==stage):
            set_stage(st,destination)
    if st.sidebar.button('Save progress now'):
        # Values in focused fields are submitted with the button click.
        st.session_state['_explicit_save']=True
    st.sidebar.caption('Use each form’s Save/Check button to submit its fields. Keep Docker running while using the guide. If it pauses or disconnects, copy unsent text before refreshing. Use one guide tab for your work.')
