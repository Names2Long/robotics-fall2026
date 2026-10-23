# Lab 7 validation

The following is the historical October 19 validation record, not verification of the October 21 student-experience revision. Current tests, performance measurements and the incomplete live browser visual check are recorded in STUDENT_EXPERIENCE_STATUS.md. ROS was not retested or required by the October 21 image investigation.

Validated on October 19, 2026.

- Windows Python 3.12: all 35 unit and workflow tests passed. The workflow runs all three frozen models, exercises 14 playground steps and five Mission 2 views, changes and saves NMS/classification/segmentation thresholds, completes all missions, exports, restarts and validates restored work. Numerical checks cover box AP, mask IoU/Dice, NMS, manual-mask alignment and preprocessing/shape filters alongside persistence and behavior checks.
- Docker course environment, ROS 2 Jazzy: all three ROS packages built with colcon.
- ROS preflight: every check passed, including model checksum and real inference.
- Required local preflight also passed inside the course container. Package checks import the working modules so apt-installed OpenCV is accepted alongside pip-installed OpenCV.
- Live ROS detectors: the classical and learned nodes both returned reference-cup detections and annotated images while preserving the source timestamp.
- Live ROS policy: confirmed fresh observations enabled approach, missing and stale observations stopped motion, and fresh evidence restored approach.
- The documented ROS policy launch progressed through all ten scenarios, including left/right steering and unstable target position. The publisher, behavior node and command guard all exited cleanly on the test's timed SIGINT.
- Browser: checked footer navigation resets the page scroll to zero, playground steps reset to the top, controls and code appear side by side, and the Run button produces image outputs. Automated Streamlit tests cover all 14 playground steps and the expanded submission path.
- Expanded browser review verified actual classifier labels/confusion counts, nine accepted proposals reduced to one by NMS on normal_1, and learned foreground versus manual cup masks with agreement/error colors and IoU/Dice. The semantic/instance distinction uses an explicitly identified schematic.
- Normal `student_submission` contains only `.gitkeep`. Test submissions use separate ignored directories.

## Deliberate limits

The 31 evaluation images combine controlled derivatives, condition-matched negative controls and two independent photographs. This is a small teaching collection, not a representative benchmark. Rotation and background composites are image transformations, not physical viewpoint measurements. Models remain frozen. The classifier's explicit cup/coffee-mug mapping and class-agnostic foreground segmentation have different output tasks. Mask scores use 29 approximate visible-cup references and exclude the independent photos. Cup AP50 is not multiclass or multi-IoU mAP.

The playground executes displayed code one operation at a time. Mission 1 supplies the complete detector and asks students to run it, tune parameters and diagnose results. Mission 3 retains a policy transition expression. It uses the selected detector's saved result, then injects controlled observation changes to isolate policy behavior.

Mission 3 evaluates time sequences of observations and resulting commands. It is not a closed-loop Gazebo navigation task and does not validate collision avoidance, physical stopping distance, human safety or demographic fairness. The ROS demonstration uses isolated topics. A persistent confident false target is intentionally a failure the policy can exhibit.

## Release checks

The bundled ONNX artifact is explicitly included by Git rules. Student answers and evidence are not blanket-ignored. Instructor backups, runtime output, virtual environments and build products are ignored. No commit or push is performed as part of this implementation task.
