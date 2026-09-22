from __future__ import annotations

import argparse
import os

from lab.autosave import restore, save
from lab.navigation import current_stage, render_progress, set_stage
from lab.session import initialize
from lab_config import LAB
from pages import concepts, final, intro, mission_1, mission_2, mission_3, preflight


PAGES = {
    "intro": intro.render,
    "concepts": concepts.render,
    "preflight": preflight.render,
    "mission_1": mission_1.render,
    "mission_2": mission_2.render,
    "mission_3": mission_3.render,
    "final": final.render,
}


def run_smoke_test() -> None:
    import tempfile
    from pathlib import Path
    from lab.ai_log import assigned_pattern
    from missions import mission_1 as m1, mission_2 as m2, mission_3 as m3
    from simulation.kinematics import SEQUENCES

    locked = "2026-08-31T00:00:00+00:00"
    from lab.motion_trials import modeled_trial
    responses = {
        "mission_1.predictions": {name: {"id": name, "saved_at": locked, "description": "My predicted path"} for name in SEQUENCES},
        "mission_1.sketch": {"data": "smoke-test placeholder"},
        **{f"mission_1.compare.{name}": "Comparison" for name in SEQUENCES},
        **{f"mission_1.{key}": "Explanation" for key in m1.REFLECTIONS},
    }
    runs = [modeled_trial(name, name) for name in SEQUENCES]
    assert m1.evaluate(runs, responses).passed
    from lab.frame_learning import reference_snapshot
    snapshot = reference_snapshot()
    responses.update({"mission_2.snapshot":snapshot,**{f"mission_2.{key}": "Explanation" for key in m2.REFLECTIONS}})
    with tempfile.TemporaryDirectory() as camera_directory:
        camera_source=Path(camera_directory)/'camera_transform.py';camera_source.write_text('# revised')
        camera_lock={'integrity_valid':True};camera_result={'file_present':True,'source_sha256':m2.current_hash(camera_source),
            'unit_tests_passed':True,'test_count':5,'source_differs_from_original':True,'live_passed':True}
        assert m2.evaluate(camera_result,camera_lock,responses,camera_source).passed
    pattern = assigned_pattern("test-student")
    lock = {"pattern": pattern, "locked_at": locked, "prompt_sha256": "a", "output_sha256": "b", "integrity_valid": True}
    ai_result = {"pattern": pattern, "unit_tests_passed": True, "integration_passed": True, "commands_bounded": True, "final_stop_verified": True, "source_differs_from_original": True, "test_count": 7}
    responses.update({f"mission_3.{key}": "A substantive response explaining evidence and responsibility." * 2 for key in m3.REFLECTIONS})
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for relative in ("week03_pattern/pattern.py", "week03_pattern/pattern_node.py", "test/test_student_pattern.py"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# source\n" + "value = 1\n" * 30, encoding="utf-8")
        lock['source_sha256']='original'
        ai_result.update(source_sha256=m3.current_hash(root),shape_check_passed=True,model_stop_passed=True,test_count=9,
                         implementation_present=True,student_test_file_present=True,student_test_count=2)
        assert m3.evaluate(ai_result, lock, responses, root).passed
    print("Week 3 lab smoke test passed.")


def run_streamlit_app() -> None:
    import streamlit as st

    st.set_page_config(page_title=LAB.title, page_icon="🧭", layout="wide")
    initialize(st)
    restore(st)
    if st.session_state.get('recovery_note'):
        st.warning(st.session_state['recovery_note'])
    with st.sidebar.expander("Instructor controls"):
        expected = os.environ.get(LAB.instructor_password_env, "frames-master")
        password = st.text_input("Password", type="password")
        if password == expected:
            destination = st.selectbox("Jump to", LAB.stages)
            if st.button("Go"):
                set_stage(st, destination)
        else:
            st.caption("Locked")
    render_progress(st)
    try:
        PAGES[current_stage(st)](st)
    finally:
        # Reruns triggered by navigation must still persist the newly selected stage.
        try:
            if st.session_state.get('recovery_note','').startswith('Saved progress could not be read'):
                st.sidebar.error('Autosave paused to preserve unreadable files. Back up your current text.')
            else:
                save(st)
                st.sidebar.success('Progress saved' if st.session_state.pop('_explicit_save',False) else 'Autosaved')
        except OSError as error:
            st.sidebar.error(f'Progress could not be saved: {error}. Copy your text before closing the guide.')


def main() -> None:
    parser = argparse.ArgumentParser(description=LAB.title)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    run_smoke_test() if args.smoke_test else run_streamlit_app()


if __name__ == "__main__":
    main()
