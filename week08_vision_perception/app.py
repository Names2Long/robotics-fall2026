import argparse
from lab.autosave import load_state, save, KEYS
from lab.session import initialize
from lab.navigation import LABELS, current_stage, render_progress, set_stage, footer, scroll_to_top
from lab.submissions import export, backup_bytes
from lab_config import LAB
from pages import concepts, final, intro, investigation, preflight
from pages import robot_missions

PAGES = {"intro": intro.render, "concepts": concepts.render, "preflight": preflight.render,
         "investigation": investigation.render, "final": final.render,
         "pillar_search": robot_missions.pillars,
         "line_following": robot_missions.line}


def run_streamlit_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title, page_icon="📷", layout="centered")
    initialize(st)
    if not st.session_state.get("loaded_autosave"):
        saved = load_state()
        for key in (*KEYS, "recovery_blocked", "recovery_note", "recovered"):
            if key in saved: st.session_state[key] = saved[key]
        st.session_state["loaded_autosave"] = True
        st.session_state["scroll_to_top"] = True
    if st.session_state.get("recovery_note"): st.warning(st.session_state["recovery_note"])
    if st.session_state.get("save_error"): st.error("Saving failed: "+st.session_state["save_error"]+". Keep this page open and copy your current answer before restarting.")
    with st.sidebar:
        st.subheader("Lab 7")
        for stage in LAB.stages:
            if st.button(LABELS[stage], key="nav."+stage, disabled=stage == current_stage(st)):
                set_stage(st, stage)
        if st.button("Save draft and prepare backup"):
            try:
                export(st)
                st.session_state['prepared_backup'] = backup_bytes()
                st.success("Draft saved")
            except (OSError, ValueError) as error: st.error(str(error))
        if st.session_state.get('prepared_backup') is not None:
            st.download_button("Download saved backup", st.session_state['prepared_backup'], "lab7-backup.zip", "application/zip")
        st.caption("Press Save draft and prepare backup to create a current ZIP. A prepared download is a snapshot from that button press, not later edits.")
    if st.session_state.get("recovery_blocked"): st.stop()
    render_progress(st)
    try:
        PAGES[current_stage(st)](st)
        footer(st)
        scroll_to_top(st)
        save(st)
        st.sidebar.caption("Answers and progress saved locally")
    except (OSError, ValueError) as error:
        st.error(f"Could not complete this operation: {error}. Your earlier saved work is retained.")


def run_smoke_test():
    from perception.experiments import run, validate
    for method in ("classical", "learned"):
        evidence = run(method)
        print(method, validate(evidence, method)["metrics"])
    print("Lab 7 detector investigation smoke test passed")


def main():
    parser = argparse.ArgumentParser(description=LAB.title)
    parser.add_argument("--smoke-test", action="store_true")
    # Streamlit and AppTest may supply their own process arguments.
    args, _ = parser.parse_known_args()
    if args.smoke_test: run_smoke_test()
    else:
        import streamlit as st
        # These page modules are render helpers, not standalone Streamlit apps.
        st.navigation([st.Page(run_streamlit_app, title=LAB.title)], position="hidden").run()


if __name__ == "__main__": main()
