from lab.autosave import _atomic, submission_root
from lab.completion import current_signature, mission_status, saved_matches
from lab.final_reflection import render_final_reflection, write_final_reflection
from lab.submissions import manifest_current, submission_zip, write_manifest
from lab.ui import text_response
from lab_config import LAB


def render(st):
    st.header("Final synthesis and submission")
    st.write("Bring motion evidence, LiDAR observations, and both saved maps together. Technical synthesis and personal reflection are separate pieces of writing.")
    st.code("motion estimate + LiDAR observations → occupancy-grid map")
    synthesis = text_response(
        st, "final.synthesis",
        "In 200–300 words, explain what the robot can and cannot know about the TurtleBot3 House from your two maps. Use evidence from both routes to discuss LiDAR coverage, motion-estimate error, possible map corrections on revisits, mapping time, and visible map limitations. Explain which map you would trust more for a later task and why.",
        height=220,
    )
    words = len(synthesis.split())
    st.caption(f"Technical synthesis: {words}/200–300 words")
    reflection_ready = render_final_reflection(st)
    status = mission_status(st)
    identity = all(str(st.session_state["student"].get(key, "")).strip() for key in ("name", "email"))
    checks = [(mission.replace("_", " ").title() + " current saved evidence", valid) for mission, valid in status.items()]
    checks += [
        ("Student name and email", identity),
        ("Technical synthesis contains 200–300 words", 200 <= words <= 300),
        ("Individual reflection contains 1–300 words", reflection_ready),
    ]
    st.subheader("Submission readiness")
    st.dataframe(
        [{"Requirement": label, "Status": "Ready" if valid else "Not yet"} for label, valid in checks],
        hide_index=True, width="stretch",
    )
    for mission in LAB.missions:
        if status[mission]:
            continue
        checked = st.session_state["checked_evidence_ids"].get(mission)
        signature = current_signature(st, mission)
        if checked is None:
            st.info(f"{mission.replace('_', ' ').title()}: complete its steps and save it.")
        elif checked != signature:
            st.info(f"{mission.replace('_', ' ').title()}: answers, predictions, or evidence changed. Return via Lab navigation and check/save it again.")
        elif not saved_matches(mission, signature):
            st.info(f"{mission.replace('_', ' ').title()}: a saved file is missing or changed. Return via Lab navigation and save the mission again.")
    if st.button("Prepare checked submission", type="primary", disabled=not all(valid for _, valid in checks)):
        try:
            write_final_reflection(st)
            _atomic(submission_root() / "final_synthesis.md", "# Final synthesis\n\n" + synthesis.strip() + "\n")
            path = write_manifest(st)
        except (OSError, ValueError) as error:
            st.error(f"Submission could not be prepared: {error}")
        else:
            st.success(f"Verified submission prepared at {path.parent}. Download a backup, then commit your own work.")
    if manifest_current(st):
        st.download_button(
            "Download Lab 6 submission ZIP backup",
            submission_zip(st), "lab06_submission.zip", "application/zip",
        )
        st.success("The current mission files, writing, identity, and file hashes match the manifest.")
    elif (submission_root() / "manifest.json").exists():
        st.warning("A previous export is stale. Resolve the checklist and prepare a new submission.")
    st.write("From the repository root, commit the complete folder to your personal fork and submit that commit's URL:")
    st.code(
        'git status\ngit add week06_slam_localization/student_submission\n'
        'git commit -m "Submit Lab 6"\ngit push origin main',
        language="bash",
    )
    st.caption("Check the commit's file list on GitHub. The ZIP is a backup, not an automatic upload.")
