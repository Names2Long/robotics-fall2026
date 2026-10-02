# Instructor notes — Week 5

## Design intent

This is a 3–4 hour individual lab (or two sessions). It is deliberately independent of ROS so students can focus on the epistemic problem: a robot acts on measurements, not ground truth. Each Course ID produces deterministic data, allowing students to resume work and instructors to reproduce results while discouraging answer copying.

## Suggested timing

| Activity | Time |
|---|---:|
| Introduction and four walkthroughs | 25–35 min |
| Mission 1: characterize | 35–45 min |
| Mission 2: calculate, filter and fuse | 50–65 min |
| Mission 3: design, revise and decide | 50–65 min |
| Synthesis and artifact check | 15–20 min |

## Mission evidence

Mission 1 checks estimates against computed statistics with stated tolerances. The assigned sensor emphasizes one defect—bias, noise, quantization, or outliers—but may include minor dropout and noise so diagnosis requires judgment. Ask students why a larger sample reduces uncertainty in a mean but does not remove systematic bias.

Mission 2 uses a shared truth trajectory and two complementary sensors. Sensor A is fast, noisy, and outlier-prone. Sensor B is slower and biased but steadier. Students calculate three worked outputs, then predict and log at least six distinct configurations: three moving-average windows at fixed weight, a matched moving-average/median comparison, and three fusion weights with the same filter. One six-record design is supplied; additional experiments are allowed. The maximum-error allowance is wider than the RMSE allowance because the trajectory includes a deliberate abrupt transition; delay and RMSE prevent students from “solving” the task through excessive smoothing. Delay uses the third consecutive sample within 0.15 m, not a single lucky crossing.

Mission 3 evaluates all seven cases, including conflict and simultaneous dropout, for every policy. Require a predicted baseline and distinct revision per context even if the baseline passes. A passing missing-data policy must stop or declare insufficient evidence. The assistive context has a stricter false-safe and delay criterion. Evaluation safety distances are fixed at 0.75 m (warehouse) and 0.95 m (assistive), independent of policy settings. Dangerous-command events count MOVE or SLOW at truth ≤0.45 m: they are risk proxies, not physical collisions. Scenario replay shows raw/filtered evidence, decisions and reasons. Written prompts make students identify who bears each error cost rather than treating the task as numerical optimization alone.

## Assessment suggestion (100 points)

- Mission 1 measurements and diagnosis: 25
- Mission 2 experimental method and final pipeline: 25
- Mission 3 policy performance and context comparison: 30
- Final synthesis: 15
- Artifact completeness and clarity: 5

Automated gates establish minimum completeness, not writing quality. Review whether claims cite the student's own metrics, whether parameter choices are causally explained, and whether the sociotechnical analysis names concrete stakeholders and limitations.

## Facilitation and accessibility

- Students work individually, but whole-class discussion of concepts is appropriate before work begins.
- Do not grade a particular “correct” policy parameter set; many sets can satisfy the evidence criteria.
- The CSV outputs support students who prefer external calculation tools.
- Plots are supplemented with tables and textual metric labels; completion never relies on color identification alone.
- Course ID locks once the student begins. Correcting an identity requires preserving the original attempt first; do not relabel someone else's saved evidence.

## Resetting a local attempt

Move `student_submission/` to a safe backup location, then relaunch the app. Do not delete it until the student confirms the backup is usable.

For instructor testing, prefer `WEEK05_SUBMISSION_DIR` set to an absolute temporary folder outside the repository. Never commit instructor-generated student files. `WEEK05_INSTRUCTOR_PASSWORD` enables sidebar navigation only, not completion. Automated tests always use isolated temporary folders.

## Recovery and submission

Atomic autosaves retain a previous-valid backup. Unreadable saves are preserved, not silently replaced. A recovered old-version attempt retains answers and archives older experiments for download; students need fresh predicted experiments under updated numerical checks. Changing responses or relevant policy settings invalidates only the affected mission. Removing or changing saved artifacts invalidates completion and export.

Students prepare an export only when current evidence and writing pass the readiness checklist. A manifest records file hashes and mission signatures; the ZIP is a local backup. The graded submission is the GitHub commit URL from the student's own fork. The starter contains only `.gitkeep`; generated submissions remain trackable so students can commit them. The guide does not push or upload automatically.
