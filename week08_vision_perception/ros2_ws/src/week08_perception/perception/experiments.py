import csv
import hashlib
import io
import json
import time
import math
from functools import lru_cache
from copy import deepcopy
from dataclasses import asdict
import cv2
from perception import dataset
from perception.classical import Settings, process
from perception.learned import FrozenDetector, MODEL_SHA256, annotate, suppress_duplicates
from evaluation.metrics import evaluate_rows, threshold_sweep, by_condition, localization_metrics, iou
from perception.student_code import check_implementation


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def run(method, settings=None, implementation=None):
    if method == 'learned':
        from perception.representations import MODELS
        from lab.autosave import write_json
        token = signature({'dataset': dataset.fingerprint(), 'models': MODELS, 'detector': MODEL_SHA256})
        path = dataset.ROOT/'runtime/model_cache'/(token+'.json')
        try:
            evidence = json.loads(path.read_text(encoding='utf-8'))
            validate(evidence, method)
            return evidence
        except (OSError, ValueError, TypeError, KeyError):
            pass
        evidence = _run(method, settings, implementation)
        validate(evidence, method)
        write_json(path, evidence)
        return evidence
    return _run(method, settings, implementation)


def _run(method, settings=None, implementation=None):
    if implementation is not None: check_implementation(implementation)
    settings = settings or asdict(Settings())
    detector = FrozenDetector() if method == "learned" else None
    if method not in ("classical", "learned"):
        raise ValueError("Unknown method")
    if detector:
        detector.predict(dataset.tuning_image())
    rows = []
    for item in dataset.samples():
        started = time.perf_counter()
        if detector:
            raw_detections = detector.predict(item["image"],suppress=False)
            detections = suppress_duplicates(raw_detections,.45)
            best = detections[0] if detections else {}
            detected, score, box = bool(detections), best.get("confidence", 0), best.get("bbox")
        else:
            output = process(item["image"], Settings(**settings), implementation)
            detected, box = output["detected"], output["bbox"]
            score, detections, raw_detections = float(detected), [], []
        rows.append({"image_id": item["image_id"], "condition": item["condition"], "expected": item["expected"],
                     "detected": detected, "confidence": float(score), "bbox": box, "detections": detections,"raw_detections":raw_detections,
                     "reference_box": item["reference_box"], "selected_iou": iou(box,item["reference_box"]),
                     "latency_ms": (time.perf_counter()-started)*1000})
    from perception.lesson import code_for
    evidence = {"schema_version": 2, "method": method, "dataset": dataset.fingerprint(), "target": "cup",
            "settings": settings if method == "classical" else {"model_sha256": MODEL_SHA256, "score_floor": .001},
            "rows": rows, "implementation": implementation,
            "program": code_for(Settings(**settings)) if method == "classical" and implementation is None else None,
            "selected_threshold": .5 if detector else None}
    if detector:
        from perception.visual_experiments import run_visual_collection
        evidence['representations'] = run_visual_collection()
        evidence['classification_threshold'] = .1
        evidence['segmentation_threshold'] = .5
        evidence['nms_iou'] = .45
    return evidence


def validate(evidence, method):
    # Include the live dataset and code identity so changing either invalidates the cache.
    from perception.lesson import code_for
    code = code_for(Settings(**evidence['settings'])) if isinstance(evidence, dict) and method == 'classical' else ''
    return deepcopy(_validated(json.dumps(evidence, sort_keys=True, allow_nan=False), method, dataset.fingerprint(), code))


@lru_cache(maxsize=12)
def _validated(serialized, method, dataset_token, code_token):
    return _validate(json.loads(serialized), method)


