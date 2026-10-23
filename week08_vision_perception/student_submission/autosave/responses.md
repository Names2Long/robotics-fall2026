# Lab 7 saved answers

## mission_1.diagnosis
During practice, I lowered the minimum circularity from 0.60 to 0.10 while keeping the other settings unchanged. The mask stayed the same because circularity filters the contours after the mask is created. Before the change, candidate 0 was rejected because its circularity was 0.1355, below 0.60. After lowering the threshold, it became eligible. Its area of 107,338.5 pixels^2 also exceeded the minimum area of 3,193. A green box appeared around almost the entire image rather than isolating the mug. This shows that allowing less circular regions can produce a detection without correctly locating the target. A different cup could fail the color thresholds, while a background with matching colors could be selected instead.

## mission_1.limitations
I changed the minimum circularity from 0.60 to 0.10, keeping all other settings the same. The mask did not change, but a green box appeared around almost the entire image. The contour’s circularity was 0.1355, so it failed the original threshold but passed the lower one. The box still did not isolate the mug. This shows that passing the shape filter does not mean the detector found a cup. A differently colored cup could be missed, and a background matching the color rule could be selected instead.

## pillar_search.diagnosis
In my attempt the robot successfully centered the blue pillar. The camera image shows the blue pillar, and the white mask isolates its colored region. Initially, its centroid was left of center, producing negative image error. With the angular command equal to minus gain times error, this produced a positive turn command, turning the robot left. The final error approached zero, and the annotated image shows the yellow centroid close to the magenta center line. The robot then stopped turning, while forward speed remained zero throughout. This attempt used gain 1.2, tolerance 0.10 and hold time 0.70 seconds. Without a recorded comparison using different settings, I cannot determine whether a setting change improved or worsened performance.

## pillar_search.evidence
In my attempt, all four requested colors. Red, green, turquoise and blue completed the centering. None remained unfinished. The report records all four visited colors and an outcome of complete after 19.53 simulation seconds. The visible timeline begins with four WAIT_CAMERA decisions with zero commands, followed by SEARCH for red. The error plot shows four centering intervals approaching zero, with pauses in turning between them. The final camera image and mask support successful blue centering, with the centroid close to the image center. A centered region and stable hold only establish alignment with pixels matching the color rule. Another similarly colored object could pass the same rule, and horizontal image alignment provides no depth measurement or physical distance.

## line_following.comparison
I compared practice attempt with my tracked and I noticed both used gain 0.08, maximum speed 0.16 m/s, ROI 0.60–0.95, hue range 140 - 169, and steering expression -gain * error. On the straight practice strip, mean absolute image error was approximately 0.144, with no line loss events before I ended the run. On the curved track, the robot completed the route in 187.25 simulation seconds, also without losing the line, but mean absolute error increased to approximately 0.483. Around 50 seconds, error reached about +0.8 and the controller commanded a right turn around 130 seconds, error approached -0.9 and it commanded a left turn. Forward speed decreased during larger errors. The final mask still selected the magenta route near the finish. This shows successful route following with substantial offsets on bends, rather than consistently centered tracking. I did not change settings between these attempts, so this comparison does not demonstrate the effect of a parameter change.

## line_following.limits
In my track attempt  the initial timeline shows WAIT_CAMERA with zero forward and angular commands. This stop began because camera information was not yet available, rather than because of an incorrect steering calculation or a rejected line contour. Once a valid image arrived, the controller entered TRACK and began moving. The run later completed at the red finish panel, visible in the final camera image, and the forward command returned to zero. There were no recorded line loss events. For a real delivery robot around people, line following alone would be insufficient. It would need obstacle and person detection, distance sensing such as lidar or a depth camera, and reliable localization. Tests should cover people crossing its path, blocked routes, changing lighting, worn markings, camera delays, sensor failures, and stopping distance under different speeds, loads and floor conditions.

## final.synthesis
From the three missions, I observed that visual evidence can guide a robots actions without proving object identity, distance, or safety.

In Mission 1, lowering the classical detector’s circularity threshold from 0.60 to 0.10 made a contour with circularity 0.1355 eligible. However, its box covered almost the entire image instead of isolating the mug. Passing the color and shape rules therefore did not establish that the selected region was the target. For normal_1, the learned classifier’s highest scoring label was notebook, which described the scene without locating the mug. The foreground segmentation had mask IoU 0.5756, with both extra foreground and missed cup pixels. Detailed boundaries alone did not establish cup identity.

