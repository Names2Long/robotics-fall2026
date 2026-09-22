from __future__ import annotations
import base64
from io import BytesIO
import math
import uuid

from lab.evidence import evidence_id
from lab.motion_trials import modeled_trial, now, run_live
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_1 import evaluate, valid_run
from pages.concepts import visual
from simulation.kinematics import SEQUENCES, integrate_sequence

TITLES = {"straight":"Straight motion", "turn_then_drive":"Turn, stop, then drive", "arc":"Curved motion"}
DESCRIPTION = {
    "straight":"Drive at 0.15 m/s for 3 seconds, with no turning, then stop.",
    "turn_then_drive":"Rotate left at 0.50 rad/s for π seconds (about 3.14 s), stop, then drive at 0.15 m/s for 2 seconds and stop.",
    "arc":"Drive at 0.15 m/s while turning left at 0.40 rad/s for 4 seconds, then stop.",
}


def drawing_background():
    from PIL import Image, ImageDraw
    image=Image.new("RGB",(600,360),"white");draw=ImageDraw.Draw(image)
    for x in range(40,600,40): draw.line((x,0,x,360),fill="#dbe7ed",width=1)
    for y in range(20,360,40): draw.line((0,y,600,y),fill="#dbe7ed",width=1)
    origin=(160,260);draw.line((origin[0],origin[1],540,origin[1]),fill="#b33c36",width=3)
    draw.line((origin[0],origin[1],origin[0],35),fill="#2457bb",width=3)
    draw.polygon(((540,260),(525,253),(525,267)),fill="#b33c36")
    draw.polygon(((160,35),(153,50),(167,50)),fill="#2457bb")
    draw.text((545,246),"+x",fill="#b33c36");draw.text((170,30),"+y",fill="#2457bb")
    draw.ellipse((150,250,170,270),fill="#087f80");draw.text((125,278),"start",fill="#15354a")
    return image


def sketch_editor(st):
    st.write("Draw the predicted turn and forward segment. Include the turn direction and endpoint.")
    try:
        from streamlit_drawable_canvas import st_canvas
        from PIL import Image
        st.image(drawing_background(), caption="Reference grid: the robot starts at the origin facing +x", width=600)
        st.caption("Use the blank canvas below to sketch the turn, forward segment, and endpoint. The reference grid is not copied into your drawing.")
        mode=st.radio("Drawing tool",("freedraw","line"),format_func=lambda v:"Pen" if v=="freedraw" else "Straight line",horizontal=True)
        version=st.session_state.setdefault("m1.sketch_version",0)
        initial=st.session_state.get("m1.sketch_drawing")
        result=st_canvas(fill_color="rgba(8,127,128,0.15)",stroke_width=4,stroke_color="#087f80",
                         background_color="#ffffff",update_streamlit=True,height=360,width=600,
                         drawing_mode=mode,initial_drawing=initial,key=f"m1.sketch_canvas.{version}")
        left,middle,right=st.columns(3)
        with left:
            if st.button("Undo last stroke",key="m1.sketch_undo") and result.json_data:
                drawing=dict(result.json_data);drawing["objects"]=list(drawing.get("objects",[]))[:-1]
                st.session_state["m1.sketch_drawing"]=drawing;st.session_state["m1.sketch_version"]+=1;st.rerun()
        with middle:
            if st.button("Clear drawing",key="m1.sketch_clear"):
                st.session_state["m1.sketch_drawing"]={"version":"4.4.0","objects":[]}
                st.session_state["m1.sketch_version"]+=1;st.rerun()
        with right:
            if st.button("Save drawing",key="m1.sketch_save",disabled=result.image_data is None):
                image=Image.fromarray(result.image_data.astype("uint8"),"RGBA");buffer=BytesIO();image.save(buffer,format="PNG")
                set_response(st,"mission_1.sketch",{"mime":"image/png","data":base64.b64encode(buffer.getvalue()).decode("ascii"),"source":"canvas"})
                if result.json_data: st.session_state["m1.sketch_drawing"]=result.json_data
                st.rerun()
    except (ImportError, TypeError):
        st.warning("The drawing canvas is unavailable in this container. Use the image-upload fallback below.")
    with st.expander("Upload a sketch instead"):
        uploaded=st.file_uploader("Upload PNG or JPG, at most 3 MB",type=["png","jpg","jpeg"],key="m1.sketch_upload")
        if uploaded and uploaded.size<=3_000_000:
            if st.button("Save uploaded sketch"):
                set_response(st,"mission_1.sketch",{"mime":uploaded.type,"data":base64.b64encode(uploaded.getvalue()).decode("ascii"),"source":"upload"});st.rerun()
        elif uploaded: st.error("Choose an image smaller than 3 MB.")
    if response(st,"mission_1.sketch"):
        st.image(base64.b64decode(response(st,"mission_1.sketch")["data"]),caption="Saved prediction sketch",width=500)


