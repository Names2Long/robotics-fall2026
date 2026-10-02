# Lab 5 implementation plan

1. **Saving and navigation:** atomic saves and previous-valid backups; unreadable-save protection; restore page, settings, selected experiments, predictions and answers; lock Course ID; isolated instructor storage; Back/Next and instructor navigation.
2. **Numerical correctness:** conventional MAD median; missing/empty-data handling; validate settings; define last-valid-sample windows and sustained response delay; fixed context safety benchmarks; independent seven-scenario evidence checks.
3. **Guided learning:** connected error/filter/fusion/delay walkthroughs; worked formulas; required hand calculations; predicted controlled experiments comparing three moving-average windows, a matched median filter, and three fusion weights (six distinct records can cover the requirements).
4. **Policy design:** explain actual decision logic; require predicted baseline and distinct revision in each context; invalidate stale tests; scenario replay, accessible tables and CSVs; distinguish dangerous-command proxies from physical collisions.
5. **Submission:** recheck current answers, seeds, settings and recorded files; invalidate only affected missions; actionable readiness checklist; synthesis/reflection exports; hashed manifest; ZIP backup; personal-fork Git submission.
6. **Environment and verification:** Windows/macOS/Linux launchers, pinned tested dependencies, CLI/UI preflight; numerical, recovery, stale-state and end-to-end tests. All testing uses temporary submission folders.

## Acceptance

- Complete the entire student route and export a current verified submission.
- No changed settings or answers can submit stale evidence.
- Restart restores work; corrupt saves cannot be silently replaced.
- All eight requested learning activities are explicit and checked.
- Starter contains only `.gitkeep`; generated submissions remain Git-trackable.

## Detailed implementation and completion record

### 1. Protect student work and make navigation explicit — implemented

Problem: earlier saves did not retain navigation/controls, and a corrupt save could become an empty attempt. Completed work could remain marked complete after an answer changed.

Changes: `lab/autosave.py` uses atomic replacement and a previous-valid backup, validates save structure, preserves unreadable originals, and blocks if recovery cannot safely proceed. `lab/session.py`, `lab/controls.py`, `lab/navigation.py`, and `app.py` restore identity, stage, prediction locks, mission controls, selected experiments, and policy histories. Course ID locks to protect assigned data. Previous/Next, Back, sidebar navigation, explicit mission saves, and optional instructor navigation do not fabricate evidence. Older experiments are archived and downloadable, not erased.

Verification: restart and navigation tests, invalid-primary/backup recovery, blocked unreadable saves, legacy migration, and selective invalidation tests.

### 2. Correct numerical and evaluation behavior — implemented

Problem: even-count MAD used the wrong middle value; empty/missing estimates could divide by zero; an isolated lucky response could understate delay. A policy threshold should not redefine the evaluation hazard itself.

Changes: `simulation/sensors.py` uses the conventional median for MAD. `simulation/filters.py` validates inputs and handles no available evidence explicitly. Window length means valid readings; missing values hold estimates. Response delay ends at the third consecutive acceptable sample. `simulation/scenarios.py` fixes evaluation safety distances by context and records every scenario trace. Independent regeneration rejects forged or stale results. Dangerous-command events are explicitly described as decision-risk proxies, not physical collisions.

Verification: exact worked outputs, even-count MAD regressions, empty/missing-data cases, invalid settings, sustained delay, all seven traces, and fixed-benchmark tests.

### 3. Close the filter/fusion learning gaps — implemented

Problem: running a few configurations did not ensure manual calculation, controlled window experiments, or multiple fusion weights.

Changes: four connected walkthroughs introduce errors, formulas with examples, fusion, and delay. Mission 1 requires a preserved prediction before revealing data. Mission 2 requires hand calculations; six distinct predicted configurations cover three moving-average windows at fixed weight, matched median/moving-average settings, and three fusion weights with otherwise identical settings. Numerical tables and CSVs complement plots. Students select recorded evidence, compare metrics, and explain the trade-offs.

Verification: missing calculations, duplicate settings, absent comparisons, and missing predictions fail checks. UI tests record the six suggested configurations through the actual controls.

### 4. Make policy design an actual tested experiment — implemented

Problem: unmodified defaults and outdated test results could satisfy a design task; aggregate scores obscured why decisions happened.

Changes: Mission 3 explains decision pseudocode and benchmarks. Both contexts require a predicted supplied baseline plus a distinct revision. Every test runs seven scenarios; results must match current controls and assigned seeds. Policies must differ in at least two justified parameters. Scenario replay offers time-series charts, decision reasons, accessible tables, and CSVs. Written explanations compare quantitative costs, stakeholders, and limitations.

Verification: stale controls, manipulated metrics, missing revision/prediction, and incomplete scenarios fail. UI tests exercise baseline/revision tests and all traces. A 100-Course-ID sweep establishes that all three missions have passing routes for the tested assignments; it is not proof for every possible ID or deployment.

### 5. Verify submission completeness and freshness — implemented

Problem: a filename-only manifest could include missing or obsolete evidence; final instructions disagreed about how to submit.

Changes: `lab/completion.py` rechecks answers, assigned data, signatures, and saved artifact hashes. Only affected missions are invalidated. Final readiness requires all current missions, identity, a 150–250-word synthesis, and a 1–300-word reflection. `lab/submissions.py` creates a hashed manifest and a current ZIP backup. Instructions consistently require a personal-fork Git commit and its URL; no automatic upload is implied. Student-generated files remain Git-trackable.

Verification: complete guide/export tests, ZIP-to-manifest hash comparisons, changed responses/settings, modified evidence, and missing artifacts. All generated test evidence is in temporary directories. The course starter remains `.gitkeep` only.

### 6. Simplify startup and document the revised lab — implemented

Changes: Linux/macOS and Windows launchers create a virtual environment, install pinned dependencies, perform preflight, and start Streamlit without Docker or ROS. The README, overview, and instructor notes describe the revised activities, timing, recovery, submission, and isolated instructor testing. CLI smoke checks and the expanded regression suite are provided.

Verification: local dependency preflight and smoke test; automated Streamlit walkthrough/mission/restart/export tests; launcher syntax checks. Cross-platform fresh dependency installations still need a platform-specific manual check; they are not claimed as tested on macOS/Linux by this Windows run.

## Final verification results

- 30 automated tests passed, including real Streamlit server startup and HTTP health, navigation/restart, recording experiments, testing revisions, recovery, and hashed ZIP export.
- Passing routes verified for 100 distinct Course IDs across all three missions.
- CLI preflight and smoke test passed with the pinned dependencies.
- Windows PowerShell and Bash launcher syntax checks passed; `git diff --check` passed.
- No generated student evidence was added to the starter: `student_submission/` contains only `.gitkeep`, and generated submissions are not ignored by Git.
- The temporary test server was stopped. No commit or push was performed as part of this implementation.
