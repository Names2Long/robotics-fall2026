import json
import os
import subprocess
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESS_RUN_ID = uuid.uuid4().hex


def current_run_id():
    return os.environ.get("COURSE_LAB_RUN_ID") or PROCESS_RUN_ID


def is_current(evidence):
    run_id = current_run_id()
    return bool(run_id and isinstance(evidence, dict) and evidence.get("ready") and evidence.get("run_id") == run_id)


def render(st):
    st.header("ROS 2 preflight")
    st.write("Before opening the simulator, check that this course container has ROS 2 Jazzy, the Week 6 packages, RViz, and the correct ROS domain. This checks the installed environment. Mission 1 checks live topics.")
    st.write("The guide and terminal share the same workspace. You do not need to upload a JSON file.")
    st.caption("The button below runs `bash scripts/course_preflight.sh` in this same container.")
    if st.button("Run preflight now", key="preflight.run"):
        try:
            result = subprocess.run(
                ["bash", str(ROOT / "scripts" / "course_preflight.sh")],
                cwd=ROOT, env={**os.environ, "COURSE_LAB_RUN_ID": current_run_id()},
                capture_output=True, text=True, timeout=90, check=False,
            )
            path = ROOT / "runtime" / "evidence" / "preflight.json"
            evidence = json.loads(path.read_text(encoding="utf-8"))
            if result.returncode:
                evidence["ready"] = False
            st.session_state["evidence"] = {**st.session_state["evidence"], "preflight": evidence}
            if result.returncode and not evidence.get("ready"):
                st.error("Preflight found one or more failed checks. Review the table below.")
                st.code(result.stdout + result.stderr)
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            st.error(f"Preflight could not finish: {error}")
    evidence = st.session_state["evidence"].get("preflight")
    if not is_current(evidence):
        st.info("Preflight has not passed in this lab launch. Run the check above before continuing. An older preflight file does not count.")
        if isinstance(evidence, dict) and evidence.get("run_id") == current_run_id():
            st.dataframe(evidence.get("checks", []), hide_index=True, width="stretch")
        return
    st.success("Environment ready for this lab launch.")
    st.caption("Checked at " + str(evidence.get("captured_at", "unknown time")) + ". Verify live /scan, /odom, TF, and /map in Mission 1.")
    st.dataframe(evidence.get("checks", []), hide_index=True, width="stretch")
