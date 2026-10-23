# Lab 7 implementation and verification status

Revision date: October 21, 2026.

Implementation follows STUDENT_EXPERIENCE_PLAN.md. The required flow is now preflight, a 15-step playground, one detector investigation with Parts A/B/C, and final synthesis/submission. No replacement behavior mission has been designed.

## Requirement-by-requirement implementation

| Requested change | Status | Implementation and verification |
| --- | --- | --- |
| Remove Lab 6 references, upload comments and development-history explanations from preflight | Implemented | pages/preflight.py contains a short purpose, numbered actions, result table and troubleshooting instructions |
| Explain what preflight checks beyond opening the guide | Implemented | Actual execution on all shared images, three vision models, required assets and writable submission storage. Explicit first-run preparation. Package imports alone are not the readiness claim |
| Clarify ROS readiness | Implemented scope change | The revised required image work does not use ROS. The page explicitly does not certify ROS readiness. No ROS environment was verified in this revision |
| Original image directly after the playground starting question | Implemented | Source scene is first, with clickable selection in the pixel lesson and the original image in later lessons |
| Click-to-select pixel, synchronized sliders, BGR values and color square | Implemented, automated checks passed | Local dependency-free component, coordinate validation and source/display scaling. Python checks both slider keys and duplicate-event handling. Node checks the shipped component event script. Live browser clicking remains unverified |
| Remove confusing pixel controls from RGB channel inspection | Implemented | All three complete channel views shown together, with explanation of what grayscale channel intensity means. Grayscale is a separate topic |
| Separate resize and crop | Implemented | Distinct lessons, fixed full-scene resize examples and separately controlled rectangular crop. Playground now has 15 steps |
| Show sensible parameter alternatives side by side | Implemented | RGB and HSV channels, brightness/contrast examples, Gaussian/median kernels, and morphology kernels 1/3/9. Interactive sliders remain where spatial selection or bounds exploration is useful |
| Prevent inherited outputs/settings across playground topics | Implemented | Fresh original image on every run. Fixed prerequisite masks rebuilt and labeled. All 15 steps tested, including comparison with the original source and expected fixed morphology input after changing threshold controls |
| Repair and explain the final centroid/box topic | Implemented | Known manual teaching silhouette, explicit distinction from detector output, full scene plus enlarged region, coordinate table and visibly different rectangle/silhouette centers |
| Replace isolated coffee image with a robotics-relevant multi-object scene | Implemented | Mug, laptop, keyboard and trackpad. Assistive desk-location scenario. CC0 source provenance and independent visible-mug outline/handle-hole annotation. Top clipping and lack of depth/calibration stated explicitly |
| Explain classical evaluation values | Implemented | Shared metrics helper introduces presence counts, box counts, ratios, undefined values, IoU and milliseconds before interpretation. Candidate-table terms explained in the shared pipeline renderer |
| Explain image IDs and remove unnecessary response-count commentary | Implemented | Selector names such as normal_1 and dim_1 explained beside outputs and in the question. Questions point to the relevant mask and contour evidence |
| Explain frozen models, tasks and matching scenes | Implemented | Part B defines weights, inference, classification, detection, segmentation and identical-image comparison in plain language before use. Model-specific output explanations appear in each guided activity |
| Speed up scene/activity changes | Implemented | First preparation computes once, persists predictions by dataset/model key, and later pages reuse them. Bounded caches cover shared scenes, fingerprints, validation and decoded masks. Backup ZIP creation removed from normal rerenders |
| Explain and simplify the old fifth learned activity | Implemented by restructuring | Replaced by a separate Part C with a numbered decision workflow. Primary condition table and paired images come first. Advanced metrics live in explained expanders, not an unintroduced wall of results |
| Make comparison questions answerable from visible evidence | Implemented | Default normal/dim/occluded comparison table has both methods' correct, false and missed boxes plus timing. Same-image views are paired. Second question uses the specified normal_1 foreground example and visible mask scores. Finalization requires a saved comparison of at least three valid conditions |
| Merge classical, learned and comparison work | Implemented | One investigation page, three explicit parts, bottom previous/next controls and part selector. Compatible mission_1/mission_2 evidence keys retained |
| Scrap current Mission 3 without inventing a replacement | Implemented | Former guide page moved to extensions/behavior/guide_page.py, indexed with preserved policy/ROS components. Removed from active navigation, required checks and synthesis. Existing archived evidence remains recoverable |
| Fix related issues throughout the lab | Implemented | Introduction, final page, shared helpers, navigation, readiness, persistence migration, README, overview, annotation manifest, outline coverage and instructor notes updated consistently |
| Preserve student work and enable a fresh instructor test | Implemented | Old stage keys migrate without deleting answers. Recovery and draft exports retained. Known instructor testing data archived, not deleted. Normal submission folder contains only .gitkeep |

## Verification

- Windows Python 3.12: all 42 automated tests passed in the final run (23.961 seconds). Coverage includes model inference, all playground steps, supplied code execution, saved thresholds, three-part comparison, artifact regeneration, final readiness, restart restoration and recovery. Archived behavior logic continues to have unit coverage even though it is not assigned.
- The shipped pixel-component JavaScript passed its Node contract test for render handshake, scaled click coordinates and image-edge clamping.
- `python app.py --smoke-test` passed for both detectors on all 31 images.
- A warm persisted learned collection loaded in about 0.239 seconds in a fresh Python process on this machine.
- Before removing repeated ZIP creation, one paired-scene AppTest rerender measured 1.070 seconds. Afterward repeated runs measured 0.146, 0.149 and 0.182 seconds. These are local test measurements, not guarantees for other hardware or full browser/network latency.
- A repeated learned-collection request was tested with model inference patched to fail if called. It reused the saved results successfully.
- `git diff --check` reported no whitespace errors. Existing working changes were preserved. No commit or push was requested or performed.

## Remaining verification limits

Live browser visual verification could not be completed because the automation tab became unavailable. Do not treat automated rendering and component contract tests as proof of browser layout, actual clicking or perceived responsiveness. A short manual pilot of the pixel picker, source-image placement, plot descriptions and three-part flow remains recommended.

ROS integration was not rerun. It is outside the revised required experiment scope. Historical October 19 ROS/browser results in VALIDATION.md do not verify this revision.

## Fresh-test state

Known instructor test answers and experiments were moved recoverably to `runtime/student-experience-backup-20261021-222028`. The normal student_submission folder was verified to contain only .gitkeep. The isolated port-8502 browser test server was stopped. Its testing files remain isolated under runtime. The reusable model cache contains predictions only, not identity, answers or progress.

Restart the lab with run_lab.ps1 or run_lab.sh. The normal guide should begin at Start with empty identity and progress. Use an isolated WEEK08_SUBMISSION_DIR for future automated tests, and archive only known instructor test data before another clean manual test.
