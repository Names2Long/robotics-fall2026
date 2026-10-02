# Lab 5 — Sensors, Noise, and Uncertainty

An individual Streamlit lab connecting imperfect measurements, estimation, and decisions about people and robots. It runs locally without Docker, Gazebo, or ROS. Use Python 3.12 or newer and an internet connection for the first dependency installation.

## Start the guide

From the repository root on Linux/macOS:

```bash
cd week05_sensors_uncertainty
bash run_lab.sh
```

On Windows, in PowerShell:

```powershell
cd week05_sensors_uncertainty
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_lab.ps1
```

The launcher creates a local virtual environment, installs pinned dependencies, checks the environment, and starts the guide. Leave the terminal running; open the local URL it displays. Do not use `sudo`. If Linux cannot create a virtual environment, install the distribution's Python venv package first.

Alternatively, create and activate a Python virtual environment yourself, install `requirements.txt`, then run:

```bash
python app.py --preflight
python -m streamlit run app.py
```

## Student route

1. Four connected walkthroughs explain sensor errors, worked filter outputs, weighted fusion, and response delay. Previous/Next and sidebar navigation support review.
2. Mission 1: predict before seeing your assigned 240-reading dataset; calculate statistics, diagnose the sensor, and explain consequences.
3. Mission 2: calculate moving-average, median, and fusion outputs; predict and record at least six distinct configurations covering three moving-average windows, a matched median comparison, and three fusion weights. Measure error, availability, and sustained response delay; justify a selected passing pipeline.
4. Mission 3: predict and test a baseline and a distinct revision for both warehouse and assistive settings. Every policy runs all seven scenarios. Compare quantitative metrics, inspect individual decisions using scenario replay/tables, and explain context-dependent choices and limitations.
5. Write a 150–250-word technical synthesis and a separate 1–300-word individual reflection. Check readiness, prepare the verified submission, and download its ZIP backup.

The delay measure requires three consecutive acceptable samples; available held estimates are not necessarily fresh evidence. Policy safety benchmarks are fixed by context, independent of the student's stopping threshold. Dangerous-command events are a risk proxy, not physical collisions.

## Saving and recovery

Answers, settings, experiment histories, selected configuration, predictions, and location save locally. The Course ID determines repeatable data and locks once work begins. Save predictions before testing and explicitly check/save each mission; the guide does not automatically hide its results. Local autosave is not a remote backup.

An unreadable primary autosave recovers the previous valid backup where possible. If both saves are unreadable, the guide stops without replacing them. Keep the folder intact and contact the instructor. Earlier-version experiments are archived and downloadable; answers are retained, but the revised requirements need new experiments and checks. Changing an answer or relevant policy setting invalidates affected completion; other missions are retained. Changed evidence requires a fresh export.

## Submit your own work

The starter contains only `student_submission/.gitkeep`. Generated student submissions are intentionally Git-trackable. The submission includes identity/autosave, measurements, calculations, experiment histories, plots, all seven policy traces for both contexts, explanations, synthesis, reflection, and a SHA-256 manifest. The ZIP is a backup, not an automatic upload.

In your personal fork, from the repository root:

```bash
git status
git add week05_sensors_uncertainty/student_submission
git commit -m "Submit Lab 5"
git push origin main
```

Inspect the GitHub commit's files and submit that commit URL through the course submission system. If Git reports conflicts, stop and preserve your work before asking for help.

## Instructor verification

```bash
python app.py --preflight
python app.py --smoke-test
python -m unittest discover -s tests -v
```

Tests use temporary submission directories, never the starter. For instructor trials, set `WEEK05_SUBMISSION_DIR` to an absolute folder outside the repository before starting. Optional instructor navigation uses `WEEK05_INSTRUCTOR_PASSWORD`; it bypasses navigation only, never evidence checks. See [instructor notes](content/instructor_notes.md) and the [implementation plan](content/improvement_plan.md).
