from __future__ import annotations
import argparse
from lab.autosave import load_state, save
from lab.completion import refresh_completion
from lab.navigation import LABELS, current_stage, render_progress, set_stage
from lab.session import initialize, sync_widgets
from lab_config import LAB
from pages import final, intro, mission_1, mission_2, preflight, tutorials
PAGES = {
    "intro": intro.render, "tutorial_1": tutorials.render, "tutorial_2": tutorials.render,
    "preflight": preflight.render, "tutorial_3": tutorials.render,
    "mission_1": mission_1.render, "mission_2": mission_2.render,
    "final": final.render,
}

def run_smoke_test():
    from analysis.map_metrics import analyze_pixels, quality_score
    from missions import mission_1 as m1, mission_2 as m2
    pixels = [205] * 100 + [254] * 750 + [0] * 150; metrics = analyze_pixels(40, 25, 255, pixels, .05); metrics["known_fraction"] = .6
    first = {"strategy": "perimeter_then_interior", "duration_minutes": 7, "metrics": metrics, "quality_score": max(50, quality_score(metrics))}; second = {"strategy": "room_by_room", "duration_minutes": 5, "metrics": {**metrics, "known_fraction": .65}, "quality_score": 70}
    responses = {**{f"mission_1.{key}": "A detailed explanation of poorly observed areas and what happened when the robot returned to a known wall. " * 2 for key in m1.REFLECTIONS}, **{f"mission_2.{key}": "A detailed comparison of the two routes using recorded time, map measurements, and visible structures. " * 2 for key in m2.REFLECTIONS}}
    responses.update({"mission_1.route.original_prediction": "I will map the perimeter, revisit the starting wall, and watch for unobserved interior space.",
                      "mission_2.strategy.original_prediction": "My second route may map the accessible area faster while preserving recognizable wall outlines."})
    assert m1.evaluate(first, responses, True, True).passed; assert m2.evaluate(first, second, responses).passed
    print("Week 6 lab smoke test passed.")

def access_map(st, status):
    student = st.session_state["student"]
    identity = all(str(student.get(key, "")).strip() for key in ("name", "email"))
    reviewed = st.session_state["tutorial_complete"]
    preflight_ready = preflight.is_current(st.session_state["evidence"].get("preflight"))
    return {
        "intro": True, "tutorial_1": identity, "tutorial_2": reviewed.get("tutorial_1", False),
        "preflight": reviewed.get("tutorial_2", False), "tutorial_3": preflight_ready,
        "mission_1": reviewed.get("tutorial_3", False), "mission_2": status["mission_1"],
        "final": status["mission_2"],
    }


def run_streamlit_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title, page_icon="🗺️", layout="wide"); initialize(st)
    if not st.session_state.get("loaded_autosave"):
        saved = load_state()
        if saved.get("recovery_blocked"):
            st.error(saved["recovery_note"]); st.stop()
        for key in ("stage", "student", "responses", "completed_missions", "checked_evidence_ids",
                    "evidence", "tutorial_complete", "prediction_locks", "visited_stages",
                    "recovered_from_backup"):
            if key in saved: st.session_state[key] = saved[key]
        if saved.get("recovery_note"): st.session_state["recovery_note"] = saved["recovery_note"]
        st.session_state["loaded_autosave"] = True
    if st.session_state.get("recovery_note"): st.warning(st.session_state["recovery_note"])
    status = refresh_completion(st)
    render_progress(st)
    access = access_map(st, status)
    with st.sidebar.expander("Lab navigation", expanded=True):
        for stage in LAB.stages:
            revisiting = stage in st.session_state.get("visited_stages", [])
            if st.button(LABELS[stage], key=f"nav.{stage}", disabled=not (access[stage] or revisiting) or stage == current_stage(st), width="stretch"): set_stage(st, stage)
    stage = current_stage(st)
    PAGES[stage](st)
    sync_widgets(st)
    status = refresh_completion(st)
    access = access_map(st, status)
    index = LAB.stages.index(stage)
    st.divider()
    back_column, next_column = st.columns(2)
    with back_column:
        if index and st.button(f"← Back to {LABELS[LAB.stages[index - 1]]}", key="page.back", width="stretch"):
            set_stage(st, LAB.stages[index - 1])
    with next_column:
        if index + 1 < len(LAB.stages):
            next_stage = LAB.stages[index + 1]
            can_advance = stage.startswith("tutorial_") or access[next_stage]
            if st.button(f"Next: {LABELS[next_stage]} →", key="page.next", type="primary", disabled=not can_advance, width="stretch"):
                if stage.startswith("tutorial_"):
                    st.session_state["tutorial_complete"] = {**st.session_state["tutorial_complete"], stage: True}
                set_stage(st, next_stage)
    try: save(st); st.sidebar.caption("Progress auto-saved locally")
    except OSError as error: st.sidebar.error(f"Autosave failed: {error}")

def main():
    parser = argparse.ArgumentParser(description=LAB.title); parser.add_argument("--smoke-test", action="store_true"); args = parser.parse_args(); run_smoke_test() if args.smoke_test else run_streamlit_app()
if __name__ == "__main__": main()
