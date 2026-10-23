# Lab 7 student-experience revision

## 1. Workflow and preservation
- Replace the three-mission student flow with one detector investigation with three parts: classical, learned representations, comparison.
- Remove the old behavior mission from navigation, required checks and synthesis. Preserve its implementation as an archived extension, not a required exercise.
- Preserve earlier response/evidence keys so saved work remains recoverable. Archive instructor test submissions and restart with empty testing state after verification.

## 2. Environment and source scene
- Explain only checks relevant to the required experiments. Verify actual model execution, shared assets and disk writes, not just imports needed to open Streamlit.
- Clearly distinguish a working guide from a checked ROS environment. Do not claim ROS readiness for Python-only experiments.
- Use a multi-object tabletop scene with an explicit assistive/table-clearing use case, provenance and independently defined annotations. Keep the target category consistent across detectors.

## 3. Progressive playground
- Show the original scene immediately after the starting question.
- Add click-to-select pixel coordinates synchronized with sliders and a BGR color swatch.
- Remove irrelevant pixel controls from channel inspection. Explain channel grayscale views.
- Separate resize and crop into distinct lessons.
- Compare sensible parameter choices side by side, especially smoothing and morphology.
- Start every topic from the same original scene. Show fixed prerequisite masks explicitly, without inheriting prior experimental settings.
- Make the final centroid/box lesson show an identifiable selected region, coordinates and the two centers explicitly.

## 4. Detector investigation and explanations
- Explain image IDs, test conditions, counts, latency and overlap measures at their first use.
- Introduce frozen weights, classification, detection and foreground segmentation in plain language.
- Precompute and persist model outputs once. Cache immutable scene generation, fingerprints, previews and threshold-dependent validation, with bounded caches.
- Split the comparison into a small primary side-by-side workflow and optional detailed metrics. Give each table/graph a question, reading instructions and limitations.
- Provide a three-condition comparison table, paired images and focused written questions that point to their evidence.

## 5. Consistency, verification and handoff
- Update introduction, navigation, completion, final export and course documentation together.
- Retain safeguards for autosave, drafts and recovery. No accuracy gate.
- Test every playground step, click-coordinate validation, independent inputs, cached rerenders, merged flow, persistence and final export.
- Record implementation status and measured verification results per group.