def answer(st, key, label, **kwargs):
    # Restore from autosave only when creating the widget, avoiding competing defaults.
    widget = f"m1.{key}"
    if widget not in st.session_state:
        st.session_state[widget] = str(response(st, key, ""))
    value = st.text_area(label, key=widget, **kwargs)
    set_response(st, key, value)
    return value


def prediction_form(st, name, predictions):
    prior = predictions.get(name)
    if prior:
        st.success("Prediction saved. Run the trial below.")
        st.write(prior["description"])
        st.caption("Your original prediction is retained so you can explain what you learned.")
        return prior
    st.markdown("**Before running:** picture the path from (0, 0), facing +x. "
                "Here +x is initially forward and +y is initially left. Heading starts at 0 radians.")
    if name == "straight":
        st.latex(r"d=vt")
        st.write("Multiply speed by duration for distance. With no turning, consider whether heading changes.")
    elif name == "turn_then_drive":
        st.latex(r"\Delta\theta=\omega t")
        st.write("First calculate the turn. Then draw the forward segment along the new heading. "
                 "Include the start arrow, turn direction, and endpoint in a sketch.")
        sketch_editor(st)
    else:
        st.latex(r"\Delta\theta=\omega t,\qquad R=\frac{v}{\omega}")
        st.write("Predict left or right turning, describe the path shape, and estimate heading change. "
                 "An exact endpoint calculation is optional.")
    with st.form(f"prediction_form_{name}"):
        description = st.text_area("Describe your predicted path and final orientation", key=f"m1.description.{name}")
        a, b = st.columns(2)
        with a:
            heading = st.number_input("Predicted final heading (radians)", value=0., step=.1, key=f"m1.heading.{name}")
        with b:
            distance = st.number_input("Predicted traveled path length (m)", min_value=0., value=0., step=.01, key=f"m1.distance.{name}")
        if name != "arc":
            x = st.number_input("Predicted final x (m)", value=0., step=.01, key=f"m1.x.{name}")
            y = st.number_input("Predicted final y (m)", value=0., step=.01, key=f"m1.y.{name}")
        else:
            x = y = None
        submitted = st.form_submit_button("Save prediction", type="primary")
    if submitted:
        if not description.strip():
            st.warning("Describe the path you expect before saving.")
        elif name == "turn_then_drive" and not response(st,"mission_1.sketch"):
            st.warning("Add your sketch before saving this prediction.")
        else:
            prior = {"id":uuid.uuid4().hex,"saved_at":now(),"description":description,
                     "x":x,"y":y,"theta":heading,"path_length":distance}
            predictions[name] = prior
            set_response(st,"mission_1.predictions",predictions)
            st.rerun()
    return None


