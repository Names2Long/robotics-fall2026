# Frozen learned detector

This release bundles YOLOX nano from the official YOLOX 0.1.1rc0 release.

- Source: https://github.com/Megvii-BaseDetection/YOLOX/releases/tag/0.1.1rc0
- Artifact: https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_nano.onnx
- Upstream implementation: https://github.com/Megvii-BaseDetection/YOLOX
- License: Apache 2.0. See YOLOX_LICENSE.txt.
- SHA-256: `c789161ed43c8269fcd4e67c67eeeb4e80c622da2eb296a20bc6007bd18a0b7d`
- Input: `[1,3,416,416]`, BGR float values 0 to 255, top-left letterbox with padding 114.
- Output: `[1,3549,85]`, decoded with stride 8/16/32 grids. Score = objectness times class score.
- Classes: standard 80 COCO categories in labels.txt. Cup is index 41.
- Postprocessing: cup-only NMS at IoU 0.45. Keep scores at least 0.001 for later sweeps.

No training occurs. The loader verifies the checksum and output shape. A student does not download or replace the model. The original YOLOv8 parser was replaced because the release now specifies an actual reproducible artifact. Do not substitute a YOLOv8 model into this parser.

The core inference implementation is in ros2_ws/src/week08_perception/perception/learned.py and is shared with the ROS node and guide.

## Frozen image classifier

- Artifact: https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/image_classification_mobilenet/image_classification_mobilenetv1_2022apr.onnx
- Source and preprocessing: https://github.com/opencv/opencv_zoo/tree/main/models/image_classification_mobilenet
- SHA-256: `cf4c563b54e7144d7c2803ee22a6471e68ae87377554724d501624f602395bea`
- License: Apache 2.0, bundled in CLASSIFIER_LICENSE.txt.
- Labels: https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt, bundled as imagenet_labels.txt.
- Input: resized RGB 224 × 224, divided by 255, normalized by mean [0.485, 0.456, 0.406] and std [0.229, 0.224, 0.225]. Output: 1000 logits, converted to softmax scores.
- Cup-presence rule: sum scores for the ImageNet labels cup and coffee mug. A high espresso score does not count under this explicit mapping. It is not a calibrated cup probability.

## Frozen foreground segmenter

- Original model: https://github.com/xuebinqin/U-2-Net
- Released ONNX artifact: https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx
- Released preprocessing/postprocessing: https://github.com/danielgatis/rembg/blob/main/rembg/sessions/u2netp.py
- SHA-256: `309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8`
- License: Apache 2.0, bundled in SEGMENTER_LICENSE.txt.
- Input: RGB 320 × 320, per-image maximum normalization and the released mean/std normalization. Output: foreground scores, min/max normalized per image and resized to source coordinates. Saved scores are quantized to 8-bit PNG for portable evidence.
- Scope: class-agnostic salient foreground, not semantic cup labels or instance IDs. Cup-mask overlap evaluates suitability for the stated robot task. Other foreground objects can create extra regions.

The two extra model loaders live in perception/representations.py. All artifacts are bundled and checksum-verified. MobileNet V1 was selected to support the course container's OpenCV 4.6 runtime as well as the local runtime. No additional student inference dependency is required.
