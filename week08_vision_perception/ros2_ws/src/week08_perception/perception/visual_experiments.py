"""Saved predictions let threshold and metric activities reuse actual inference."""
import base64
import time
from functools import lru_cache
import cv2
import numpy as np
from perception.dataset import samples, fingerprint
from perception.representations import classify, segment, MODELS
from evaluation.metrics import evaluate_rows, mask_metrics


def encode(probability):
    ok, data = cv2.imencode('.png',np.round(np.clip(probability,0,1)*255).astype('uint8'))
    if not ok: raise ValueError("Cannot save segmentation output")
    return base64.b64encode(data.tobytes()).decode('ascii')


@lru_cache(maxsize=64)
def decode(text):
    data = cv2.imdecode(np.frombuffer(base64.b64decode(text,validate=True),np.uint8),cv2.IMREAD_GRAYSCALE)
    if data is None or data.shape != (320,480): raise ValueError("Invalid saved segmentation image")
    result = data.astype(np.float32)/255
    result.setflags(write=False)
    return result


def run_visual_collection():
    items = samples()
    classify(items[0]['image'])
    segment(items[0]['image'])
    rows = []
    for item in items:
        started = time.perf_counter()
        classes = classify(item['image'])
        classifier_ms = (time.perf_counter()-started)*1000
        started = time.perf_counter()
        saliency = segment(item['image'])
        rows.append({"image_id":item['image_id'],"condition":item['condition'],"expected":item['expected'],
                     **classes,"classifier_ms":classifier_ms,"segmenter_ms":(time.perf_counter()-started)*1000,
                     "saliency_png":encode(saliency)})
    return {"dataset":fingerprint(),"models":MODELS,"rows":rows}


def validate_visual(evidence):
    if not isinstance(evidence,dict) or evidence.get('dataset') != fingerprint() or evidence.get('models') != MODELS:
        raise ValueError("Run the classification and segmentation collection for the current models and images")
    expected = {i['image_id']:i for i in samples()}
    rows = evidence.get('rows',[])
    if len(rows) != len(expected) or {r.get('image_id') for r in rows} != set(expected):
        raise ValueError("Visual representation evidence needs every shared image exactly once")
    for row in rows:
        item = expected[row['image_id']]
        if row['expected'] != item['expected'] or row['condition'] != item['condition'] or not 0 <= row['cup_score'] <= 1:
            raise ValueError("Invalid classification evidence")
        decode(row['saliency_png'])
    return rows


def classification_results(rows, threshold):
    return evaluate_rows([{**row,"detected":True,"confidence":row['cup_score'],"latency_ms":row['classifier_ms']} for row in rows],threshold)


def segmentation_results(rows, threshold):
    references = {r['image_id']:r for r in samples()}
    results = []
    for row in rows:
        reference = references[row['image_id']]['reference_mask']
        if reference is not None:
            results.append({"image_id":row['image_id'],"condition":row['condition'],"target_present":row['expected'],
                            **mask_metrics(decode(row['saliency_png'])>=threshold,reference)})
    return results
