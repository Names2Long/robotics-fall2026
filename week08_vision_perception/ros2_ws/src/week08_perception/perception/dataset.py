import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(os.environ.get("WEEK08_LAB_ROOT", Path(__file__).resolve().parents[4]))
SOURCE = ROOT / "assets" / "conditions" / "tabletop.jpg"
CONDITIONS = ("normal", "dim", "glare", "far", "occluded", "rotated", "cluttered", "distractor", "blur", "background", "independent")
VERSION = "tabletop-controls-v5"
REFERENCE_BOX = [235, 0, 148, 108]  # Visible cup and handle. Top is outside the photograph.


def transform(image, condition, variant, box=None):
    image = image.copy()
    matrix = None
    if condition == "normal": matrix = np.float32([[1, 0, 8*variant], [0, 1, 0]])
    elif condition == "dim": image = np.clip(image.astype(float)*(.45 if variant == 1 else .65), 0, 255).astype(np.uint8)
    elif condition == "glare":
        overlay = image.copy()
        cv2.circle(overlay, (230,145), 45+15*variant, (255,255,255), -1)
        image = cv2.addWeighted(image,.25,overlay,.75,0)
    elif condition == "far":
        scale = .4 if variant == 1 else .6
        matrix = np.float32([[scale,0,240*(1-scale)],[0,scale,160*(1-scale)]])
    elif condition == "occluded": cv2.rectangle(image,(275,30),(295+15*variant,115),(90,90,90),-1)
    elif condition == "rotated": matrix = cv2.getRotationMatrix2D((240,160),12*variant,1)
    elif condition == "cluttered":
        cv2.rectangle(image,(5,20),(90,90+20*variant),(230,230,230),-1)
        cv2.circle(image,(425,250),20*variant,(240,240,240),-1)
    elif condition == "blur": image = cv2.GaussianBlur(image,(9 if variant == 1 else 17,)*2,0)
    elif condition == "background":
        mask = source_mask()
        yy,xx = np.indices(image.shape[:2])
        background = np.full_like(image,(45,125,75) if variant == 1 else (210,205,195))
        background[((xx//35+yy//35)%2)==0] = (170,180,190)
        image[~mask] = background[~mask]
    if matrix is not None:
        image = cv2.warpAffine(image,matrix,(480,320),borderMode=cv2.BORDER_CONSTANT,borderValue=(65,75,85))
        if box:
            x,y,w,h = box
            corners = cv2.transform(np.float32([[[x,y],[x+w,y],[x,y+h],[x+w,y+h]]]),matrix)[0]
            low,high = corners.min(axis=0),corners.max(axis=0)
            low = np.maximum(low,0)
            high = np.minimum(high,[480,320])
            box = [float(low[0]),float(low[1]),float(high[0]-low[0]),float(high[1]-low[1])]
    return image,box


def independent(name, normalized_box):
    image = cv2.imread(str(ROOT/"assets/conditions"/name))
    if image is None: raise FileNotFoundError(name)
    h,w = image.shape[:2]
    scale = min(480/w,320/h)
    resized = cv2.resize(image,(round(w*scale),round(h*scale)))
    canvas = np.full((320,480,3),95,np.uint8)
    dx,dy = (480-resized.shape[1])//2,(320-resized.shape[0])//2
    canvas[dy:dy+resized.shape[0],dx:dx+resized.shape[1]] = resized
    x,y,bw,bh = normalized_box
    return canvas,[dx+x*w*scale,dy+y*h*scale,bw*w*scale,bh*h*scale]


def tuning_image():
    image = cv2.imread(str(SOURCE))
    if image is None:
        raise FileNotFoundError("The bundled tabletop.jpg scene is missing. Restore the Lab 7 assets.")
    return cv2.resize(image, (480, 320))


def source_mask():
    annotation = json.loads((ROOT/"assets/conditions/tabletop_annotation.json").read_text(encoding="utf-8"))
    points = np.asarray(annotation["polygon"],dtype=np.int32)
    mask = np.zeros((320,480),np.uint8)
    cv2.fillPoly(mask,[points.astype(np.int32)],1)
    for hole in annotation.get("holes", []):
        cv2.fillPoly(mask,[np.asarray(hole,dtype=np.int32)],0)
    return mask.astype(bool)


def reference_mask(condition, variant):
    mask = source_mask().astype(np.uint8)
    matrix = None
    if condition == "normal": matrix = np.float32([[1,0,8*variant],[0,1,0]])
    elif condition == "far":
        scale = .4 if variant == 1 else .6
        matrix = np.float32([[scale,0,240*(1-scale)],[0,scale,160*(1-scale)]])
    elif condition == "rotated": matrix = cv2.getRotationMatrix2D((240,160),12*variant,1)
    elif condition == "occluded": cv2.rectangle(mask,(275,30),(295+15*variant,115),0,-1)
    if matrix is not None: mask = cv2.warpAffine(mask,matrix,(480,320),flags=cv2.INTER_NEAREST,borderValue=0)
    return mask.astype(bool)


@lru_cache(maxsize=1)
def _samples():
    original = tuning_image()
    items = []
    for condition in CONDITIONS[:-1]:
        for variant in (1, 2):
            image = original.copy()
            if condition == "distractor":
                image[:] = (65,75,85)
                cv2.rectangle(image,(140,80),(300,210),(220,220,220),-1)
                if variant == 2: cv2.circle(image,(340,240),40,(250,250,250),-1)
            if condition != "distractor": image, box = transform(original, condition, variant, REFERENCE_BOX)
            else: box = None
            items.append({"image_id": f"{condition}_{variant}", "condition": condition,
                          "expected": condition != "distractor", "image": image, "reference_box": box,
                          "reference_mask":reference_mask(condition,variant) if condition != "distractor" else np.zeros((320,480),bool)})
    # Negative controls under each non-distractor condition prevent a single negative dominating FPR.
    for condition in (c for c in CONDITIONS if c not in ("distractor","independent")):
        image = np.full_like(original, 95)
        cv2.rectangle(image, (130, 70), (290, 240), (200, 210, 220), -1)
        image,_ = transform(image,condition,1)
        items.append({"image_id": f"{condition}_absent", "condition": condition, "expected": False, "image": image, "reference_box": None,"reference_mask":np.zeros((320,480),bool)})
    for name,box in (("independent_mug.jpg",[0,0,.81,.87]),("independent_cup.jpg",[.08,.01,.85,.94])):
        image,reference = independent(name,box)
        items.append({"image_id": name[:-4], "condition": "independent", "expected": True,
                      "image": image, "reference_box": reference,"reference_mask":None})
    # Shared cache is immutable. Callers copy before drawing or altering pixels.
    for item in items:
        item['image'].setflags(write=False)
        if item['reference_mask'] is not None: item['reference_mask'].setflags(write=False)
    return tuple(items)


def samples():
    return [{**item, 'reference_box': list(item['reference_box']) if item['reference_box'] else None}
            for item in _samples()]


@lru_cache(maxsize=1)
def fingerprint():
    digest = hashlib.sha256(VERSION.encode())
    for item in samples():
        digest.update(json.dumps({k: v for k, v in item.items() if k not in ("image","reference_mask")}, sort_keys=True).encode())
        digest.update(item["image"].tobytes())
        if item["reference_mask"] is not None: digest.update(item["reference_mask"].tobytes())
    return digest.hexdigest()
