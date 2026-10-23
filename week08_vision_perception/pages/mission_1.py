from dataclasses import asdict
from perception.dataset import tuning_image, samples
from perception.classical import Settings, process
from perception.lesson import code_for
from perception.experiments import run, validate
from lab.ui import settings_controls, pipeline_views, metrics_view, text_response, mission_status, picture
from lab.submissions import store_run


def render(st):
    st.subheader("Part A: configure and test a classical detector")
    st.write("Your task is to configure a color rule that proposes the mug's image location. Run the supplied code, inspect its intermediate results and test how one fixed configuration handles changed images. The rule does not understand the word mug. It selects pixels and connected regions that match your parameters.")
    st.markdown("""1. **Practice:** adjust the detector's parameters and run it on the photograph below.
2. **Test:** lock one configuration and run it on the complete image collection.
3. **Explain:** inspect the saved outputs and answer the two questions at the end.

A detector is the sequence of operations that turns an image into a proposed target box. Here those operations are BGR-to-HSV conversion, thresholding, mask cleaning, contour extraction, and selection of the largest eligible contour. These are the same operations you ran in the playground. The code is supplied below, and your sliders set its parameters. There is no separate file you need to find.
""")
    st.subheader("1. Practice on this photograph")
    image = tuning_image()
    photo, explanation = st.columns([1, 1])
    picture(photo, image, "Practice scene: locate the mug, not the laptop or desk equipment")
    explanation.write("The target is the visible mug and handle. Its top is outside the photograph. The keyboard, trackpad and laptop are not targets. An assistive robot would need to distinguish these before selecting an object, then obtain depth and additional views before grasping.")
    explanation.write("Try hue 0 to 35, saturation 70 to 255, value 25 to 180, kernel 3 and minimum area 300 as an initial brown-surface rule. Inspect which mug and desk pixels pass. This is a starting experiment, not a promise of a correct box. The wood can pass the same rule. Change one bound at a time and observe why the selected contour changes.")
    explanation.write("Change one parameter, run the detector, and compare with your previous output. Circularity filters shape, while preprocessing changes the image before masking. Keep a useful contrasting example in mind for the second written answer. You are investigating a simple rule's limitations, so perfect accuracy is not required.")
    controls, program = st.columns([1, 1.4])
    with controls:
        st.markdown("**Choose the parameters**")
        settings = settings_controls(st, "classical", vertical=True)
        st.caption("Hue selects color families, saturation selects color intensity and value selects brightness. Minimum area and circularity reject candidate regions. The preprocessing expander controls smoothing, brightness and contrast. These settings are locked and saved with the batch. Return to the playground to revisit any operation.")
    with program:
        st.markdown("**Run the supplied detector code**")
        st.caption("Slider values appear in the code. The guide loads the photograph into image, then executes this code when you press Run. The batch test uses this same code for every image.")
        with st.container(height=360):
            st.code(code_for(settings), language="python", wrap_lines=True)
        if st.button("Run detector on practice photograph", type="primary"):
            st.session_state["classical_preview"] = {"settings": asdict(settings), "result": process(image, settings)}
    preview = st.session_state.get("classical_preview", {})
    current = preview.get("settings") == asdict(settings)
    if current:
        pipeline_views(st, image, settings, result=preview["result"])
        st.caption("Check whether white mask pixels belong to the cup. Use the contour numbers and area table to explain why the selected region won.")
    else:
        st.info("Run the detector to see the outputs for these settings. Changing a slider updates the code but does not run it.")
    st.subheader("2. Lock one configuration and test all images")
    st.write(f"After tuning, press the button below. It keeps your current parameters fixed and runs the detector on all {len(samples())} images. You do not adjust the rule separately for each image. The guide saves settings, masks, contours, boxes, predictions and metrics automatically.")
    st.write("The collection includes dim lighting, glare, smaller apparent size, partial occlusion, image rotation, clutter, blur and a constructed background change. Target-absent examples test false detections. Two independent cup photographs show different viewpoints and real backgrounds, but change several factors together. Image rotation alone is not a change in camera viewpoint, and apparent size is not a measured physical distance.")
    if st.button("Lock settings and evaluate all images", type="primary", disabled=not current):
        with st.spinner("Running the displayed detector code on all images"):
            store_run(st, "mission_1", run("classical", asdict(settings)))
    evidence = st.session_state["evidence"].get("mission_1")
    if evidence and evidence.get("schema_version") == 2:
        st.markdown("**Saved experiment**")
        st.write("Saved run settings", evidence["settings"])
        if evidence["settings"] != asdict(settings):
            st.info("The controls differ from this saved experiment. Run a new batch to replace it, or analyze the saved settings shown above.")
        try:
            results = validate(evidence, 'classical')
        except (ValueError, TypeError, KeyError) as error:
            st.info(str(error)+'. Earlier answers remain below. Run the practice detector and evaluate the current collection when you are ready to update the evidence.')
        else:
            metrics_view(st, results)
            st.write("An image ID is the short name in the selector below and in saved predictions.csv. For example, dim_1 means the first dim-lighting variant. A name ending in _absent is a no-cup control. Select normal_1 and dim_1 first, then inspect an absent example. These names let you identify exactly which output supports an answer.")
            items = {item["image_id"]: item for item in samples()}
            selected = st.selectbox("Inspect a test image from the saved run", list(items))
            st.caption(f"Image ID: {selected}. Condition: {items[selected]['condition']}. Cup present: {items[selected]['expected']}.")
            pipeline_views(st, items[selected]["image"], Settings(**evidence["settings"]), evidence.get("implementation"))
    st.subheader("3. Explain your results")
    st.write("Use the test-image selector and the mask/contour panels above. A failure is useful evidence when you explain its cause. You can use normal_1 and dim_1, or another pair where the result changes.")
    text_response(st, "mission_1.diagnosis", "Compare two images from the saved-run selector. Give their selector names, such as normal_1 and dim_1. For each, is the box on the mug? Use the mask, contour table and one relevant setting to explain why the detector selected or missed that region.")
    text_response(st, "mission_1.limitations", "During practice, which single parameter did you change? Describe what changed in the mask or selected box and why. What limitation remains for a different cup or background?")
    mission_status(st, "mission_1")
