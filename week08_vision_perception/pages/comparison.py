"""A focused comparison first, with explicitly explained optional metric details."""
from copy import deepcopy
import cv2
import pandas as pd
from perception.dataset import samples, CONDITIONS
from perception.classical import Settings, process
from perception.learned import annotate, suppress_duplicates
from perception.experiments import validate, signature
from evaluation.metrics import iou, mask_metrics
from perception.visual_experiments import decode
from perception.representations import mask_overlay
from lab.ui import picture, text_response, mission_status
from lab.submissions import store_run

CONDITION_HELP = {
    'normal': 'baseline scene with a small horizontal translation',
    'dim': 'reduced image brightness', 'glare': 'added bright patch',
    'far': 'smaller apparent size, not measured physical distance',
    'occluded': 'part of the mug covered', 'rotated': 'image rotated, not a new camera viewpoint',
    'cluttered': 'extra bright shapes', 'distractor': 'bright shapes without a mug',
    'blur': 'Gaussian image blur', 'background': 'constructed replacement background',
    'independent': 'different real cup photographs, with several factors changed together'}


def preview_for(evidence, controls):
    preview = deepcopy(evidence)
    preview.update(selected_threshold=controls['detection'], nms_iou=controls['nms'],
                   classification_threshold=controls['classification'], segmentation_threshold=controls['segmentation'])
    for row in preview['rows']:
        row['detections'] = suppress_duplicates(row['raw_detections'], controls['nms'])
        best = row['detections'][0] if row['detections'] else {}
        row.update(detected=bool(best), confidence=best.get('confidence', 0.), bbox=best.get('bbox'))
        row['selected_iou'] = iou(row['bbox'], row['reference_box'])
    return preview


def paired_image(st, item, classical, learned):
    result = process(item['image'], Settings(**classical['settings']), classical.get('implementation'))
    row = next(r for r in learned['rows'] if r['image_id'] == item['image_id'])
    left = result['annotated'].copy()
    right = annotate(item['image'], row['detections'], learned['selected_threshold'])
    if item['reference_box']:
        x, y, w, h = map(int, item['reference_box'])
        for image in (left, right): cv2.rectangle(image, (x,y), (x+w,y+h), (255,255,0), 1)
    a, b = st.columns(2)
    picture(a, left, 'Classical, saved Part A settings')
    picture(b, right, 'Learned, current acceptance threshold')
    st.caption('Cyan is the same supplied reference on both images. Green is the method\'s prediction. An absent scene has no reference. Compare whether a box is on the mug, not merely whether any box exists.')


