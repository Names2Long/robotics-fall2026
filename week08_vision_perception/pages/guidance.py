"""Plain-language worked examples placed at the point of application."""


def intro(st):
    st.markdown("""### How to work through this lab
1. Run preflight, then work through the image playground one operation at a time. Use the controls and Run buttons. You do not submit tutorial answers.
2. In Part A of the detector investigation, tune and run the supplied OpenCV detector. Evaluate fixed settings across the collection and explain its failures.
3. In Part B, inspect frozen classification, detection and foreground segmentation. In Part C, compare the same images side by side and save your recommendation.
4. Begin Mission 2 by starting the pillar simulation and checking live camera frames, simulation time and the guard. Complete pillar search and Mission 3 line following. Save settings before restarting a controller and keep its recorded attempts in the guide. Repeat the live check after each world reset.
5. Write one technical synthesis connecting all three missions, then the shared course reflection and submission checklist.

The first mission studies saved images. The next two missions run camera-in-the-loop robot experiments in the course virtual desktop.

For example, wood on the desk may pass the same color rule as the mug. A detector can be wrong about identity even when it draws a plausible box. Image coordinates alone do not supply depth or a safe grasp pose.

Answers save when an edit reaches the application, usually when you leave the field. Look for the local-save message. Experiment results save when you press their run/save buttons. Final exported writing is refreshed by Save draft or Finalize. Save a draft and download a ZIP before updating the repository. Your work is in `week08_vision_perception/student_submission`. A ZIP is a backup, not a Git submission.
""")




def mission2(st):
    st.markdown("""### What the output means
Inference applies already-trained weights to an image. Frozen means those weights never change here. A candidate such as `cup, score 0.70, box [100, 40, 80, 60]` says the model proposes a cup in that rectangle. At threshold 0.50 it is accepted. At 0.80 it is rejected. Overlapping candidates can describe the same object, so the detector keeps a stronger candidate and suppresses nearby duplicates. This is not proof of identity.

### Read the measures before choosing a method
TP means target present and a prediction accepted. FP means target absent but a prediction accepted. FN means target present but no accepted prediction. TN means target absent and no accepted prediction. These are **image-presence** counts.

If eight of ten accepted detections are on target-present images, precision is 8/10 = 0.80. If twelve images contain the target and eight are detected, recall is 8/12, about 0.67. Precision asks how trustworthy accepted detections are under this test. Recall asks how many target-present images were found. False-positive rate is FP/(FP + TN), the fraction of absent images that triggered a detection. Blank values mean there were no examples in the denominator, not a perfect score.

The separate **box metrics** require intersection over union (IoU) of at least 0.50 with the reference cup. IoU is overlap area divided by the total area covered by either box. A box on the plate may pass image-presence scoring but fail box matching. An unmatched prediction is a box FP, and a cup without a matched box is a box FN. Extra boxes also count as FP. Manual reference boxes are approximate. Under occlusion they describe the full cup extent, and rotated references enclose its transformed extent.

### Make a fair comparison
1. Finish and save Mission 1 first. Keep its configuration fixed while comparing.
2. Run the frozen detector once on the same images. No training is performed.
3. Compare low, medium and high thresholds using the sweep and the same annotated image. Lower thresholds can recover misses but also admit false detections. If counts do not change, report that no candidate scores crossed the tested thresholds.
4. Inspect at least three conditions, one absent example, and the independent photos. Compare image-presence and box scores. Processing milliseconds measure inference work, not camera-to-action delay.
5. Choose the method for a robot seeking any cup in these examples. The methods do not identify one particular person's cup. Save your chosen method, threshold and comparison before continuing.

Changing the threshold is a preview until you press Save selected threshold and comparison. If you rerun Mission 1, review and save this comparison again. Independent photos improve the check beyond one image, but are still far too few to establish reliability in a deployment population.
""")


