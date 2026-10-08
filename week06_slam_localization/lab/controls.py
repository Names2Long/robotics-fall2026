"""Write-once predictions. Later revisions are kept separately from the original."""
from lab.evidence import evidence_id
from lab.session import response, set_response
from lab.ui import text_response


def prediction(st, activity, context, prompt, *, min_chars=20):
    draft = text_response(st, activity + ".prediction_draft", prompt)
    signature = evidence_id(context)
    locks = dict(st.session_state.get("prediction_locks", {}))
    record = locks.get(activity)
    if record is None:
        if st.button("Save prediction before observing", key="predict." + activity, disabled=len(draft.strip()) < min_chars):
            record = {"context_signature": signature, "text": draft.strip()}
            locks[activity] = record
            st.session_state["prediction_locks"] = locks
            set_response(st, activity + ".original_prediction", record["text"])
    elif record.get("context_signature") != signature:
        st.warning("The experiment conditions changed after your original prediction. The original is preserved. Save a new prediction for this setup.")
        if st.button("Save prediction for changed conditions", key="repredict." + activity, disabled=len(draft.strip()) < min_chars):
            history = list(locks.get(activity + ".history", []))
            history.append(record)
            locks[activity + ".history"] = history
            record = {"context_signature": signature, "text": draft.strip()}
            locks[activity] = record
            st.session_state["prediction_locks"] = locks
    if record and record.get("context_signature") == signature:
        st.success("Prediction saved before the result. It remains in your submission even if you revise your explanation.")
        st.caption("Original prediction: " + record["text"])
        return record["text"]
    st.info("Save a prediction for the displayed conditions before recording this experiment.")
    return None