def render(st, evidence, classical):
    st.write('Decide which cup detector you would investigate further for the desk-assistance task. Compare the same conditions, then check one example in detail. You do not need to discuss every graph. The primary table and paired images below supply the evidence for your answers.')
    if not classical:
        st.info('Run and save the fixed classical configuration in Part A first.')
        return
    try:
        other = validate(classical, 'classical')
    except (ValueError, TypeError, KeyError) as error:
        st.info(str(error)+'. Revisit Part A. Your writing remains saved.')
        return
    controls = st.session_state['settings'].setdefault('learned_views', {
        'step': 0, 'classification': evidence.get('classification_threshold', .1),
        'segmentation': evidence.get('segmentation_threshold', .5),
        'detection': evidence['selected_threshold'], 'nms': evidence.get('nms_iou', .45)})
    st.markdown('### 1. Choose the conditions and threshold')
    st.write('A condition is a named change to the image. Start with normal, dim and occluded. These test the baseline, reduced brightness and partial covering. Keep the classical settings fixed. Change only the learned acceptance threshold to see its effect.')
    conditions = st.multiselect('Conditions to compare', CONDITIONS, default=['normal','dim','occluded'], key='comparison.conditions')
    for condition in conditions: st.caption(condition+': '+CONDITION_HELP[condition])
    controls['detection'] = st.slider('Comparison detection threshold', .05, .9, float(controls['detection']), .05, key='comparison.threshold')
    preview = preview_for(evidence, controls)
    results = validate(preview, 'learned')
    st.markdown('### 2. Read the paired condition results')
    st.write('Each condition has a row for each detector. Correct boxes overlap the supplied mug box by at least 0.50 IoU. A false box is an unmatched prediction, including a box on the wrong object. A missed mug has no matching box. One image can therefore contribute both a false box and a miss. Smaller error counts are better on the same images.')
    rows = []
    for condition in conditions:
        for method, scored, source in (('Classical', other, classical), ('Learned', results, preview)):
            boxes = next(r for r in scored['box_conditions'] if r['condition'] == condition)
            presence = next(r for r in scored['conditions'] if r['condition'] == condition)
            rows.append({'Condition': condition, 'Detector': method, 'Images': presence['sample_count'],
                         'Correct boxes': boxes['box_tp'], 'False boxes': boxes['box_fp'], 'Missed mugs': boxes['box_fn'],
                         'Box precision': boxes['box_precision'], 'Box recall': boxes['box_recall'],
                         'Processing ms/image': presence['mean_latency_ms']})
    st.dataframe(rows, hide_index=True, width='stretch')
    st.caption('Precision is correct boxes / all accepted boxes. Recall is correct boxes / reference mugs. A blank ratio has no denominator. Processing time was measured during the original computation, excludes model loading and display, and is reused in previews. It is not camera-to-action delay or a safety measure.')
    st.markdown('### 3. Compare the same image side by side')
    items = {r['image_id']: r for r in samples()}
    candidates = [key for key, item in items.items() if item['condition'] in conditions]
    if candidates:
        chosen = st.selectbox('Comparison image ID', candidates, key='comparison.image')
        st.write(f"{chosen}: condition {items[chosen]['condition']}, mug present = {items[chosen]['expected']}.")
        paired_image(st, items[chosen], classical, preview)
    else:
        st.info('Select at least one condition to inspect its images.')
    st.markdown('### 4. Inspect one foreground-mask example')
    st.write('Use normal_1 as the common example. The foreground model has no cup label, so a detailed mask can include desk equipment. Green pixels below are accepted foreground. Compare with the supplied visible-mug silhouette. You may use this specific example in your recommendation.')
    focus = items['normal_1']
    visual = next(r for r in evidence['representations']['rows'] if r['image_id'] == 'normal_1')
    mask = decode(visual['saliency_png']) >= controls['segmentation']
    a, b = st.columns(2)
    picture(a, mask_overlay(focus['image'], mask), 'normal_1: predicted foreground')
    picture(b, focus['reference_mask'].astype('uint8')*255, 'normal_1: reference visible-mug mask')
    scores = mask_metrics(mask, focus['reference_mask'])
    st.table([scores])
    st.caption('mask_iou is shared foreground / pixels in either mask. dice is twice shared foreground / the two foreground counts added together. Both range from 0 to 1, with 1 meaning identical masks. extra_pixels mark unwanted foreground and missed_pixels mark omitted mug pixels. These scores test region agreement, not object identity.')
    with st.expander('Explore threshold tradeoffs and the precision-recall curve'):
        st.write('Read one sweep row at a time. It shows the learned detector at that confidence threshold on the same collection. box_precision and box_recall use correctly located boxes. A higher threshold can remove false boxes and also lose real mugs. Unchanged counts mean no proposal crossed that threshold.')
        sweep = pd.DataFrame(results['sweep'])[['threshold','box_tp','box_fp','box_fn','box_precision','box_recall']]
        st.dataframe(sweep, hide_index=True)
        st.line_chart(sweep.set_index('threshold')[['box_precision','box_recall']], height=210)
        st.caption('Horizontal axis: confidence threshold. Vertical axis: proportion. Look for the cost in missed mugs when rejecting more boxes.')
        pr = results['detection_pr']
        if pr['points']:
            st.line_chart(pd.DataFrame(pr['points']), x='recall', y='precision', height=210)
        st.metric('Cup AP50', pr['ap50'])
        st.write('This second graph has recall on the horizontal axis and precision on the vertical axis. Ranked predictions are matched at IoU 0.50. AP50 summarizes the precision envelope across recall, penalizing false boxes and missed mugs. It uses all saved scores, so changing just the acceptance threshold does not change AP50. It is one-class AP50, not a multi-class or multi-IoU mAP benchmark.')
    with st.expander('Review classification and segmentation details'):
        st.write('The classification matrix asks whether a whole-image score predicts cup presence. Rows show reality and columns show the predicted decision. It is not a box-location test. TP, FP, FN and TN count correct-present, false-present, missed-present and correct-absent decisions.')
        from pages.learned_lessons import confusion
        confusion(st, results['classification'])
        st.table([{key:results['classification'][key] for key in ('accuracy','precision','recall','false_positive_rate')}])
        st.caption('Accuracy is the fraction of correct presence decisions. Precision is the fraction of accepted presence decisions that were correct. Recall is the fraction of present images found. False-positive rate is the fraction of absent images falsely reported present. Class balance can make accuracy look high even when cups are missed.')
        segmentation = pd.DataFrame(results['segmentation'])
        st.write('Each mask row compares one image with its annotation. Look for low IoU or Dice and then inspect that scene in Part B. Independent photos have no mask annotations and are excluded. Empty target-absent masks can score 1, so do not mix them into a target-present average.')
        st.dataframe(segmentation, hide_index=True)
        st.table([segmentation[segmentation.target_present][['mask_iou','dice']].mean().to_dict()])
        st.caption('The small table is the mean over annotated target-present images only. References are approximate visible silhouettes, not hidden geometry.')
    st.markdown('### 5. Save and explain your recommendation')
    preferred = st.selectbox('Detector recommended for further testing', ['classical','learned'], index=['classical','learned'].index(evidence.get('preferred_method','learned')))
    if st.button('Save detector comparison', type='primary'):
        preview['comparison_run'] = signature(classical)
        preview['preferred_method'] = preferred
        preview['comparison_conditions'] = list(conditions)
        if len(conditions) < 3:
            st.info('Select at least three conditions for your saved comparison.')
        else:
            store_run(st, 'mission_2', preview)
            st.success('Comparison, thresholds and detector recommendation saved.')
    st.caption('Threshold changes are previews until saved. If you rerun Part A, review and save this comparison again. No minimum accuracy is required.')
    text_response(st, 'mission_2.comparison', 'Use the paired condition table to compare normal, dim and occluded, or three conditions you selected. For each, give both detectors\' correct-box, false-box and missed-mug counts. Which differences matter for locating the mug? Use one paired image ID to explain a difference. If the counts are identical, explain that finding rather than inventing a difference.')
    text_response(st, 'mission_2.choice', 'Which detector and acceptance settings do you recommend for further testing, based on your condition table and processing times? Then use the normal_1 foreground example above: report its mask IoU or Dice and explain why a detailed foreground mask does not by itself identify the requested mug. State one important limit of this small image test.')
    mission_status(st, 'mission_2')
