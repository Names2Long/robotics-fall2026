# Live vision mission implementation and verification

## Implemented groups

| Plan group | Implementation |
| --- | --- |
| 1. Original environments | Four-pillar world and straight/curved floor textures, local Gazebo materials, source attribution and CC BY-NC 4.0 license |
| 2. ROS environment | Camera-equipped Waffle, bounded images, clock and image bridges, explicit TwistStamped velocity bridge, launch locks, fresh world starts and live preflight |
| 3. Shared perception and control | HSV masks, largest contours, resolution-independent centroids, turn-only search/center/hold, proportional line tracking, loss stop and latched red finish cue |
| 4. Motion safeguards | Freshness checks, invalid-image stop, bounded commands, clean-exit stop and independent monotonic command-loss watchdog |
| 5. Recorded evidence | Settings, capture stamps, decisions, commands, outcomes and final diagnostic images in portable reports. Interrupted attempts can be retained. Export creates timelines, images and summaries |
| 6. Student workflow | Mission 1 static investigation preserved, installed-software checks in initial preflight, simulation startup and live checks at the beginning of Mission 2, reset and live checks in Mission 3, saved attempts, focused questions, readiness and final export |
| 7. Verification and clean retest | Unit and Streamlit workflow tests, ROS build, real Gazebo camera runs and isolated ROS watchdog test. Test reports archived outside active evidence and guide restarted |

## Verified

- All three ROS packages build successfully in the running course Jazzy container.
- Live preflight passes with received changing camera frames, advancing clock, subscribed TwistStamped bridge and independent guard.
- Actual Gazebo pillar search centers red, green, turquoise and blue, completes in 19.4 simulation seconds and commands zero afterward.
- Straight practice tracks the line during a deliberately time-limited 10-second run, with no line-loss event. Practice has no finish marker.
- The earlier supplied-controller baseline completed the curved track in 164.1 simulation seconds at 0.12 m/s. The revised code-based mission deliberately does not start with that tuned configuration.
- The current weak-gain starter was tested for 50 simulation seconds and showed a large off-center error on a bend. A separately edited Python program completed the full track at the new 0.16 m/s maximum in 127.9 simulation seconds and stopped at the finish. These are controlled simulation observations, not guarantees across settings or physical robots.
- Isolated ROS integration checks steering sign, pillar forward-speed prohibition, camera-loss stop and watchdog stop after controller loss.
- 60 automated tests pass, including all 16 playground steps, the four-operation comparison, runnable Python reference, Part A response gate, code-driven steering and fixed safeguards, exact shared reflection wording, retained robot reports, restart recovery and final artifact regeneration.
- The full initial preflight passes in the course container with Gazebo stopped. Local guides without ROS report image readiness only. Progress saved on the removed setup page migrates to Mission 2 without losing answers.
- The image-view processes launch successfully in the course virtual desktop. A full visual student walkthrough and workload pilot remain recommended.

The Gazebo test caught and fixed a duplicate-pose bug in the installed model adaptation. A regression test now requires one robot pose. The launcher closes inherited lock descriptors so switching worlds does not remain blocked by an orphaned child.

## Current student-experience revision

- The playground ends with a downloadable, documented `scripts/playground_reference.py` covering every operation. Its CLI produces 39 intermediate images and measurements.
- Mission 1 uses bottom back/next buttons only. Both Part A responses are needed before B or C, including after restart.
- Mission 3 uses the saved `student_submission/line_following/controller.py`, loaded by the ROS node. Its constants and arithmetic steering function are edited on the page. Separate Practice and Track panels explain import requirements and repeat the Terminal 3 viewer command. Each report retains its exact code, and new code-based submissions require two different track programs. Old reports remain readable.
- The fixed node handles freshness, missing observations, finish detection and command bounds. Invalid steering computations stop at CODE_ERROR. Arbitrary imports and calls are not supported in the small steering editor.
- One technical synthesis connects all three missions. The separate deployment checklist is removed from the page, readiness and required export files. Existing responses remain preserved. The course reflection uses exactly the earlier labs' five prompts and 300-word instructions.

## Reproduce

From the lab directory in the course virtual desktop:

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install
cd ..
bash scripts/launch_vision_world.sh pillars
```

In another terminal in the same directory:

```bash
bash scripts/check_vision.sh
bash scripts/run_vision.sh pillar_search pillars
```

Stop controller and world before switching to practice or track. Use the corresponding line controller command shown in the guide.

For the isolated watchdog regression, with no physical robot connected:

```bash
source scripts/ros_env.sh
export ROS_DOMAIN_ID=128
python3 scripts/check_live_control.py
```

Normal test commands remain `python -m unittest discover -s tests -v` and `node --test tests/test_pixel_component.cjs`. Student answers are never required to meet a success score. Readiness requires retained camera evidence for the four-color request and both line worlds, plus explanations.

Test artifacts are recoverable under ignored `runtime/instructor_archives`. The normal `student_submission` directory contains only `.gitkeep` for a fresh instructor start. Model caches are retained for responsiveness and do not contain student answers.
