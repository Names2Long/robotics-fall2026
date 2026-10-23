# Incorporated vision investigations

The active lab has 15 independent-input playground steps and one detector investigation in three parts. Part A covers classical detection. Part B has four guided learned-representation activities. Part C is a focused comparison. The former behavior mission is archived and not required. Historical mission_1 and mission_2 names below identify compatible storage keys for Parts A and B/C.

| Requested component | Student activity and implementation |
| --- | --- |
| 1.1 Image representations | Playground pixels/resolution, RGB/BGR channel arrays and views, grayscale and HSV conversion |
| 1.2 Preprocessing | Separate resize and crop lessons, paired brightness/contrast examples, Gaussian/median methods and kernel sizes side by side. Part A saves selected preprocessing |
| 1.3 Masks and morphology | HSV threshold sliders, standalone erosion/dilation, opening/closing and kernel experiments |
| 1.4 Localization | Area and circularity filters, moment centroids, boxes and comparison of contour/box centers |
| 1.5 Failure investigation | Mission 1 fixed-configuration collection, intermediate images and two diagnostic questions |
| 2.1 Classification | Frozen MobileNet V1, top-five ImageNet labels, explicit cup/coffee-mug score mapping, whole-scene limitations |
| 2.2 Detection | Frozen YOLOX, confidence and NMS controls, before/after proposals and runnable overlap demonstration |
| 2.3 Segmentation | Frozen U²-Net small salient-foreground inference, thresholded masks, reference comparisons, definitions and a two-cup semantic/instance schematic |
| 2.4 Representations | Identical scene displayed as raw image, classical mask, classification labels, detection boxes and learned foreground mask |
| 4.1 Classification evaluation | Confusion matrix, accuracy/precision/recall, explicit equations and class-balance reweighting demonstration |
| 4.2 Detection evaluation | Box IoU, confidence sweep, actual precision-versus-recall plot and all-point cup AP50. Multiclass and multi-IoU mAP are explained, not claimed as measured |
| 4.3 Segmentation evaluation | Mask IoU/Dice, disagreement image, extra/missed pixels, oversegmentation and undersegmentation |
| 4.4 Robustness | Shared 31-image collection adds blur and constructed background changes. Independent real photographs vary viewpoint, object design and background together |
| 4.5 Method comparison | Part C paired condition table, identical annotated images side by side, correct/false/missed boxes and measured processing cost |
| 4.6 Conclusions | Focused questions point to three selected conditions and one normal_1 mask example. Final synthesis distinguishes observed image errors from possible consequences for a future robot |

## Model and annotation limits

The segmenter produces class-agnostic salient foreground, not semantic cup labels or instance IDs. Its output is evaluated against the cup region desired by the robot so that students can observe task mismatch. Semantic and instance representations are explained with an explicitly labeled schematic.

Cup-presence classification sums the ImageNet scores for cup and coffee mug. This explicit mapping can miss a scene classified as espresso. Those scores are not calibrated binary cup probabilities.

The multi-object desk photograph has an approximate manually traced visible-mug polygon and handle hole, independent of model predictions. Geometry transformations keep masks aligned, and occluders remove covered pixels. Reference boxes enclose the visible source extent because the mug is clipped at the top. The 29 annotated masks include empty negative references. The two independent photographs have boxes but no pixel masks and are excluded from segmentation scoring.

Background composites and image rotations are controlled image experiments. They are not measurements of physical viewpoint changes. The independent photos offer limited transfer evidence with several changing factors. No model training is added.

## Saved evidence

Mission 1 exports the executed code, settings, preprocessing/mask/contour/box images and predictions. Mission 2 saves classifier scores, raw and suppressed box proposals, compressed foreground scores and selected thresholds. Export regenerates classification and segmentation CSVs, a box PR CSV/SVG, a confusion-matrix SVG, a quantitative summary, prediction/annotation images and manually supplied reference masks. Threshold previews reuse saved inference.
