# Lab 7 instructor notes

## Teaching route

Preflight checks image operations and installed robot software, followed by 16 independent-input playground lessons, Mission 1 detector investigation in three parts, Mission 2 pillar search, Mission 3 line following, then one technical synthesis and the shared course reflection. There is no separate deployment checklist. Simulation startup and live readiness checks begin Mission 2. Do not launch Gazebo during initial preflight. Mission 3 repeats live checks after resetting worlds. Part A covers classical detection, Part B learned representations and Part C a focused matched comparison. Both Part A responses are required before opening B or C, with part navigation only at the bottom.

The final playground step links a documented executable reference for all operations. The comparison lesson applies erosion, dilation, opening and closing to one mask with a common kernel. Mission 3 edits actual Python in the guide rather than sliders. The saved controller.py is loaded by the ROS node, and the exact source travels with each recorded attempt. Its initial gain is intentionally weak and speed is 0.16 m/s. Separate Practice and Track panels make importing a practice run explicit. New code-based evidence requires two distinct track programs. Older retained reports remain readable and are not retroactively forced to contain code that was never recorded.

The source is Ryan Riggins' CC0 multi-object desk photograph, with a mug, laptop, keyboard and trackpad. Its top-clipped mug is explicitly noted. The task is to propose the mug's image location for an assistive robot, not to execute a grasp. Manual visible-extent annotations are independent of the models. See assets/conditions/TABLETOP_SOURCE.md.

The playground separates resizing from cropping. RGB, HSV, smoothing and morphology show useful alternatives together. Morphology rebuilds a fixed raw threshold mask, displayed before the results, without inheriting threshold experiments from the prior topic. The final geometry lesson uses a labeled teaching annotation so a failed detector does not prevent learning the difference between rectangle center and silhouette centroid. It is not scored as detector success.

## Models and matched evaluation

The shared cup category includes the mug. Frozen means weights do not change during the lab. MobileNet assigns whole-image labels. YOLOX supplies scored cup boxes. U²-Net supplies class-agnostic foreground, not semantic cup identities or instances. Do not treat these as interchangeable tasks.

Preflight runs real inference and warms a dataset/model-keyed on-disk cache. Normal scene selection and guided navigation must not run the models again. Shared scene construction, fingerprints, segmentation decoding and validation use bounded caches. Rebuild after source/model updates. Export regenerates evidence from canonical saved predictions, not from mutable UI previews.

Part C leads with correct boxes, false boxes and missed mugs per selected condition, alongside timings and box precision/recall. Paired images use identical image IDs and shared cyan references. The first question directs students to three conditions and one paired example. The second directs them to one specified mask example and a bounded recommendation. Detailed threshold/AP, classification and mask tables remain in explained expanders. Students do not need to discuss every metric.

Image-presence and box-location metrics answer different questions. Box matching requires IoU at least 0.50. AP50 is a single-class precision-envelope summary, not multi-class/multi-IoU mAP. Foreground-mask agreement against a mug silhouette measures task fit, not object identity. Missing denominators are undefined rather than zero or perfect. Independent photos lack mask annotations. Do not average empty negative masks into target-present segmentation quality.

Controlled image rotation is not a new physical viewpoint. Apparent-size changes do not establish distance. Independent photographs change multiple factors together. This small collection does not support deployment safety or demographic-fairness claims. It is acceptable to observe no difference or poor performance, provided the student explains the evidence. There is no minimum accuracy gate.

## Saving, migration and release checks

Stable storage keys remain mission_1 for Part A and mission_2 for Parts B/C. Older stage identifiers migrate into the combined investigation and responses are preserved. Old behavior evidence is not a finalization requirement. Older image experiments require rerunning when the dataset fingerprint changes. Drafts remain downloadable.

Use WEEK08_SUBMISSION_DIR with an absolute isolated path for testing. The automated suite checks all playground steps, saved program execution, comparison settings, restart restoration and final artifact regeneration. The distributed submission folder contains only .gitkeep. Archive known instructor testing data under ignored runtime and restart the server for a clean test. Do not delete genuine student work.

See ROS_MISSIONS_PLAN.md for the live mission design and ROS_MISSIONS_STATUS.md for verification. A student timing and visual-interaction pilot is still useful. Mission 1 does not need ROS. The separate live check requires received camera frames, advancing simulation time, the TwistStamped command bridge and the independent guard.

Live attempts are stored first under ignored runtime/robot_runs. Students retain selected reports in the guide, including interrupted or unsuccessful runs. Finalization requires an all-four-color attempt and both practice and track attempts, not successful completion or a numeric performance score. New evidence keys pillar_search and line_following do not collide with learned evidence in mission_2. Settings are read at controller startup, not changed live by the browser.

Each launch recreates the world and robot. Scripts set ROS_DOMAIN_ID=28 and GZ_PARTITION=lab7_vision. Launch only one world and controller at a time. Keep the rotation-only pillar task distinct from line following, where fresh valid line observations permit bounded forward motion. The independent guard uses a monotonic watchdog, so a paused simulation clock does not prevent stopping on controller loss. These safeguards are educational simulation constraints, not a physical safety system.

Track artwork and pillar layout originate with Tom Howard and the University of Sheffield under CC BY-NC 4.0. Preserve assets/robot_worlds attribution and license when redistributing. The controller and world generator are new ROS 2 implementations, not a mechanical ROS 1 port.