def show_result(st, name, result, prediction):
    observed = result["observed_pose"]
    ideal = integrate_sequence(SEQUENCES[name])
    model = result["source"] == "modeled"
    (st.warning if model else st.success)("Modeled evidence. Live motion and stopping were not verified." if model
                                          else "Live trial recorded. A final stop command and low odometry velocities were observed.")
    if model:
        st.caption(result["model_description"])
    st.caption("Coordinates below are relative to this trial's starting pose. Positive y is to the left of the initial heading.")
    rows = []
    for axis, label in (("x","Final x (m)"),("y","Final y (m)"),("theta","Heading (radians)")):
        factor = 1
        pred = prediction.get(axis)
        difference = None if pred is None else observed[axis]-pred
        if difference is not None and axis=="theta":
            difference = math.atan2(math.sin(difference),math.cos(difference))
        rows.append({"Quantity":label,"Your prediction":"optional" if pred is None else round(pred*factor,3),
                     "Ideal model":round(ideal[axis]*factor,3),"Modeled result" if model else "Odometry result":round(observed[axis]*factor,3),
                     "Result minus prediction":"n/a" if difference is None else round(difference*factor,3)})
    st.table(rows)
    st.caption("The ideal column applies the constant-velocity formulas. Your prediction is not replaced by that calculation.")
    if result.get("samples"):
        samples = result["samples"]
        path_length = sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(samples,samples[1:]))
        st.write(f"Predicted path length: {prediction['path_length']:.3f} m. "
                 f"{'Modeled' if model else 'Odometry-estimated'} path length: {path_length:.3f} m. "
                 f"Start-to-end distance: {math.hypot(observed['x'],observed['y']):.3f} m.")
        if st.button("Replay recorded path", key=f"replay.{name}"):
            st.session_state[f"replay.token.{name}"] = uuid.uuid4().hex
        # Recorded samples use a uniform replay speed; this is a path review, not live control.
        visual(st, mode="motion", samples=samples, v=0,w=0,duration=4,
               token=st.session_state.get(f"replay.token.{name}",result["trial_id"]),
               replay=True)
        st.caption("Replay of the recorded path at an illustrative speed; this does not command Gazebo.")
    with st.expander("Starting and ending pose in the measurement frame"):
        st.write("These are odom estimates for live runs, or model-frame values for backup runs. "
                 "The table above rotates and translates them into a common starting reference.")
        st.json({"source":result["source"],"start":result.get("start_pose"),"end":result.get("end_pose"),
                 "frame":result.get("measurement_frame","model")})
    return answer(st, f"mission_1.compare.{name}",
                  "Compare your prediction with the result. Cite one difference, suggest a cause, and state what evidence would help check that cause.")


