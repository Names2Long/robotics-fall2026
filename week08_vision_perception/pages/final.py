from lab.ui import text_response
from lab.completion import readiness
from lab.submissions import export, backup_bytes
from lab.navigation import set_stage


def render(st):
    st.header("Bring the evidence together")
    from pages.guidance import final
    final(st)
    st.subheader("Technical synthesis")
    text_response(st, "final.synthesis", "What did the three missions teach you about turning visual evidence into reliable robot behavior? Connect your classical and learned detector comparison, pillar centering, and line-following experiments using specific saved results. Explain how a perception or control choice affected the outcome and what limitations remain.", 180)
    from lab.final_reflection import render
    render(st)
    st.subheader("Submission readiness")
    checks = readiness(st.session_state)
    st.dataframe(checks, hide_index=True)
    if st.button("Review identity"): set_stage(st,"intro")
    if st.button('Review detector investigation'): set_stage(st, 'investigation')
    if st.button("Save draft submission"):
        export(st)
        st.session_state['prepared_backup'] = backup_bytes()
        st.success("Draft saved with current answers and evidence")
    if st.button("Finalize verified submission", type="primary", disabled=not all(r["ready"] for r in checks)):
        root = export(st, final=True)
        st.session_state['prepared_backup'] = backup_bytes()
        st.success(f"Complete submission saved at {root}")
    if st.session_state.get('prepared_backup') is not None:
        st.download_button("Download prepared submission backup", st.session_state['prepared_backup'], "lab7-submission.zip", "application/zip")
    st.caption('Save a draft or finalize to prepare an updated ZIP. The prepared ZIP does not include later edits until you save again.')
    st.markdown("Inspect your saved answers and evidence, then commit and push your own `week08_vision_perception/student_submission` folder. Submit the commit link. A ZIP download does not push to GitHub. If finalization is blocked, keep the draft and send the readiness message to your instructor.")
