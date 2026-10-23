from lab_config import LAB
from lab.autosave import save

LABELS = {"intro": "Start", "concepts": "Image playground", "preflight": "Preflight", "mission_1": "Classical detector",
          "mission_2": "Compare detectors", "investigation": "Mission 1: detector investigation", "final": "Synthesis and submission",
          "pillar_search": "Mission 2: pillar search", "line_following": "Mission 3: line following"}


def current_stage(st):
    stage = st.session_state.get("stage", "intro")
    return stage if stage in LAB.stages else "intro"


def set_stage(st, stage):
    previous = current_stage(st)
    st.session_state["stage"] = stage
    try:
        save(st)
    except OSError as error:
        st.session_state["stage"] = previous
        st.error(str(error))
        return
    st.session_state["scroll_to_top"] = True
    st.rerun()


def scroll_to_top(st):
    """Scroll only on entry/navigation, never on a slider or Run rerender."""
    if not st.session_state.pop("scroll_to_top", False):
        return
    import uuid
    st.html("""<script>
    // Navigation token: """ + uuid.uuid4().hex + """
    (() => {
    const reset = () => {
      window.scrollTo(0, 0);
      document.querySelectorAll('[data-testid="stMain"], [data-testid="stAppViewContainer"], section.main')
        .forEach(el => el.scrollTo(0, 0));
    };
    requestAnimationFrame(reset);
    setTimeout(reset, 100);
    setTimeout(reset, 300);
    })();
    </script>""", unsafe_allow_javascript=True)


def render_progress(st):
    index = LAB.stages.index(current_stage(st))
    st.progress((index+1)/len(LAB.stages), text=f"{index+1}/{len(LAB.stages)}: {LABELS[current_stage(st)]}")


def footer(st):
    index = LAB.stages.index(current_stage(st))
    left, right = st.columns(2)
    if index and left.button("Back to " + LABELS[LAB.stages[index-1]], key="footer.back"):
        set_stage(st, LAB.stages[index-1])
    incomplete = current_stage(st) == "concepts" and not st.session_state["settings"].get("playground_progress", {}).get("finished")
    if incomplete:
        right.caption("Run each playground step and finish the final step to continue.")
    if current_stage(st) == "preflight":
        from lab.preflight import is_current
        incomplete = not is_current(st.session_state["settings"].get("preflight_report"))
        if incomplete:
            right.caption("Run preflight and resolve any failed checks before continuing.")
    if current_stage(st) == 'investigation':
        incomplete = st.session_state['settings'].get('investigation_part',0) < 2
        if incomplete: right.caption('Use the part navigation above to complete A, B and C in order.')
    if index < len(LAB.stages)-1 and right.button("Continue to " + LABELS[LAB.stages[index+1]], key="footer.next", type="primary", disabled=incomplete):
        set_stage(st, LAB.stages[index+1])