In Mission 2, I noticed it took 9.53 simulation seconds to complete all four colors . The final blue mask isolated the pillars colored region, and its centroid was close to the image center. Negative horizontal error produced a positive angular command, turning the robot left toward the target. Forward commands remained zero. This demonstrated image based centering, but not recognition of a unique landmark or measurement of its distance.

In Mission 3, my practice attempt and tracked attempt both used gain 0.08 and maximum speed 0.16 m/s. Mean absolute image error increased from approximately 0.144 on practice to 0.483 on the track. The track nevertheless completed in 187.25 simulation seconds without line loss. I infer that this controller could follow the route under the tested conditions, although completion did not mean consistently accurate centering.

Together, these results show why perception must be evaluated alongside the actions it produces. A real assistive or delivery robot would also need depth, calibration, obstacle detection, and testing under varied conditions before these image based behaviors could support safe physical interaction.

## final.course_reflection
This lab helped me understand how image processing connects to robot movement. Working with masks, centroids, and steering commands made robotics feel more concrete because I could see how camera information affected the robot’s behavior.

What stood out most was that a result could look successful while still having limitations. In the detector activity, lowering the circularity threshold produced a box around almost the entire image instead of identifying the mug. The line following robot also completed the track despite having substantial centering error. These results taught me to inspect the evidence rather than judge performance only by whether a box appeared or the robot reached the finish.

The setup and troubleshooting required patience. One controller failed to start because I used the practice command while the track world was running. Reading the error and correcting the command helped me understand the importance of matching the controller to its environment. Seeing the robot eventually complete the route made me more interested in learning how perception and control work together.

Addtionally, I would say that technical decisions matter for people. A robot that follows a colored line does not necessarily recognize a person or know how far away an obstacle is. Stopping when camera information is unavailable is useful, but additional sensing and testing would still be necessary around people.

Overall, I learned to treat failures and imperfect results as evidence that can guide the next part of the lab.

## mission_2.comparison
At the learned acceptance threshold of 0.50, I compared normal, dim and occluded while keeping the classical settings fixed.

For normal, the classical detector had 0 correct boxes, 0 false boxes and 2 missed mugs. The learned detector had 1 correct box, 0 false boxes and 1 missed mug.

For dim, the classical detector had 0 correct boxes, 1 false box and 2 missed mugs. The learned detector had 0 correct boxes, 0 false boxes and 2 missed mugs.

For occluded, both detectors had identical results: 0 correct boxes, 0 false boxes and 2 missed mugs.

The learned detector located one additional mug under normal conditions and avoided the classical detectors false box under dim conditions. However, neither located the mugs in the dim or occluded conditions at these settings. In the paired normal_1 image, both methods show the cyan reference but no green prediction, so both miss this particular mug. The learned detectors advantage in the normal condition therefore comes from another image, not normal_1. Avoiding false boxes matters, but producing no boxes is not sufficient when the robot needs to locate the mug.

## mission_2.choice
I recommend the learned detector for further testing. At the current acceptance threshold of 0.50, it found a mug under normal conditions and avoided the false detection made by the classical detector under dim conditions. However, it still missed many mugs. I would investigate a lower threshold of 0.20 next. The saved threshold sweep shows 12 correct boxes, 1 false box and 8 missed mugs across the collection, compared with 3 correct boxes, 0 false boxes and 17 missed mugs at 0.50. This trades one additional false detection for substantially fewer misses.

The learned detector took approximately 39 - 41 ms per image in the three selected conditions, compared with approximately 3.6 - 4.4 ms for the classical detector. It was slower, but its localization results justify further testing. These processing times exclude model loading and display and do not measure complete robot response time.

For normal_1, the foreground mask had IoU 0.5756 and Dice 0.7306, with 4,453 extra pixels and 1,852 missed mug pixels. This model identifies prominent foreground without assigning a cup label, so a detailed mask does not establish that the region is the requested mug. One important limitation is that this small collection contains many modified versions of the same scene, so the results do not establish performance across unfamiliar real environments.
