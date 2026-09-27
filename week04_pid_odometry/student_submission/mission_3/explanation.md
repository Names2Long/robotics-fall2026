# mission_3 Submission

- Name: Ishraq Chowdhury
- Section: CSCI 39536

## Explanations

### technical_analysis

I predicted that higher speed and too little derivative control could cause tracking errors and reduce pedestrian clearance. The robot computes the direction to the next route point and compares it with its estimated heading. PID uses this heading error to adjust the wheel speed differences and steer. The drive reached all four waypoints and kept 0.30 m from pedestrians, but the maximum path error was 0.12 m, above the 0.10 m limit, so more tuning is needed. The green path shows the true motion, while the orange path shows the odometry estimate. An inaccurate wheel radius converts wheel rotation into the wrong distance, so even a well-tuned controller can steer based on an wrong position.

### human_centered_analysis

The most consequential failure would be the robot injuring a pedestrian. I would choose a slower speed and clearance greater than the minimum 0.28 m to leave room for tracking errors and unexpected movement. The engineers and the company deploying the robot are responsible for testing and verifying that these choices are safe before using it.