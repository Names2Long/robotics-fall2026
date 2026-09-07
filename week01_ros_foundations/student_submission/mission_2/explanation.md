# Mission 2

## Predictions

{'straight': 'I predict the robot will finish ahead of its starting point by about three feet ', 'rotation': 'I predict its postion will be rotated to the left while its direction will also be towards the left ', 'curve': 'I predict the robot to turn fully right because the robot is moving straight and turning right at the same time ', 'curve_modified': 'This curve should be tighter and turn the left, because the turning speed is now +0.80 rad/s, so the robot curves left rather than right. '}

## Prediction Locks

{'rotation': '2026-09-06T22:18:31.385499+00:00', 'straight': '2026-09-06T22:19:56.098712+00:00', 'curve': '2026-09-06T22:22:52.875896+00:00', 'curve_modified': '2026-09-06T22:29:57.597814+00:00'}

## Motion Comparison

Based on the Straight Motion trial, I predicted the robot will finish ahead of its starting point by about three feet. However after running the simulation I noticed I over estimated. Since the robot command path was 0.45 and estimated travel path was 0.3. Both of which are less than 3 ft


## Measurement Explanation

On the curved trial, the estimated travel path was  0.398m while the start to end distance was 0.38m. Since the turning speed created a curved path where the robot traveled a longer distance compared to the straight line distance. It also technically traveled a longer route.

## Safety Explanation

The command guard checks every proposed driving command on /student_cmd_vel before it is allowed through. The final zero command marks the planned end of a trial by commanding zero forward and zero turning speed. The timeout is needed if a program crashes or communication drops while the robot is already in motion and after a second without a new command the guard will stop on its own

## Modified Settings

{'linear_x': 0.22, 'angular_z': 0.8, 'duration': 4.0}
