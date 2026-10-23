from dataclasses import asdict
import cv2
import pandas as pd
from lab.autosave import save
from lab.session import response, set_response
from perception.classical import Settings, process


def changed(st):
    try:
        save(st)
        st.session_state.pop("save_error",None)
    except OSError as error: st.session_state["save_error"] = str(error)


def text_response(st, key, label, height=120):
    widget = "field."+key
    if widget not in st.session_state: st.session_state[widget] = str(response(st, key))
    value = st.text_area(label, key=widget, height=height, on_change=changed, args=(st,))
    set_response(st, key, value)
    return value


def picture(st, image, caption):
    st.image(image, channels="BGR" if image.ndim == 3 else "RGB", caption=caption, width="stretch")


def settings_controls(st, prefix, vertical=False):
    saved = {**asdict(Settings()),**st.session_state["settings"].get(prefix,{})}
    values = {}
    a, b, c = (st, st, st) if vertical else st.columns(3)
    for column, channel, maximum, label in ((a, "h", 179, "Hue"), (b, "s", 255, "Saturation"), (c, "v", 255, "Value / brightness")):
        low, high = column.slider(label, 0, maximum, (saved[channel+"_low"], saved[channel+"_high"]), key=prefix+channel)
        values[channel+"_low"], values[channel+"_high"] = low, high
    a, b = (st, st) if vertical else st.columns(2)
    values["kernel"] = a.select_slider("Morphology kernel", (1, 3, 5, 7, 9), value=saved["kernel"], key=prefix+"kernel")
    values["min_area"] = b.slider("Minimum contour area (pixels²)", 1, 15000, int(saved["min_area"]), key=prefix+"area")
    values['min_circularity'] = st.slider('Minimum circularity',0.,1.,float(saved['min_circularity']),.05,key=prefix+'shape')
    with st.expander('Preprocessing parameters'):
        values['smoothing'] = st.selectbox('Smoothing',('none','Gaussian','median'),index=('none','Gaussian','median').index(saved['smoothing']),key=prefix+'smooth')
        values['blur_kernel'] = st.select_slider('Smoothing kernel',(1,3,5,7,9),value=saved['blur_kernel'],key=prefix+'blur')
        values['brightness'] = st.slider('Brightness adjustment',-80,80,int(saved['brightness']),key=prefix+'brightness')
        values['contrast'] = st.slider('Contrast multiplier',.5,2.,float(saved['contrast']),.1,key=prefix+'contrast')
    st.session_state["settings"][prefix] = values
    return Settings(**values)


def pipeline_views(st, image, settings, implementation=None, result=None):
    if result is None:
        result = process(image, settings, implementation)
    for group in (("Original BGR image", image,"Preprocessed image",result.get('preprocessed',image)),
                  ("Raw threshold mask", result["raw_mask"], "After morphology", result["mask"]),
                  ("Candidate contours", result["contours"], "Selected box and centers", result["annotated"])):
        columns = st.columns(len(group)//2)
        for index, column in enumerate(columns): picture(column, group[index*2+1], group[index*2])
    st.caption("White mask pixels pass the rule. Blue outlines show candidates. Green is the selected box. Red marks its box center. Yellow marks the contour centroid. Magenta marks the image center.")
    if result["candidates"]:
        st.caption('candidate is the number drawn on the contour image. area_px is enclosed area in square pixels. circularity compares the outline with a circle, where values near 1 are rounder. centroid is the image-coordinate balance point. eligible means the region passed the area and shape filters, not that it is a known mug.')
        st.dataframe(result["candidates"], hide_index=True)
        st.caption(f"Selected contour: {result['selected']}. Largest eligible area wins. A large region can be the wrong object.")
    else: st.info("No contours found. Inspect the mask before changing the selection rule.")
    return result


def metrics_view(st, result):
    st.markdown('**Did the detector report a cup when one was present?**')
    st.write('Each image has a known target-present or target-absent label. TP is a detection on a present image. FN is a missed present image. FP is a detection on an absent image. TN is an absent image correctly left without a detection. These counts do not yet test whether the box is on the right object.')
    st.dataframe([{k: v for k, v in result["metrics"].items() if k != "conditions"}], hide_index=True)
    st.caption('sample_count is the number of images. Precision = TP / (TP + FP). Recall = TP / (TP + FN). Accuracy is the fraction of correct present/absent decisions. False-positive rate = FP / (FP + TN). Values from 0 to 1 can be read as proportions. A blank value has no denominator. mean_latency_ms is average processing time per image in milliseconds, not robot response time.')
    st.markdown('**Which test condition caused these errors?**')
    st.write('A condition is a named image change, such as dim or blur. Each row below repeats the counts for only that condition. Compare FN for missed cups and FP for unwanted reports, not accuracy alone when the number of absent examples differs.')
    st.dataframe(result["conditions"], hide_index=True)
    if "localization" in result:
        st.write('A report on the wrong object can pass the presence check. Box matching also tests location. IoU is overlap area divided by the area covered by either the predicted or reference box. A match needs IoU at least 0.50. box_tp counts matched cups, box_fp counts unmatched predictions and box_fn counts cups without a match.')
        st.write("Box matching at IoU of at least 0.50",result["localization"])
        st.dataframe(result["box_conditions"],hide_index=True)
        st.caption("Box scores require overlap with the annotated cup, not merely a cup somewhere in the image. Extra unmatched boxes count as false positives. Annotation extents are approximate, especially under occlusion.")
    st.caption('There is no minimum accuracy required. Use these measures to explain what failed and why. A faster result is not better when it locates the wrong object.')


def mission_status(st, mission):
    from lab.completion import mission_ready
    ready, detail = mission_ready(st.session_state, mission)
    (st.success if ready else st.info)(detail)