def _validate(evidence, method):
    if not isinstance(evidence, dict) or evidence.get("schema_version") != 2 or evidence.get("method") != method:
        raise ValueError("Run the current experiment to create compatible evidence")
    if evidence.get("dataset") != dataset.fingerprint() or evidence.get("target") != "cup":
        raise ValueError("The image collection has changed. Run the experiment again")
    expected = {item["image_id"]: item for item in dataset.samples()}
    rows = evidence.get("rows", [])
    if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows) or len(rows) != len(expected) or {r.get("image_id") for r in rows} != set(expected):
        raise ValueError("Evidence must contain exactly one row per test image")
    for row in rows:
        item = expected[row["image_id"]]
        if row.get("expected") != item["expected"] or row.get("condition") != item["condition"]:
            raise ValueError("Image labels do not match the shared collection")
        if row.get("reference_box") != item["reference_box"]:
            raise ValueError("Reference boxes changed. Run the current experiment")
        detections = row.get("detections",[])
        if not isinstance(detections,list) or any(not isinstance(d,dict) for d in detections): raise ValueError("Invalid candidates")
        boxes = [row.get("bbox")] + [d.get("bbox") for d in detections]
        for box in boxes:
            if box is None: continue
            if not isinstance(box,(list,tuple)) or len(box)!=4 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in box) or box[2]<=0 or box[3]<=0:
                raise ValueError("Invalid bounding box. Re-run this experiment")
        if row.get("detected") and row.get("bbox") is None: raise ValueError("A detection needs a box")
        for detection in detections:
            score = detection.get("confidence")
            if detection.get("label") != "cup" or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=1:
                raise ValueError("Invalid learned candidate")
    if method == "classical":
        Settings(**evidence["settings"])
        if evidence.get("program") is not None:
            from perception.lesson import code_for
            if evidence["program"] != code_for(Settings(**evidence["settings"])):
                raise ValueError("The detector code has changed. Run Mission 1 again to save current evidence")
        if evidence.get("implementation") is not None: check_implementation(evidence["implementation"])
    elif evidence.get("settings", {}).get("model_sha256") != MODEL_SHA256:
        raise ValueError("The learned model does not match the frozen release")
    if method == "learned":
        from perception.visual_experiments import validate_visual
        validate_visual(evidence.get('representations'))
        if not .001 <= evidence.get('classification_threshold',0) <= .9 or not .05 <= evidence.get('segmentation_threshold',0) <= .95:
            raise ValueError("Save valid classification and segmentation thresholds")
    threshold = evidence.get("selected_threshold") if method == "learned" else None
    if method == "learned" and (not isinstance(threshold, (int, float)) or not .05 <= threshold <= .9):
        raise ValueError("Select a threshold from 0.05 to 0.90")
    result = {"metrics": evaluate_rows(rows, threshold), "conditions": by_condition(rows, threshold),
            "localization": localization_metrics(rows,threshold),
            "box_conditions": [{"condition":condition,**localization_metrics([r for r in rows if r["condition"]==condition],threshold)} for condition in dataset.CONDITIONS],
            "sweep": threshold_sweep(rows) if method == "learned" else []}
    if method == 'learned':
        from perception.visual_experiments import classification_results,segmentation_results
        from evaluation.metrics import detection_pr
        visual = evidence['representations']['rows']
        result.update(classification=classification_results(visual,evidence['classification_threshold']),
                      segmentation=segmentation_results(visual,evidence['segmentation_threshold']),
                      detection_pr=detection_pr(rows))
    return result


def csv_bytes(evidence):
    output = io.StringIO()
    fields = ("image_id", "condition", "expected", "detected", "confidence", "latency_ms", "bbox", "reference_box", "selected_iou")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(evidence["rows"])
    return output.getvalue().encode()


def evidence_images(evidence):
    images = {item["image_id"]: item["image"] for item in dataset.samples()}
    for row in evidence["rows"]:
        image = images[row["image_id"]]
        if evidence["method"] == "classical":
            result = process(image, Settings(**evidence["settings"]), evidence.get("implementation"))
            outputs = {key: result[key] for key in ("raw_mask", "mask", "contours", "annotated")}
            outputs['preprocessed'] = result.get('preprocessed',image)
        else:
            outputs = {"annotated": annotate(image, row["detections"], evidence["selected_threshold"])}
            from perception.visual_experiments import decode
            from perception.representations import mask_overlay
            visual = next(r for r in evidence['representations']['rows'] if r['image_id']==row['image_id'])
            probability = decode(visual['saliency_png'])
            mask = probability >= evidence['segmentation_threshold']
            outputs.update(saliency=(probability*255).astype('uint8'), segmentation=mask.astype('uint8')*255,
                           segmentation_overlay=mask_overlay(image,mask))
            reference = next(r for r in dataset.samples() if r['image_id']==row['image_id'])['reference_mask']
            if reference is not None: outputs['reference_mask'] = reference.astype('uint8')*255
        for name, output in outputs.items():
            if name == "annotated" and row["reference_box"]:
                x,y,w,h = map(int,row["reference_box"])
                cv2.rectangle(output,(x,y),(x+w,y+h),(255,255,0),1)
            ok, encoded = cv2.imencode(".png", output)
            if not ok:
                raise ValueError("Could not encode evidence image")
            yield f"images/{row['image_id']}_{name}.png", encoded.tobytes()
