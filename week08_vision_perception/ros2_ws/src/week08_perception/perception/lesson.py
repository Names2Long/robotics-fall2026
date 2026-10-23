"""Readable, parameterized OpenCV code shared by the lesson and detector."""
from dataclasses import asdict


def code_for(settings, through="box"):
    """Generate trusted code from validated numeric settings, never user text."""
    from perception.classical import Settings
    settings = Settings(**asdict(settings))
    parts = ["""import cv2
import numpy as np

# The guide has loaded the selected photograph into image.
working = image.copy()""" + f"""
working = np.clip(working.astype(float) * {settings.contrast} + {settings.brightness}, 0, 255).astype('uint8')
""" + (f"working = cv2.GaussianBlur(working, ({settings.blur_kernel}, {settings.blur_kernel}), 0)\n" if settings.smoothing == "Gaussian" else
        f"working = cv2.medianBlur(working, {settings.blur_kernel})\n" if settings.smoothing == "median" else "") +
        "hsv = cv2.cvtColor(working, cv2.COLOR_BGR2HSV)",
        f"""lower = np.array([{settings.h_low}, {settings.s_low}, {settings.v_low}])
upper = np.array([{settings.h_high}, {settings.s_high}, {settings.v_high}])
raw_mask = cv2.inRange(hsv, lower, upper)""",
        f"""kernel = np.ones(({settings.kernel}, {settings.kernel}), np.uint8)
opened = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel)""",
        "clean = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)",
        f"""contours, hierarchy = cv2.findContours(
    clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
minimum_area = {settings.min_area}
minimum_circularity = {settings.min_circularity}
contour_image = image.copy()
cv2.drawContours(contour_image, contours, -1, (255, 150, 0), 2)
rows = []
eligible = []
for index, contour in enumerate(contours):
    area = float(cv2.contourArea(contour))
    perimeter = cv2.arcLength(contour, True)
    circularity = 4 * np.pi * area / perimeter**2 if perimeter else 0
    moments = cv2.moments(contour)
    centroid = [moments['m10']/moments['m00'], moments['m01']/moments['m00']] if moments['m00'] else None
    passes = area >= minimum_area and circularity >= minimum_circularity
    rows.append(dict(candidate=index, area_px=area,
                     circularity=float(circularity), centroid=centroid, eligible=passes))
    x, y = contour[0, 0]
    cv2.putText(contour_image, str(index), (x, max(y, 15)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 80, 0), 1)
    if passes:
        eligible.append((area, index))""",
        """annotated = image.copy()
box = None
selected = None
if eligible:
    area, selected = max(eligible)
    box = cv2.boundingRect(contours[selected])
    x, y, width, height = box
    cv2.rectangle(annotated, (x, y), (x + width, y + height), (0, 220, 0), 2)
    center = (int(x + width / 2), int(y + height / 2))
    cv2.circle(annotated, center, 5, (0, 0, 255), -1)
    centroid = rows[selected]['centroid']
    if centroid:
        cv2.drawMarker(annotated, tuple(map(int, centroid)), (0, 255, 255), markerSize=12)
image_center_x = image.shape[1] // 2
cv2.line(annotated, (image_center_x, 0),
         (image_center_x, image.shape[0]), (255, 0, 255), 1)
detected = box is not None"""
    ]
    stops = {"hsv": 1, "mask": 2, "opening": 3, "closing": 4, "contours": 5, "box": 6}
    if through not in stops:
        raise ValueError("Unknown lesson operation")
    return "\n\n".join(parts[:stops[through]])


def execute(image, settings, through="box"):
    namespace = {"image": image.copy()}
    # Only code_for's fixed source and validated numbers enter this execution.
    exec(compile(code_for(settings, through), "<lab7 detector>", "exec"), namespace)
    return namespace


def detect(image, settings):
    values = execute(image, settings)
    return {"hsv": values["hsv"], "raw_mask": values["raw_mask"],
            "preprocessed": values["working"],
            "mask": values["clean"], "contours": values["contour_image"],
            "annotated": values["annotated"], "candidates": values["rows"],
            "selected": values["selected"], "bbox": values["box"],
            "detected": values["detected"], "settings": asdict(settings)}
