# Lab 7: Computer Vision and Learned Perception (Week 8)

An assistive robot needs to locate a mug among desk equipment. This individual lab investigates what image operations and trained models can establish about that location, and what evidence is still missing before a robot could act safely.

## Start

From the repository root, use the local launcher with Python 3.12 or newer:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\week08_vision_perception\run_lab.ps1
```

Linux/macOS:

```bash
bash week08_vision_perception/run_lab.sh
```

The guide opens at http://localhost:8501. Leave the terminal running. Mission 1 runs locally. Missions 2 and 3 require the course ROS 2 Jazzy and Gazebo container and virtual desktop. Use `scripts/ros_course.ps1 lab week08_vision_perception` or `bash scripts/ros_course.sh lab week08_vision_perception` to host the guide in the container with the same shared repository. No personal camera, training or model download is required. The image preflight and the live ROS check test different requirements.

## Student route

1. Build the Lab 7 ROS workspace in the course virtual desktop after updating, then run preflight. It checks installed ROS 2 and Gazebo software and the built workspace without launching a simulation. It also loads the full image collection, executes all three models, prepares reusable predictions and tests saving. A local guide without ROS can verify the image activities only, and explicitly reports robot software as unverified.
2. Complete 16 progressive playground lessons. The original multi-object scene appears first. Select a pixel by clicking or using sliders, inspect color channels, then examine grayscale, HSV, resize, crop, brightness, contrast, smoothing, thresholding, morphology, contours and geometric centers. A dedicated comparison displays erosion, dilation, opening and closing on the same mask and kernel. Each lesson starts from the original scene or an explicit fixed mask. Download the documented, runnable scripts/playground_reference.py at the end.
3. Complete one detector investigation in three parts:
   - **A. Classical:** tune the supplied code, run one fixed configuration on 31 images, inspect intermediate results and explain two examples.
   - **B. Learned:** load the prepared model outputs, then inspect classification, detection, foreground segmentation and their differences in four guided activities.
   - **C. Comparison:** compare at least three named conditions using paired counts and identical images side by side. Inspect one specified foreground example, save a detector recommendation and answer focused evidence questions. Further metric details are available in explained expanders.
4. Start the simulation at the beginning of Mission 2, then run the live camera, clock, command bridge and guard check. Installed software and live simulation readiness are separate checks.
5. Mission 2 uses camera HSV masks and centroid error to center four colored pillars without forward motion. Save settings and retain an all-four-color attempt, including failures.
6. Mission 3 has separate Practice and Track parts. Edit and save the actual Python settings and steering expression on the page, then restart the ROS node to load them. The starter gain is deliberately weak and the starting forward speed is 0.16 m/s. Import a practice attempt before starting Track. Retain two track experiments with different programs. Each launch recreates the robot and environment. Camera freshness and command guards remain outside the editable code.
7. Answer one technical synthesis question across the three missions and write the separate course reflection using the shared five prompts and 300-word limit. There is no separate deployment checklist. Finalize, inspect your submission, download a backup, then commit and push your own submission folder and submit the commit link.

The former canned behavior activity remains archived in [extensions/behavior](extensions/behavior/README.md). The new missions use actual Gazebo camera feedback instead. Launch and controller instructions are integrated into the guide. Run only one world and controller at a time. Each script sources the environment and uses `GZ_PARTITION=lab7_vision`. Stop the controller with Ctrl+C before resetting a world. The independent guard clamps speeds and stops after command loss. This is not a physical safety certification.

Original line artwork and pillar layout credit Tom Howard and the University of Sheffield. See [asset attribution](assets/robot_worlds/README.md) for the CC BY-NC 4.0 source license.

## What the outputs mean

Both cup detectors receive identical pixels and the same reference annotations. The mug belongs to their cup category. Classification gives whole-image labels without location. Detection proposes cup boxes. The U²-Net foreground model marks salient regions without object labels or separate instance IDs. MobileNet V1, YOLOX nano and U²-Net small have fixed pretrained weights. Threshold changes do not train them.

The 31-image collection contains controlled variants, matched synthetic negatives and two independent photographs. Conditions include brightness, blur, occlusion, image rotation, apparent size and constructed background changes. Rotation is not a new camera viewpoint. Independent photos vary several factors together. The collection is a teaching aid, not a generalization or demographic-fairness benchmark.

Image-presence counts and correctly located box counts are separate. IoU measures overlap, with 0.50 required for a matching box. Box precision and recall expose false boxes and missed mugs. The detailed views include a threshold sweep, one-class cup AP50, classification confusion matrix, and foreground-mask IoU/Dice. Time is saved processing time, not robot response time or sustained FPS. Scores have no minimum accuracy gate.

The source photograph is Ryan Riggins' CC0 multi-object desk scene. The mug is clipped at the top. References cover only its visible extent. Source, license, annotation scope and changes are documented in [assets/conditions/TABLETOP_SOURCE.md](assets/conditions/TABLETOP_SOURCE.md). A silhouette lesson uses an explicit teaching annotation so it does not confuse geometry with detection success.

## Saving and compatibility

Answers save when edits reach the application. Results save through experiment buttons. Save a draft before downloading a ZIP. Finalization regenerates and checks the artifacts before writing a complete manifest. Review the actual files on GitHub after pushing. A ZIP download is a backup, not a Git submission.

Mission 1 Part A retains the `student_submission/mission_1` evidence key. Parts B and C retain `mission_2`. These are storage names, not additional missions. Live missions use `pillar_search` and `line_following` to avoid collisions with old saved data. Runtime reports are imported with Keep this attempt in my submission. Export regenerates command CSVs, diagnostic images and summaries from the retained reports. Earlier answers and archived behavior evidence remain recoverable. Do not reset or delete student work to resolve a readiness message.

Predictions are computed once and saved under ignored `runtime/model_cache`, keyed to the images and model hashes. Scene generation, fingerprints, segmentation decoding and threshold-dependent validation use bounded caches. Scene selection and guided navigation do not run inference. The first preparation can take longer than later visits.

## Maintainer verification

```bash
python -m unittest discover -s tests -v
python app.py --smoke-test
```

Tests use temporary submission directories under ignored `runtime/test_scratch`. The distributed submission folder should contain only `.gitkeep`. For instructor retesting, archive only known testing data and restart the guide so browser session state cannot restore an old test. Preserve actual student submissions.

Implementation plan and current verification results: [STUDENT_EXPERIENCE_PLAN.md](STUDENT_EXPERIENCE_PLAN.md) and [STUDENT_EXPERIENCE_STATUS.md](STUDENT_EXPERIENCE_STATUS.md).