def mission3(st):
    st.markdown("""### From an image to a decision
For a 480-pixel-wide image, the image center is x = 240. A target at x = 360 has normalized error 0.5. A target at x = 120 has error -0.5. Positive ROS angular velocity turns left, so a right-hand target needs a negative turn command. Centering is not measuring distance.

### Write a transition rule
Enter one Python conditional expression that returns `'SEARCH'`, `'APPROACH'` or `'STOP'`. Available Boolean names are `usable`, `confirmed` and `centered`. `loss_action` is your selected action for a fresh report without a reliable target. You may use `and`, `or`, `not`, and `value_if_true if condition else value_if_false`.

For example, `'APPROACH' if centered else 'STOP'` refuses to turn toward an off-center target. Test why that may stall. Design your rule to allow centering if appropriate and choose what to do when usable evidence disappears. A state expression controls requested behavior, not raw velocity.

Fixed safeguards take priority: stale or absent messages, invalid data, an image-area goal, and insufficient confirmation stop motion. APPROACH is never permitted for an unusable observation. SEARCH may rotate only after a fresh unusable report or a confirmed usable observation. These constraints cannot be bypassed by the expression.

| Control | Plain-language meaning |
| --- | --- |
| Minimum confidence | Reject weak detections. A classical rule has binary score 0 or 1, not learned confidence |
| Maximum capture age | How old an image may be. At 0.6 s, an image captured 0.8 s ago cannot justify motion |
| Consistent frames | How many distinct recent detections are required. At 10 Hz, waiting for three instead of one adds about 0.2 s |
| Image-area goal | Stop when the box occupies this fraction of the image. This is not a physical distance |
| Center tolerance | How far from image center still counts as centered. A tolerance of 0.1 spans 24 pixels each side in a 480-pixel image |
| Maximum center change | Reset confirmation after an abrupt normalized-position jump. A low limit rejects unstable detections but can delay a real moving target |
| Fresh unusable report | Choose STOP or SEARCH when a new message reports no reliable target |

No arriving message and a fresh no-target message are different. The first may mean a broken camera link and must time out to STOP. The second says the camera is reporting but cannot currently find a usable target.

### Run and inspect
1. Save your detector choice in Mission 2. The guide uses that detector's saved score and box for the visible sequence. Other sequences explicitly inject controlled failures or geometry changes.
2. Write your transition rule and select parameters. Run all ten short sequences.
3. Inspect `steering` for left, right and centered targets. Inspect `unstable_center` to see confirmation reset after jumps. Also inspect missing, stale and false-target trials.
4. Change one rule or setting, rerun, and compare with the previous saved policy.

An incorrect approach is a forward-moving step when the injected ground truth says the target is false. Stopped opportunity steps include intentional waits when a usable centered target could have been approached. Initial action delay measures time from the first such opportunity to forward motion. A blank delay means no forward motion began. Constraint violations include turning on stale evidence, not just forward motion. One step is 0.1 s.

The plots separate confidence, image position and command units. Timelines show **policy commands before the ROS guard**, not measured robot motion. The optional ROS exercise observes the guarded output. Persistent confident false targets can fool either policy even when every timing safeguard passes.
""")


def final(st):
    st.markdown("""### Finish without losing your work
1. Use named results from all three missions to answer the single technical synthesis question. Separate what you observed from what you infer.
2. Write the separate course reflection of no more than 300 words using the shared prompts.
3. Review readiness. Use the navigation buttons to fix missing answers, identity, or experiments.
4. Press Finalize verified submission. This recreates required evidence files and checks they exist before writing a complete manifest.
5. Open `student_submission` and check `student_implementation.json`, the detector evidence and explanations, classification and segmentation CSVs, `detection_pr.svg`, the `pillar_search` and `line_following` attempt CSVs and images, `final_synthesis.md`, `final_reflection.md`, and `manifest.json`. Mission 1 Part A uses the `mission_1` storage folder. Parts B and C share `mission_2`. The storage names preserve compatibility. The robot missions use separate descriptive folders.
6. Download a current backup after saving. Commit and push the submission folder in your own repository. Check the actual files on GitHub, then submit the commit link.

If saving fails, keep the page open and copy any unsaved text somewhere safe. Save a draft whenever finalization is blocked. Do not delete your work or reset the repository to fix a readiness message. Send the exact message to your instructor.
""")
