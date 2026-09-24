# Local operation and submission storage

Lab 4 runs on the student's computer. It is not intended for shared Streamlit Cloud hosting because each run writes private progress and grading evidence to a local `student_submission/` folder.

The local workflow provides:

- one submission directory per repository clone;
- automatic saving and restart recovery;
- structured evidence tied to the student's Git history;
- an individual commit link for submission.

Students start the lab with the operating-system launcher described in the Lab 4 README. After every readiness check passes, they save the final folder, commit `week04_pid_odometry/student_submission/`, push, and submit the individual commit URL.

The repository version of `student_submission/` must contain only `.gitkeep`. Generated answers, GIFs, results, and autosaves belong to students and must never ship in the instructor starter repository.
