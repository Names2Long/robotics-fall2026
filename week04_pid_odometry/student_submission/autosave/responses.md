# Autosaved responses

- Name: Ishraq Chowdhury
- Student ID: 24005241
- Section: CSCI 39536

## Check-in answers

### background_compare

A human engineer chooses the target setpoint and tunes the proportional, integral, and derivative gains while considering environmental conditions, friction, components, materials, and possible human errors in setup. PID is a feedback controller because it continuously compares the measured output with the target and adjusts its command to reduce the error.

### background_social

For car brakes, a controller tuned too aggressively could apply braking too suddenly, causing the car to jerk and potentially injuring passengers. If tuned too cautiously, it could apply braking too slowly, increasing stopping distance and putting pedestrians, passengers, and other drivers at risk. The tuning needs to balance smooth braking with a fast enough response to stop safely.

### pid_playground_terms

The P term reacted first because it responds directly to the current error when the target moves. The I term eliminated the final gap by accumulating the remaining error over time.

### odom_background_wheels

It turns left because dR - dL is 6 - 0 = 6 cm, which is positive. Using heading change = (dR - dL) / L, the heading change is positive, meaning a left turn.

### m1_prediction

With too little Kp, I expect the arm to slowly reach the target while  with too little KD, I expect  the arm to not reach the target

### m1_arm_tuning

I predicted that low Kp would make the arm move slowly and low Kd would keep it from reaching the target. I adjusted Kp, Ki, and Kd on both the shoulder and elbow through trial and error until the arm successfully held three target poses. My final settings were Kp = 6.0, Ki = 0.9, and Kd = 1.3 for both joints. I learned that low Kd can cause overshooting and oscillation rather than stopping short. I did not separately test gravity compensation, so I cannot say how much it affected my result.

### m2_prediction

I assume the forwad distance will underestimate its distance and go too forward. While the sideways distance will barley turn

### m2_analysis

I predicted that the forward estimate would be too low and the robot would barely turn sideways. I learned that strafing means moving sideways without turning. I tuned the forward scale to 0.0494 inches per tick and the strafe scale to 0.0502 inches per tick. These control how encoder ticks become estimated forward and sideways distances. The sideways pod is necessary because the forward pod cannot measure sideways motion. The test passed with a maximum error of 0.80 inches and a final error of 0.37 inches, both below 3 inches. Some drift can remain because of wheel slip, sensor resolution, and small calibration errors that accumulate over time.

### m3_prediction

I predict that increasing speed may cause the robot to go too fast to follow the planned route accurately. Too little derivative control may cause the robot to overshoot turns or wobble because its movements are not damped enough. Therefore, clearance may decrease as the robot moves closer to pedestrians than planned.

### m3_technical

I predicted that higher speed and too little derivative control could cause tracking errors and reduce pedestrian clearance. The robot computes the direction to the next route point and compares it with its estimated heading. PID uses this heading error to adjust the wheel speed differences and steer. The drive reached all four waypoints and kept 0.30 m from pedestrians, but the maximum path error was 0.12 m, above the 0.10 m limit, so more tuning is needed. The green path shows the true motion, while the orange path shows the odometry estimate. An inaccurate wheel radius converts wheel rotation into the wrong distance, so even a well-tuned controller can steer based on an wrong position.

### m3_human

The most consequential failure would be the robot injuring a pedestrian. I would choose a slower speed and clearance greater than the minimum 0.28 m to leave room for tracking errors and unexpected movement. The engineers and the company deploying the robot are responsible for testing and verifying that these choices are safe before using it.

### final_reflection

I liked how this lab was short, fun, and informational . The interactive activities helped me understand PID control and odometry by letting me change settings and see how the robot responded live. I especially enjoyed the trial and error involved in getting the robot to reach its targets and follow a route with less error. The sidewalk delivery activity also helped me see why accuracy matters around people. Since choosing a speed and planning enough clearance affects pedestrian safety. Not just whether the robot finishes its route or not. This lab made me more interested in doing similar interactive robotics activities in the future.  Overall, I enjoyed doing a lab that did not involve ROS because I always run into technical issues with the ROS labs.

## Mission explanations

### mission_1

**prediction**: With too little Kp, I expect the arm to slowly reach the target while  with too little KD, I expect  the arm to not reach the target

**tuning_analysis**: I predicted that low Kp would make the arm move slowly and low Kd would keep it from reaching the target. I adjusted Kp, Ki, and Kd on both the shoulder and elbow through trial and error until the arm successfully held three target poses. My final settings were Kp = 6.0, Ki = 0.9, and Kd = 1.3 for both joints. I learned that low Kd can cause overshooting and oscillation rather than stopping short. I did not separately test gravity compensation, so I cannot say how much it affected my result.

### mission_2

**prediction**: I assume the forwad distance will underestimate its distance and go too forward. While the sideways distance will barley turn

**calibration_analysis**: I predicted that the forward estimate would be too low and the robot would barely turn sideways. I learned that strafing means moving sideways without turning. I tuned the forward scale to 0.0494 inches per tick and the strafe scale to 0.0502 inches per tick. These control how encoder ticks become estimated forward and sideways distances. The sideways pod is necessary because the forward pod cannot measure sideways motion. The test passed with a maximum error of 0.80 inches and a final error of 0.37 inches, both below 3 inches. Some drift can remain because of wheel slip, sensor resolution, and small calibration errors that accumulate over time.

### mission_3

**technical_analysis**: I predicted that higher speed and too little derivative control could cause tracking errors and reduce pedestrian clearance. The robot computes the direction to the next route point and compares it with its estimated heading. PID uses this heading error to adjust the wheel speed differences and steer. The drive reached all four waypoints and kept 0.30 m from pedestrians, but the maximum path error was 0.12 m, above the 0.10 m limit, so more tuning is needed. The green path shows the true motion, while the orange path shows the odometry estimate. An inaccurate wheel radius converts wheel rotation into the wrong distance, so even a well-tuned controller can steer based on an wrong position.

**human_centered_analysis**: The most consequential failure would be the robot injuring a pedestrian. I would choose a slower speed and clearance greater than the minimum 0.28 m to leave room for tracking errors and unexpected movement. The engineers and the company deploying the robot are responsible for testing and verifying that these choices are safe before using it.
