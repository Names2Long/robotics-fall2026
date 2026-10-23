import math

from perception.dataset import CONDITIONS


def iou(box, reference):
    if box is None or reference is None: return 0.
    x,y,w,h = box
    a,b,c,d = reference
    intersection = max(0,min(x+w,a+c)-max(x,a))*max(0,min(y+h,b+d)-max(y,b))
    union = w*h+c*d-intersection
    return intersection/union if union > 0 else 0.


def localization_metrics(rows, threshold=None):
    tp=fp=fn=0
    for row in rows:
        if threshold is None:
            boxes = [row["bbox"]] if row["detected"] else []
        else:
            boxes = [d["bbox"] for d in row["detections"] if d["confidence"] >= threshold]
        matched = bool(row["expected"] and any(iou(box,row["reference_box"]) >= .5 for box in boxes))
        tp += matched
        fp += len(boxes)-int(matched)
        fn += row["expected"] and not matched
    return {"box_tp":tp,"box_fp":fp,"box_fn":fn,"box_precision":tp/(tp+fp) if tp+fp else None,
            "box_recall":tp/(tp+fn) if tp+fn else None}


def evaluate_rows(rows, threshold=None):
    """Image-level target presence. A positive does not validate the box location."""
    tp = fp = fn = tn = 0
    latencies = []
    for row in rows:
        if type(row.get("expected")) is not bool or type(row.get("detected")) is not bool:
            raise ValueError("Expected and detected must be booleans")
        score = float(row.get("confidence", 0))
        latency = float(row.get("latency_ms", 0))
        if not math.isfinite(score) or not 0 <= score <= 1 or not math.isfinite(latency) or latency < 0:
            raise ValueError("Invalid score or processing time")
        predicted = row["detected"] and (threshold is None or score >= threshold)
        expected = row["expected"]
        tp += expected and predicted
        fp += not expected and predicted
        fn += expected and not predicted
        tn += not expected and not predicted
        latencies.append(latency)
    return {"sample_count": len(rows), "conditions": sorted({r["condition"] for r in rows}),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": tp/(tp+fp) if tp+fp else None,
            "recall": tp/(tp+fn) if tp+fn else None,
            "false_positive_rate": fp/(fp+tn) if fp+tn else None,
            "accuracy": (tp+tn)/len(rows) if rows else None,
            "mean_latency_ms": sum(latencies)/len(latencies) if latencies else None}


def threshold_sweep(rows, thresholds=(.05, .20, .35, .50, .65, .80)):
    return [{"threshold": value, **evaluate_rows(rows, value),
             **(localization_metrics(rows,value) if rows and "reference_box" in rows[0] else {})} for value in thresholds]


def by_condition(rows, threshold=None):
    return [{"condition": name, **evaluate_rows([r for r in rows if r["condition"] == name], threshold)} for name in CONDITIONS]


def conditions_complete(rows):
    return set(CONDITIONS).issubset({r.get("condition") for r in rows})


def mask_metrics(prediction, reference):
    import numpy as np
    prediction,reference = np.asarray(prediction,bool),np.asarray(reference,bool)
    if prediction.shape != reference.shape: raise ValueError("Masks must have matching dimensions")
    intersection = int((prediction & reference).sum())
    union = int((prediction | reference).sum())
    total = int(prediction.sum()+reference.sum())
    return {"mask_iou":intersection/union if union else 1.,"dice":2*intersection/total if total else 1.,
            "extra_pixels":int((prediction & ~reference).sum()),"missed_pixels":int((~prediction & reference).sum())}


def detection_pr(rows, overlap=.5):
    """One-class ranked box evaluation, greedy matching per image and all-point AP."""
    positives = sum(bool(row["expected"]) for row in rows)
    candidates = sorted([(d["confidence"],i,d["bbox"]) for i,row in enumerate(rows) for d in row.get("detections",[])],reverse=True)
    matched = set()
    points = []
    tp=fp=0
    for score,index,box in candidates:
        row = rows[index]
        correct = row["expected"] and index not in matched and iou(box,row["reference_box"]) >= overlap
        if correct: tp+=1; matched.add(index)
        else: fp+=1
        points.append({"score":score,"precision":tp/(tp+fp),"recall":tp/positives if positives else 0.})
    # Precision envelope, integrated over achieved recall. Unreached recall contributes zero.
    envelope = 0.
    ap = 0.
    for index in range(len(points)-1,-1,-1):
        envelope = max(envelope,points[index]["precision"])
        previous = points[index-1]["recall"] if index else 0.
        ap += (points[index]["recall"]-previous)*envelope
    return {"points":points,"ap50":ap if positives else None,"positive_images":positives}
