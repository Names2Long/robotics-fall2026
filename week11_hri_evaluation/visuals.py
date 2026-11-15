"""Visible diagrams shared by the guided activities and live ROS trials."""
import html
import streamlit as st

PHASES = ("IDLE", "CLARIFY", "CONFIRM", "EXECUTING", "WAIT_READY", "COMPLETE")


def flow(current):
    parts = []
    for label in PHASES:
        color = "#145b8a" if label == current else "#334155"
        parts.append(f'<div style="padding:12px;border-radius:8px;background:{color};color:white">{label}</div>')
    st.markdown('<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">'
                + '<span style="color:#8195ab">→</span>'.join(parts) + '</div>', unsafe_allow_html=True)
    if current in ("CANCELLED", "RECOVERY"):
        st.warning("The task is stopped. Begin a new request to recover.")


def stations(state):
    positions = {0: "Person", 2: "Correction point", 3: "Red cup", 5: "Blue cup"}
    cards = []
    for index in range(6):
        robot = "🤖 Robot" if state["position"] == index else ""
        label = positions.get(index, "Travel")
        accent = "#fb7185" if index == 3 else "#60a5fa" if index == 5 else "#86efac" if index == 0 else "#cbd5e1"
        cards.append(f'<div style="flex:1;min-width:95px;border:3px solid {accent};border-radius:8px;'
                     f'padding:12px;text-align:center;background:#172334;color:white">'
                     f'<b>{label}</b><br>{index} m<br><span style="font-size:20px">{robot or "·"}</span></div>')
    st.markdown('<div style="display:flex;gap:8px;flex-wrap:wrap;margin:12px 0">' + ''.join(cards) + '</div>',
                unsafe_allow_html=True)
    st.caption("Teaching diagram. The six marked positions correspond to metres along the Gazebo room. The person is at 0 m, red at 3 m, and blue at 5 m.")


def room(pose, state):
    # Use HTML layout with explicit visible coordinates, avoiding SVG sanitation.
    x, y, yaw = pose
    left = max(2, min(94, (x + .5) / 6 * 100))
    top = max(15, min(82, 52 - y * 20))
    target = html.escape(state["target"] or "No selected cup")
    st.markdown(f'''<div style="position:relative;width:100%;height:220px;background:#e2e8f0;
border:2px solid #64748b;border-radius:12px;color:#102030;margin:12px 0">
<span style="position:absolute;left:4%;top:10%;color:#166534">Person · 0 m</span>
<span style="position:absolute;left:56%;top:78%;color:#b91c1c">Red cup · 3 m</span>
<span style="position:absolute;left:87%;top:78%;color:#1d4ed8">Blue cup · 5 m</span>
<span style="position:absolute;left:40%;top:12%">Checkpoint · 2 m</span>
<span style="position:absolute;left:{left:.1f}%;top:{top:.1f}%;font-size:28px;transform:translate(-50%,-50%) rotate({-yaw*57.2958:.1f}deg)">➤</span>
<span style="position:absolute;left:4%;bottom:8px">Robot arrow from /odom · Selected goal {target}</span>
</div>''', unsafe_allow_html=True)


def controller_editor(work, key):
    from handover import load_controller
    from lab.storage import atomic, planner_source
    path = planner_source()
    st.write("Edit the Python below, then select Save controller. Running a check uses the saved version.")
    disk = path.read_text(encoding="utf-8-sig")
    source_key = f"{key}-source"
    disk_key = f"{key}-saved"
    if st.session_state.get(disk_key) != disk:
        st.session_state[source_key] = disk
        st.session_state[disk_key] = disk
    active = bool(work.get("active"))
    if active:
        st.caption("Finish or archive the active robot trial before editing the controller.")
    with st.form(f"{key}-editor"):
        source = st.text_area("Your interaction controller", height=470, key=source_key, disabled=active)
        if st.form_submit_button("Save controller", disabled=active):
            try:
                load_controller(source)
                atomic(path, source.encode("utf-8"))
                st.session_state[disk_key] = source
            except (SyntaxError, ValueError, OSError) as error:
                st.error(f"Controller could not be saved. {error}")
            else:
                st.success("Controller saved. Run the checks below.")
    return path
