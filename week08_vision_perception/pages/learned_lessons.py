"""Short, sequential learned-representation activities inside Mission 2."""
from copy import deepcopy
import cv2
import numpy as np
import pandas as pd
from perception.dataset import samples
from perception.classical import Settings,process
from perception.learned import annotate,suppress_duplicates
from perception.representations import mask_overlay
from perception.visual_experiments import decode,classification_results,segmentation_results
from evaluation.metrics import iou,mask_metrics,detection_pr
from lab.ui import picture

PARTS = ('Classification: what is in this scene?', 'Detection: where is the cup?',
         'Segmentation: which pixels belong?', 'Compare the representations')


def confusion(st, metrics):
    st.table(pd.DataFrame([[metrics['tn'],metrics['fp']],[metrics['fn'],metrics['tp']]],
                         index=['Actual cup absent','Actual cup present'],columns=['Predicted absent','Predicted present']))


def render(st, evidence, classical):
    controls = st.session_state['settings'].setdefault('learned_views',{
        'step':0,'classification':evidence.get('classification_threshold',.1),
        'segmentation':evidence.get('segmentation_threshold',.5),'detection':evidence['selected_threshold'],
        'nms':evidence.get('nms_iou',.45)})
    step = min(max(int(controls['step']),0),len(PARTS)-1)
    st.progress((step+1)/len(PARTS),text=f'Guided activity {step+1}/{len(PARTS)}')
    st.subheader(PARTS[step])
    items = {item['image_id']:item for item in samples()}
    chosen = st.selectbox('Shared scene to inspect',list(items),key='learned.scene')
    st.caption('A scene is one test image. Its ID, such as dim_1, identifies the exact same pixels for every method. Switching scenes uses saved predictions, not new model inference.')
    item = items[chosen]
    image = item['image']
    visual = next(row for row in evidence['representations']['rows'] if row['image_id']==chosen)
    if step == 0:
        st.write('Classification asks what kind of content an image contains. A classifier assigns scores to labels for the whole scene. MobileNet V1 learned from 1000 ImageNet categories before this lab. The mug, laptop and keyboard compete for one whole-image description. The top label does not tell the robot where any object is.')
        st.write('Inspect the top five labels on normal_1, then a distractor and an independent image. The binary evaluation below defines a cup-presence rule by adding scores for cup and coffee mug. This explicit mapping is imperfect. A high score for a keyboard or any other label is not counted as cup support.')
        st.caption('Inference resizes the full scene to 224 × 224 RGB pixels and applies the pretrained channel normalization. The weights stay fixed. Softmax converts the 1000 logits into relative scores summing to 1.')
        a,b = st.columns(2)
        picture(a,image,'Same scene used by every method')
        b.dataframe(visual['top5'],hide_index=True)
        b.metric('Cup + coffee mug score',f"{visual['cup_score']:.4f}")
        controls['classification'] = st.slider('Classification cup-score threshold',.001,.9,float(controls['classification']),.001)
        st.caption('The threshold converts relative class scores into a binary decision. Scores are not calibrated probabilities of cup presence.')
        metrics = classification_results(evidence['representations']['rows'],controls['classification'])
        confusion(st,metrics)
        st.table([{k:metrics[k] for k in ('accuracy','precision','recall','false_positive_rate')}])
        st.write('Accuracy = (TP + TN) / all images. Precision = TP / (TP + FP). Recall = TP / (TP + FN). Rows of the confusion matrix show reality and columns show the prediction. A blank metric has a zero denominator.')
        prevalence = st.slider('Hypothetical fraction of scenes containing a cup',.05,.95,.2,.05)
        tpr,fpr = metrics['recall'] or 0.,metrics['false_positive_rate'] or 0.
        st.table([{'Rule':'This classifier at observed TPR/FPR','Expected accuracy':prevalence*tpr+(1-prevalence)*(1-fpr)},
                  {'Rule':'Always predict no cup','Expected accuracy':1-prevalence}])
        st.caption('This class-balance demonstration reweights the observed rates. It does not add test data. When cups are rare, always predicting absence can have high accuracy while recall is zero.')
    elif step == 1:
        st.write('Detection asks both what an object might be and where it appears. A label is its proposed category. A box is a rectangle in image coordinates, not a physical position. A score expresses model support for that proposal, not proof. YOLOX supplies cup candidates. The acceptance threshold rejects weak candidates. Non-maximum suppression, or NMS, removes overlapping proposals that may describe the same object.')
        st.caption('The detector pads a resized image to 416 × 416, runs frozen inference and maps boxes back to the original coordinates. NMS compares overlap between predicted boxes. Scoring compares predictions with reference boxes, which is a different comparison.')
        controls['detection'] = st.slider('Acceptance threshold',.05,.9,float(controls['detection']),.05)
        controls['nms'] = st.slider('NMS overlap threshold',.1,.9,float(controls['nms']),.05)
        row = next(row for row in evidence['rows'] if row['image_id']==chosen)
        raw = row['raw_detections']
        kept = suppress_duplicates(raw,controls['nms'])
        a,b = st.columns(2)
        picture(a,annotate(image,raw,controls['detection']),'Before NMS')
        picture(b,annotate(image,kept,controls['detection']),'After NMS')
        st.table([{'Accepted before NMS':sum(r['confidence']>=controls['detection'] for r in raw),
                   'Accepted after NMS':sum(r['confidence']>=controls['detection'] for r in kept)}])
        st.caption('The next table lists retained proposals. label is the predicted category, confidence is its model score and bbox is [left x, top y, width, height] in source-image pixels. Some listed proposals are below your acceptance threshold and therefore are not drawn as accepted detections.')
        st.dataframe(kept[:15],hide_index=True)
        st.info('Lower the NMS overlap threshold to suppress more overlapping proposals. It can also suppress a box for a nearby real object. No change means this image has no proposals crossing that setting. Our scored collection has at most one reference cup per image.')
        st.markdown('**Measure overlap before interpreting a correct box**')
        offset = st.slider('Move a demonstration box horizontally (pixels)',0,120,30)
        reference = [30,25,80,65]
        predicted = [30+offset,25,80,65]
        canvas = np.full((120,240,3),245,np.uint8)
        for box,color in ((reference,(220,150,0)),(predicted,(0,150,20))):
            x,y,w,h = box
            cv2.rectangle(canvas,(x,y),(x+w,y+h),color,2)
        picture(st,canvas,'Blue reference and green prediction. Move the box to change overlap.')
        st.metric('Intersection over Union',f'{iou(predicted,reference):.3f}')
        st.write('IoU is intersection area divided by union area. Identical boxes score 1 and non-overlapping boxes score 0. Box scoring in this lab requires IoU at least 0.50. A box on the keyboard can trigger image-presence scoring when a mug is also present, but fail localization.')
    elif step == 2:
        st.write('Segmentation marks image regions at pixel level rather than enclosing them in a rectangle. This U²-Net model marks visually prominent foreground. Class-agnostic means it does not attach object-category names. It may mark the laptop or keyboard along with the mug. A detailed mask therefore does not prove that it found the requested object.')
        st.caption('The model processes 320 × 320 RGB pixels. Its foreground scores are normalized within each image and resized back to the scene. They are not calibrated probabilities of cup identity.')
        st.write('Semantic segmentation assigns a class to each pixel. Instance segmentation additionally distinguishes separate objects of the same class. This model supplies a class-agnostic foreground mask, so it provides neither semantic cup labels nor separate cup identities.')
        st.table([{'Representation':'Semantic','Two cups':'Both regions carry the cup class'},
                  {'Representation':'Instance','Two cups':'Cup 1 and cup 2 have separate region IDs'},
                  {'Representation':'This foreground model','Two cups':'Prominent regions may be joined and have no class or instance ID'}])
        with st.expander('See the difference on a two-cup schematic'):
            from perception.dataset import source_mask
            shape = cv2.resize(source_mask().astype('uint8'),(180,120),interpolation=cv2.INTER_NEAREST).astype(bool)
            semantic = np.full((140,400,3),40,np.uint8)
            instance = semantic.copy()
            for x,color in ((10,(40,190,60)),(210,(30,140,240))):
                semantic[10:130,x:x+180][shape]=(40,190,60)
                instance[10:130,x:x+180][shape]=color
            a,b = st.columns(2)
            picture(a,semantic,'Semantic: both regions have the cup class')
            picture(b,instance,'Instance: each cup has its own ID/color')
            st.caption('This is a labeled schematic made from the supplied cup outline, not another model prediction. It illustrates what additional information semantic and instance segmentation would provide.')
        controls['segmentation'] = st.slider('Segmentation foreground threshold',.05,.95,float(controls['segmentation']),.05)
        probability = decode(visual['saliency_png'])
        mask = probability >= controls['segmentation']
        a,b = st.columns(2)
        picture(a,(probability*255).astype('uint8'),'Saved foreground scores, scaled separately within each image')
        picture(b,mask_overlay(image,mask),'Thresholded foreground overlay')
        reference = item['reference_mask']
        if reference is None:
            st.info('This independent photograph has a box annotation but no pixel annotation. Inspect its mask qualitatively. No segmentation score is reported for it.')
        else:
            difference = np.zeros_like(image)
            difference[mask & reference]=(0,200,0)
            difference[mask & ~reference]=(200,0,200)
            difference[~mask & reference]=(0,220,240)
            a,b = st.columns(2)
            picture(a,reference.astype('uint8')*255,'Supplied approximate visible-cup annotation')
            picture(b,difference,'Green agreement, magenta extra foreground, yellow missed cup pixels')
            st.table([mask_metrics(mask,reference)])
        st.write('Mask IoU = shared foreground pixels / pixels in either mask. Dice = 2 × shared foreground / total foreground counts in both masks. Extra foreground is oversegmentation relative to this cup task. Missing cup pixels are undersegmentation. Both empty masks score 1 here, so inspect target-present and target-absent results separately.')
        st.caption('Reference silhouettes were manually traced independently of either model. Masks describe visible cup pixels and exclude the occluder. They are approximate teaching annotations. Reference boxes describe full cup extents, so boxes and masks have different annotation conventions.')
    elif step == 3:
        st.write('Compare the same scene across representations. Ask what the robot can infer from each output. The classification task supplies image-level labels. Detection proposes cup rectangles. Foreground segmentation supplies detailed boundaries without cup identity.')
        klass = process(image,Settings(**classical['settings']),classical.get('implementation')) if classical else None
        row = next(row for row in evidence['rows'] if row['image_id']==chosen)
        a,b = st.columns(2)
        picture(a,image,'Raw image')
        if klass: picture(b,klass['raw_mask'],'Classical threshold mask')
        st.write('Whole-image classification:',visual['top5'])
        a,b = st.columns(2)
        picture(a,annotate(image,suppress_duplicates(row['raw_detections'],controls['nms']),controls['detection']),'Cup detection boxes')
        picture(b,mask_overlay(image,decode(visual['saliency_png'])>=controls['segmentation']),'Class-agnostic segmentation')
        st.info('A grasping task may need a boundary, depth and calibration. A scene label supplies none of these. A precise foreground boundary can still include the wrong object. Image coordinates alone do not give a physical grasp pose.')
    else:
        st.write('Use the quantitative comparison below to test the visual impressions. Inspect normal, dim, blur, background, occluded and independent scenes. Keep the same image IDs across methods. Controlled changes isolate one factor, while independent photos combine different viewpoints, cup designs and real backgrounds.')
    preview = deepcopy(evidence)
    preview.update(selected_threshold=controls['detection'],nms_iou=controls['nms'],
                   classification_threshold=controls['classification'],segmentation_threshold=controls['segmentation'])
    for row in preview['rows']:
        row['detections'] = suppress_duplicates(row['raw_detections'],controls['nms'])
        best = row['detections'][0] if row['detections'] else {}
        row.update(detected=bool(best),confidence=best.get('confidence',0.),bbox=best.get('bbox'))
        row['selected_iou'] = iou(row['bbox'],row['reference_box'])
    a,b = st.columns(2)
    if step and a.button('Back to '+PARTS[step-1],key='learned.back'):
        controls['step'] = step-1
        _advance(st)
    if step<len(PARTS)-1 and b.button('Continue to '+PARTS[step+1],key='learned.next'):
        controls['step'] = step+1
        _advance(st)
    return preview,step


def _advance(st):
    from lab.autosave import save
    st.session_state['scroll_to_top'] = True
    save(st)
    st.rerun()
