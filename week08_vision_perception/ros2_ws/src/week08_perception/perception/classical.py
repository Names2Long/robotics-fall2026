from dataclasses import asdict, dataclass
import cv2
import numpy as np
import math


@dataclass(frozen=True)
class Settings:
    h_low: int = 0
    h_high: int = 179
    s_low: int = 0
    s_high: int = 65
    v_low: int = 150
    v_high: int = 255
    kernel: int = 3
    min_area: int = 300
    min_circularity: float = 0.
    smoothing: str = "none"
    blur_kernel: int = 3
    brightness: int = 0
    contrast: float = 1.

    def __post_init__(self):
        for low, high, maximum in ((self.h_low, self.h_high, 179), (self.s_low, self.s_high, 255), (self.v_low, self.v_high, 255)):
            if not 0 <= low <= high <= maximum:
                raise ValueError("Threshold bounds must be ordered and within the channel range")
        if self.kernel not in (1, 3, 5, 7, 9) or self.min_area < 1:
            raise ValueError("Use a positive minimum area and an odd kernel from 1 to 9")
        if self.smoothing not in ("none", "Gaussian", "median") or self.blur_kernel not in (1, 3, 5, 7, 9):
            raise ValueError("Choose none, Gaussian or median smoothing with an odd kernel")
        if not math.isfinite(self.contrast) or not .5 <= self.contrast <= 2 or not -80 <= self.brightness <= 80 or not 0 <= self.min_circularity <= 1:
            raise ValueError("Preprocessing or shape controls are outside the lab range")


def process(image, settings=Settings(), implementation=None):
    if implementation is None:
        from perception.lesson import detect
        return detect(image, settings)
    from perception.student_code import evaluate
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    raw = cv2.inRange(hsv, np.array([settings.h_low, settings.s_low, settings.v_low]),
                      np.array([settings.h_high, settings.s_high, settings.v_high]))
    if implementation:
        context = {"image": image, "lower": np.array([settings.h_low, settings.s_low, settings.v_low]),
                   "upper": np.array([settings.h_high, settings.s_high, settings.v_high])}
        hsv = evaluate(implementation["hsv"], context)
        raw = evaluate(implementation["raw"], {**context, "hsv": hsv})
    kernel = np.ones((settings.kernel, settings.kernel), np.uint8)
    clean = cv2.morphologyEx(cv2.morphologyEx(raw, cv2.MORPH_OPEN, kernel), cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if implementation: contours = evaluate(implementation["contours"], {"clean": clean})
    candidates = image.copy()
    cv2.drawContours(candidates, contours, -1, (255, 150, 0), 2)
    rows = []
    valid = []
    for index, contour in enumerate(contours):
        area = float(cv2.contourArea(contour))
        x, y, w, h = cv2.boundingRect(contour)
        rows.append({"candidate": index, "area_px": area, "eligible": area >= settings.min_area,
                     "x": x, "y": y, "width": w, "height": h})
        cv2.putText(candidates, str(index), (x, max(y, 15)), cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 80, 0), 1)
        if area >= settings.min_area:
            valid.append((area, index, (x, y, w, h)))
    annotated = image.copy()
    box = None
    chosen = None
    if valid:
        _, chosen, box = max(valid)
        if implementation:
            eligible = [contours[i] for _, i, _ in valid]
            selected = evaluate(implementation["selected"], {"eligible": eligible})
            chosen = next(i for _, i, _ in valid if np.array_equal(contours[i], selected))
            box = cv2.boundingRect(selected)
        x, y, w, h = box
        cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 220, 0), 2)
        cv2.circle(annotated, (int(x+w/2), int(y+h/2)), 5, (0, 0, 255), -1)
    cv2.line(annotated, (image.shape[1]//2, 0), (image.shape[1]//2, image.shape[0]), (255, 0, 255), 1)
    return {"hsv": hsv, "raw_mask": raw, "mask": clean, "contours": candidates,
            "annotated": annotated, "candidates": rows, "selected": chosen, "bbox": box,
            "detected": box is not None, "settings": asdict(settings)}
