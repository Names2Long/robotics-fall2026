# Lab 7 revision coverage

Historical coverage snapshot from the October 19 revision. The current student flow and requirement-by-requirement implementation record are in STUDENT_EXPERIENCE_PLAN.md and STUDENT_EXPERIENCE_STATUS.md. In the current revision, the playground has 15 steps, detector work is one three-part investigation, and the behavior mission is archived rather than assigned. The historical behavior recommendation below is intentionally deferred at the instructor's request.

## Seven recommendations

1. Student experience: bottom navigation, free revisiting, preserved drafts, no tutorial answers, plain-language numbered guidance, parameter tables, visible save failures and a submission checklist.
2. Image playground: 14 sequential steps introduce coordinates/resolution, RGB/BGR and grayscale/HSV, preprocessing, standalone erosion/dilation, opening/closing, area/shape filters, centroids and boxes. Controls update runnable code and later steps unlock after execution.
3. Mission 1: students run the supplied complete detector, tune its parameters on a visibly identified practice photograph, evaluate one fixed configuration and answer two questions. The displayed code is the code used by the batch evaluator. The executed code is saved with the evidence. Expression-entry fields have been removed.
4. Valid comparison: the two cup detectors use identical images and category. Additional frozen classification and class-agnostic segmentation activities explain their different output tasks. Evaluation includes confusion matrices, class balance, NMS, mask IoU/Dice, a true box PR curve, AP50, timing and condition comparisons. See OUTLINE_COVERAGE.md for every added component.
5. Detection versus behavior: student-authored transition expressions, selected detector score and geometry, freshness safeguards, ten time sequences, left/right steering, center instability, separate-unit plots and distinction between policy commands and guarded ROS output.
6. Deployment readiness: tested and missing conditions, unequal-performance questions without unsupported demographic claims, privacy, fallback behavior, synthesis and individual reflection.
7. Saving and release checks: atomic save retries for transient locks, recovery snapshots, export regeneration, required-file checks, manifest hashes, isolated testing, workflow tests and live ROS checks.

## Proposed content location

| Content | Where students encounter and apply it |
| --- | --- |
| Detections as uncertain evidence | Introduction, wrong-contour examples, persistent false-target trial |
| Coordinates and BGR/RGB/HSV | Playground pixel probe and channel views |
| Masks, contours, boxes and center calculations | Sequential playground runs and the supplied Mission 1 detector code |
| Parameter sensitivity | Worked tuning instructions and linked intermediate images |
| Controlled robustness | Fixed settings across transformed positives and matching negatives |
| Frozen inference and outputs | Mission 2 explanation, candidate records and annotations |
| Shared category and images | Dataset fingerprint and same image IDs for both detectors |
| Precision, recall, false positives and threshold tradeoffs | Worked calculation, sweeps, condition tables and saved metrics |
| Box correctness and IoU | Reference rectangles, localization counts and comparison tables |
| Image-space steering | Coordinate example, steering sequence and angular-command plot |
| Student state transitions | Conditional-expression editor, immediate checks and actual policy execution |
| Temporal reliability | Confirmation, missing, stale, alternating and unstable-center scenarios |
| Deployment limits | Four short readiness responses and final synthesis |
| Individual reflection | Separate final response, maximum 300 words |

## Scope boundaries

Mission 1 is a code-execution and parameter-design exercise using a complete supplied program. Mission 3 uses a constrained transition-expression scaffold. The supplied surrounding code handles file I/O, timing and fixed safety constraints. This keeps the lab to three missions.

Two independent photographs are a limited transfer check, not a representative benchmark. Different viewpoints and cup shapes are confounded in those photos. Controlled image rotation is not physical viewpoint change. Reference boxes are approximate, especially under occlusion.

Behavior evaluation is a time-sequence simulator with optional real ROS message flow, not closed-loop Gazebo navigation or a physical deployment test. Image area is not calibrated distance. A persistent false detection remains an intentional failure case for analysis.

Earlier answers are retained. Older experiment evidence has a different dataset fingerprint and must be rerun. Draft export remains available for incompatible evidence. No student data is packaged in the course submission directory.
