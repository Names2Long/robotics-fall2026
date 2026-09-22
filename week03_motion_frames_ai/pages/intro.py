from __future__ import annotations

from lab.navigation import set_stage


def render(st) -> None:
    st.title("Motion, Frames, and AI-Assisted ROS Development")
    st.write(
        "In this individual lab you will predict mobile-robot motion, interpret coordinates "
        "across ROS frames, and use an AI assistant while preserving and verifying its work."
    )
    st.markdown(
        "You will submit:\n"
        "- Predicted and observed robot poses\n"
        "- Robot, sensor, and hallway-camera frame evidence\n"
        "- Original AI prompts and output from the frame and motion missions\n"
        "- Problems found, modifications, tests, and final ROS code\n"
        "- Test conclusions, a short synthesis, and your personal reflection"
    )
    st.write("Begin with five short visual walkthroughs: velocity commands, wheel motion, coordinate "
             "frames, prediction and measurement, and inspection of AI-generated code. Try each example "
             "and mark it reviewed before continuing. Reuse your Docker environment from Lab 1.")
    student = dict(st.session_state.get("student", {}))
    student["name"] = st.text_input("Full name", value=student.get("name", ""))
    student["email"] = st.text_input("Hunter email", value=student.get("email", ""))
    # Keep existing assignment identities stable; new students use their email.
    if not student.get('course_id'):
        student['course_id']=student['email'].strip().lower()
    st.session_state["student"] = student
    st.write('Lab 1 introduced ROS messages and basic robot behavior. Here you will predict motion, interpret coordinate frames, and evaluate code with evidence. The five walkthroughs prepare you for three individual missions.')
    st.markdown('Use the shared Docker installation from Lab 1. Open the [lab guide](http://localhost:8501) and [virtual desktop](http://localhost:6080/vnc.html?autoconnect=1&resize=remote). ROS terminal commands run inside that desktop, not in Windows PowerShell.')
    st.info('If ROS is unavailable, labeled model/reference evidence lets you complete motion and frame reasoning. Mission 3 still requires working code and passing automated tests; any unfinished live verification is disclosed in your submission.')
    if st.button("Begin", type="primary", disabled=not student['name'].strip() or '@' not in student['email']):
        set_stage(st, "concepts")
