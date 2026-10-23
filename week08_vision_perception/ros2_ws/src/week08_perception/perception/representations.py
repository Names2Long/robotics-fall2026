"""Frozen image classification and class-agnostic foreground segmentation."""
from functools import lru_cache
import hashlib
import threading
import cv2
import numpy as np
from perception.learned import MODEL

ASSETS = MODEL.parent
MODELS = {
    "classifier": "cf4c563b54e7144d7c2803ee22a6471e68ae87377554724d501624f602395bea",
    "segmenter": "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8",
}


@lru_cache(maxsize=2)
def network(kind):
    path = ASSETS/(kind+".onnx")
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != MODELS[kind]:
        raise ValueError(f"Restore the bundled {kind}.onnx model before running this activity")
    return cv2.dnn.readNetFromONNX(str(path)), threading.Lock()


def classify(image):
    labels = (ASSETS/"imagenet_labels.txt").read_text(encoding="utf-8").splitlines()
    if len(labels) != 1000:
        raise ValueError("The classifier needs the supplied 1000 ImageNet labels")
    rgb = cv2.cvtColor(cv2.resize(image, (224, 224)), cv2.COLOR_BGR2RGB).astype(np.float32)/255
    blob = ((rgb-np.array([.485,.456,.406]))/np.array([.229,.224,.225])).transpose(2,0,1)[None].astype(np.float32)
    net, lock = network("classifier")
    with lock:
        net.setInput(blob)
        scores = net.forward().reshape(-1).copy()
    if scores.size != 1000 or not np.isfinite(scores).all():
        raise ValueError("Unexpected classifier output")
    # The bundled graph returns logits. Softmax normalizes their relative support.
    scores = np.exp(scores-scores.max())
    scores /= scores.sum()
    cup_indices = [i for i, label in enumerate(labels) if label in ("coffee mug", "cup")]
    if len(cup_indices) != 2:
        raise ValueError("Cup label mapping does not match the supplied labels")
    return {"top5": [{"label":labels[i],"score":float(scores[i])} for i in scores.argsort()[-5:][::-1]],
            "cup_score":float(scores[cup_indices].sum())}


def segment(image):
    rgb = cv2.cvtColor(cv2.resize(image,(320,320)),cv2.COLOR_BGR2RGB).astype(np.float32)
    rgb /= max(float(rgb.max()), 1.)
    blob = ((rgb-np.array([.485,.456,.406]))/np.array([.229,.224,.225])).transpose(2,0,1)[None].astype(np.float32)
    net, lock = network("segmenter")
    with lock:
        net.setInput(blob)
        probability = net.forward()[0,0].copy()
    if probability.shape != (320,320) or not np.isfinite(probability).all():
        raise ValueError("Unexpected segmentation output")
    # Match the released inference recipe's per-image saliency normalization.
    low, high = float(probability.min()), float(probability.max())
    probability = (probability-low)/max(high-low,1e-8)
    return cv2.resize(probability,(image.shape[1],image.shape[0]))


def mask_overlay(image, mask):
    output = image.copy()
    output[mask] = (.5*output[mask]+.5*np.array([30,200,50])).astype('uint8')
    return output
