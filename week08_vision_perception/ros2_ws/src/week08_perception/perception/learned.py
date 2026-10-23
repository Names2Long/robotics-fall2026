"""Frozen YOLOX nano inference. Original preprocessing and grid decoding conventions."""
import hashlib
import os
from pathlib import Path
import cv2
import numpy as np

MODEL = Path(os.environ.get("WEEK08_LAB_ROOT", Path(__file__).resolve().parents[4])) / "assets" / "models" / "detector.onnx"
MODEL_SHA256 = "c789161ed43c8269fcd4e67c67eeeb4e80c622da2eb296a20bc6007bd18a0b7d"
TARGET_CLASS = 41  # COCO cup, zero based


class FrozenDetector:
    def __init__(self, model=MODEL):
        if not model.is_file() or hashlib.sha256(model.read_bytes()).hexdigest() != MODEL_SHA256:
            raise ValueError("The frozen YOLOX model is missing or has changed. Restore assets/models/detector.onnx.")
        self.net = cv2.dnn.readNetFromONNX(str(model))

    def predict(self, image, suppress=True):
        # YOLOX uses BGR float pixels 0..255, top-left letterbox with value 114.
        ratio = min(416/image.shape[0], 416/image.shape[1])
        resized = cv2.resize(image, (int(image.shape[1]*ratio), int(image.shape[0]*ratio)))
        canvas = np.full((416, 416, 3), 114, np.uint8)
        canvas[:resized.shape[0], :resized.shape[1]] = resized
        self.net.setInput(cv2.dnn.blobFromImage(canvas, 1.0, (416, 416), swapRB=False))
        raw = np.asarray(self.net.forward())[0].copy()
        if raw.shape != (3549, 85):
            raise ValueError(f"Unexpected YOLOX output {raw.shape}")
        grids, strides = [], []
        for stride in (8, 16, 32):
            y, x = np.meshgrid(np.arange(416//stride), np.arange(416//stride), indexing="ij")
            grids.append(np.stack((x, y), axis=-1).reshape(-1, 2))
            strides.append(np.full((x.size, 1), stride))
        grid, stride = np.concatenate(grids), np.concatenate(strides)
        raw[:, :2] = (raw[:, :2]+grid)*stride
        raw[:, 2:4] = np.exp(np.clip(raw[:, 2:4], -20, 20))*stride
        scores = raw[:, 4]*raw[:, 5+TARGET_CLASS]
        candidate = np.where(scores >= .001)[0]
        boxes = []
        for index in candidate:
            cx, cy, w, h = raw[index, :4]/ratio
            boxes.append([float(cx-w/2), float(cy-h/2), float(w), float(h)])
        detections = []
        for k, box in enumerate(boxes):
            x, y, w, h = box
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(image.shape[1], x+w), min(image.shape[0], y+h)
            if x2 > x1 and y2 > y1:
                detections.append({"label": "cup", "confidence": float(scores[candidate[k]]),
                                   "bbox": [x1, y1, x2-x1, y2-y1]})
        detections = sorted(detections, key=lambda row: row["confidence"], reverse=True)
        return suppress_duplicates(detections,.45) if suppress else detections


def suppress_duplicates(detections, overlap):
    if not 0 <= overlap <= 1: raise ValueError('NMS overlap must be between 0 and 1')
    if not detections: return []
    kept = cv2.dnn.NMSBoxes([r['bbox'] for r in detections],[r['confidence'] for r in detections],.001,float(overlap))
    return [detections[int(i)] for i in np.asarray(kept).reshape(-1)]


def annotate(image, detections, threshold):
    result = image.copy()
    for detection in detections:
        if detection["confidence"] < threshold:
            continue
        x, y, w, h = map(int, detection["bbox"])
        cv2.rectangle(result, (x, y), (x+w, y+h), (0, 220, 0), 2)
        cv2.putText(result, f"cup {detection['confidence']:.2f}", (x, max(16, y-5)), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 160, 0), 1)
    return result
