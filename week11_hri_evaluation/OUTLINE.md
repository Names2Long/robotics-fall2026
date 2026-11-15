# Lab 10 outline

The individual lab uses a TurtleBot3, ROS 2 Jazzy, Gazebo, the course browser guide, and local speech recognition. The scenario is delivering a red or blue cup from a marked station to a person. Loading and transfer are represented by a simulated tray state. The robot physically drives between the stations in Gazebo.

## Setup

Launch the lab through the course launcher. In the virtual desktop, start the room and ROS interaction controller. The preflight page checks fresh robot odometry, microphone capture, local transcription, and saving. The guide shows the same live robot pose as Gazebo.

## Guided activity 1. From speech to a shared goal

Teach intended speech, transcription, parsed events, target selection, clarification, and confirmation one stage at a time. Compare a clear request, an ambiguous request, a misheard color, and a refusal misheard as permission. Use the student's microphone-check transcript as another example. Draw the candidate stations and highlight the relevant interaction phase.

## Guided activity 2. When may the robot complete a handover?

Explain arrival, offering, readiness, and transfer separately. Students start a blue-cup teaching trace, send readiness too early, and advance the diagram through the trip. At the offer they compare readiness, timeout, and cancellation. Show the robot marker, phase diagram, tray and transferred-cup values, and event trace throughout.

## Guided activity 3. Repair a readiness rule in the guide

Explain the faulty condition and the expected behavior before showing editable Python. Students run the starter checks, find the first unexpected transition, edit and save the readiness guard on the page, then rerun it. Normal transfer and early or missing readiness must pass. Explain why cancellation remains for Mission 1.

## Guided activity 4. Who controls the robot?

Explain manual, shared, and autonomous responsibilities with a comparison table. Show the same changed-goal checkpoint in each mode. Students use distinct visible controls to redirect the teaching trace and compare who chooses the goal, confirms it, and supplies the movement. Relate each control to the later Gazebo trials.

## Mission 1. Build and verify the interaction

Edit the Python controller in the guide. Implement selection, clarification, confirmation, correction, cancellation, readiness, and timeout behavior. Work through selection and confirmation, offering and release, then interruption and recovery. Run the full scripted suite, inspect expected and observed transitions, and explain one guard.

Reset the Gazebo robot. Run the saved controller in the ROS interaction node, request blue, confirm, observe the round trip, and authorize the handover. Save the ROS result. The node advances its task state only when fresh odometry reaches the next waypoint.

## Mission 2. Voice trials, feedback redesign, and retest

Reset before each trial. Speak a clear request, an ambiguous request followed by a named cup, a correction, and a cancellation. Corrections and cancellations occur at the same yellow checkpoint. Recognized permission is reviewed before application. Save intended speech, transcripts, events, robot poses, distance, and outcome.

Choose an observed feedback problem, revise the message for a state reached in that baseline, and repeat the same scenario. Show corresponding baseline and retest events side by side and explain what changed.

## Mission 3. Compare the modes

Run a normal blue-cup delivery and a changed-goal red-cup delivery in each of three modes.

- Manual teleoperation uses a ROS keyboard node. The person steers, loads at the station, returns, offers, and signals readiness.
- Shared autonomy uses spoken requests and the student's checked interaction rules. The supplied movement controller drives the confirmed task.
- Autonomous execution uses the supplied task policy. The person starts it and uses Stop and a new goal at the intervention checkpoint.

Reset the world before every new trial. Use the same readiness button in all six. Compare delivered cup, outcome, elapsed time, operator inputs, distance, and intervention trace. Timing includes the person's voice recording and review.

## Synthesis and submission

Answer one technical synthesis using evidence from all three missions, then complete the shared course reflection. The readiness table verifies current source and ROS evidence. Save and inspect the complete submission and push it to the student's fork. Draft backups retain unfinished work and archived attempts.