def render(st):
    st.title("Mission 1: Predict and execute motion")
    st.write("Complete three trials. Save a prediction, run the robot or use the labeled backup model, "
             "then explain the result. A prediction can be wrong and still be useful evidence of your learning.")
    with st.expander("Prepare Gazebo and your reference frame", expanded=True):
        st.write("If the simulator is already running from preflight, keep that launch open. Otherwise start it with the commands below. "
                 "Do not run teleoperation or another motion node during these trials.")
        st.code("cd /workspace/week03_motion_frames_ai\nexport ROS_DOMAIN_ID=25\nbash scripts/launch_lab.sh", language="bash")
        st.write("Each live run requests the same starting location, then records a ROS pose estimate. "
                 "Predictions use (0, 0, 0 radians) relative to that starting pose, so they do not require "
                 "Gazebo's absolute coordinates. The next lab examines how odometry produces this estimate.")
    predictions = dict(response(st,"mission_1.predictions",{}))
    selected = dict(response(st,"mission_1.results",{}))
    ready_count = sum(valid_run(selected.get(n),predictions.get(n)) for n in SEQUENCES)
    st.progress(ready_count/3,text=f"{ready_count}/3 trial results collected")
    active=st.session_state.setdefault("mission_1.active_trial",next((n for n in SEQUENCES if not str(response(st,f"mission_1.compare.{n}","")).strip()),"arc"))
    names=list(SEQUENCES)
    for i,name in enumerate(SEQUENCES):
        previous = list(SEQUENCES)[:i]
        unlocked = all(valid_run(selected.get(n),predictions.get(n)) and str(response(st,f"mission_1.compare.{n}","")).strip() for n in previous)
        with st.expander(f"Trial {i+1}: {TITLES[name]}", expanded=unlocked and name==active):
            if not unlocked:
                st.info("Collect the preceding trial's result first.")
                continue
            st.write(DESCRIPTION[name])
            prediction = prediction_form(st,name,predictions)
            if not prediction:
                continue
            if st.button("Run live trial" if name not in selected else "Retry live trial", key=f"live.{name}",type="primary"):
                with st.spinner("Preparing, running, and collecting stop evidence. This can take up to about 70 seconds."):
                    try:
                        result,error = run_live(name,prediction["id"])
                    except OSError as failure:
                        result,error = None,f'The trial could not start: {failure}. Check storage permissions or use modeled evidence.'
                set_response(st,f"mission_1.error.{name}",error)
                if result:
                    history = list(response(st,"mission_1.attempts",[])); history.append(result)
                    set_response(st,"mission_1.attempts",history)
                    selected[name]=result; set_response(st,"mission_1.results",selected)
                st.rerun()
            error = response(st,f"mission_1.error.{name}","")
            if error:
                st.warning(error)
                st.write("For live recovery, stop the simulator launch with Ctrl+C and relaunch it. "
                         "Keep your saved prediction. You can also continue with the model below.")
            with st.expander("Use backup modeled evidence"):
                st.write("Use this if the simulator is unavailable or times out. It imposes 8% less translation "
                         "and 7% less rotation to practice comparing predictions and observations. These are "
                         "illustrative differences, not measured simulator errors. It does not establish live ROS execution.")
                if st.button("Use modeled trial",key=f"model.{name}",disabled=name in selected and selected[name].get("source")=="live"):
                    result=modeled_trial(name,prediction["id"])
                    selected[name]=result; set_response(st,"mission_1.results",selected)
                    history=list(response(st,"mission_1.attempts",[])); history.append(result)
                    set_response(st,"mission_1.attempts",history)
                    st.rerun()
            if name in selected:
                analysis=show_result(st,name,selected[name],prediction)
                if i<len(names)-1:
                    if st.button("Save analysis and continue",key=f"continue.{name}",disabled=not analysis.strip(),type="primary"):
                        st.session_state["mission_1.active_trial"]=names[i+1]
                        st.session_state["scroll_to_top_pending"]=True
                        st.rerun()
                elif analysis.strip():
                    st.success("All three trial analyses are saved. Complete the two synthesis questions below.")

    st.subheader("Compare the three trials")
    st.caption("Use the per-trial tables. For modeled trials, identify the imposed difference rather than attributing it to real sensor noise.")
    answer(st,"mission_1.trial_synthesis",
           "In one response, compare the three trials. Identify which path shapes and heading changes matched your expectations, cite the largest position or heading difference, propose a possible cause and evidence that could test it, and predict the straight-line distance at the same speed for twice the duration using d = vt.",height=180)
    st.subheader("Motion in a public hallway")
    st.write("Imagine one of these motions happening near a person. Consider predictability, passing distance, and time to react.")
    answer(st,"mission_1.hallway_analysis",
           "In one response, identify motion that could confuse or discomfort someone nearby, name a motion parameter you would change and its tradeoff, and propose one measurable criterion for acceptable motion around people with a way to evaluate it.",height=170)
    runs = list(selected.values())
    responses = st.session_state["responses"]
    check=evaluate(runs,responses)
    render_check(st,check)
    relevant={k:v for k,v in responses.items() if k.startswith("mission_1.") and not k.startswith("mission_1.error.")}
    current_id=evidence_id(relevant)
    if st.button("Check and save Mission 1",disabled=not check.passed,type="primary"):
        # Keep the image out of the prose export; save the actual image beside it.
        export=dict(responses); sketch=export.pop("mission_1.sketch",None)
        export["mission_1.sketch"]="See prediction_sketch image in this folder."
        target=save_mission("mission_1",{"evidence_id":current_id,"runs":runs,
            "predictions":predictions,"live_verification_pending":[n for n in SEQUENCES if selected[n]["source"]!="live"],
            "check":[r.__dict__ for r in check.requirements]},export)
        if sketch:
            suffix="png" if sketch["mime"]=="image/png" else "jpg"
            (target/f"prediction_sketch.{suffix}").write_bytes(base64.b64decode(sketch["data"]))
        complete_mission(st,"mission_1",current_id)
        st.rerun()
    if check.passed and st.session_state.get("checked_evidence_ids",{}).get("mission_1")==current_id:
        st.success("Mission 1 saved, including evidence sources and your explanations.")
        if st.button("Continue to Mission 2",type="primary"):
            set_stage(st,"mission_2")
