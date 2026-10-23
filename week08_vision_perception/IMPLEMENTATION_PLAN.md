# Lab 7 implementation plan

Implementation coverage is recorded in [REVISION_COVERAGE.md](REVISION_COVERAGE.md). Actual verification and scope limits are recorded in [VALIDATION.md](VALIDATION.md). The completed revision includes a sequential runnable-code playground, explicit local preflight, a supplied Mission 1 detector with parameter controls, independent transfer images, reference-box metrics, selected-detector policy integration and ten temporal scenarios.

Implementation status: complete for the scope below. Validation results and deliberate experiment limits are recorded in `VALIDATION.md`.

The subsequent outline expansion is mapped component by component in `OUTLINE_COVERAGE.md`. It adds 14 playground steps, three frozen vision models, five Mission 2 activities, mask annotations, NMS exploration, confusion/class-balance analysis, PR/AP50, mask IoU/Dice and portable evaluation reports while retaining three missions.

## 1. Shared experiment and evidence model

- Give both detectors the same versioned, labeled image collection and target class.
- Keep a baseline tuning image separate from evaluation images. Include target-absent examples.
- Implement reusable classical image processing with raw mask, cleaned mask, candidate contours and selected box.
- Pin a pretrained artifact and document its source, license, labels, preprocessing and checksum. Never train during the lab.
- Store predictions per image with settings, dataset fingerprint and model fingerprint. Compute threshold sweeps from individual scores.
- Recompute metrics from saved predictions. Report image-level presence metrics explicitly and show condition breakdowns.

## 2. Guided student experience

- Introduce Lab 7 and its three missions with goals, expected observations and evidence.
- Replace the concepts questionnaire with a compact interactive image playground covering coordinates, RGB/BGR, HSV, masks, morphology, contours, boxes and image centers.
- Put inference guidance in Mission 2 and policy guidance in Mission 3.
- Provide complete runnable commands, explicit terminal setup and bottom Back/Continue controls.
- Remove roster identifier and avoid written tutorial requirements, arbitrary answer lengths and accuracy gates.

## 3. Experiments and application

- Mission 1 locks a configuration, evaluates the shared collection, preserves intermediate images and asks two focused diagnostic questions.
- Mission 2 runs frozen inference, retains a threshold sweep and compares both methods on matching images. Students select a detector and justify it for a stated task.
- Mission 3 uses one policy implementation in both evaluation and ROS. Add capture-time freshness, message timeout, temporal confirmation and explicit stopping behavior.
- Provide reproducible sequence trials for reliable, low-confidence, absent, delayed, false, occluded, alternating and close-target evidence. Distinguish observation tests from physical deployment claims.
- Make policy decisions, commands, errors and delays visible. Keep physical-distance claims out of uncalibrated box-area tests.
- Add Deployment Readiness to the existing synthesis and retain the course reflection.

## 4. Persistence and submission

- Save edits before navigation and restore stage, identity, answers, configurations and evidence.
- Use atomic writes, recovery snapshots and protection for unreadable saves.
- Allow draft saves and ZIP backups at any point. Validate current evidence and write the current synthesis and mission answers at export.
- Automatically use local evidence. Keep manual imports optional.
- Use an isolated submission directory for tests so the instructor starts fresh.

## 5. Verification and release notes

- Test image transformations, detector outputs, exact script entry points, per-image metrics and matching dataset checks.
- Test sequences against the actual policy, including stale capture timestamps and alternating evidence.
- Test navigation, restart, corruption recovery, changed evidence and ZIP export.
- Run the guide with Streamlit's app testing facilities and inspect a browser when available.
- Document actual validation and any remaining ROS or model limitations. Do not claim physical deployment validation.
