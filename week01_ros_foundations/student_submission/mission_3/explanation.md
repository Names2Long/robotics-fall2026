# Mission 3

## Data To Command

The first function uses front_distance() to find the nearest valid LiDAR distance thats ahead of the robot. While the second function will use that distance to decide if the robot needs to move stop or move forward

## Missing Data Safety

The robot will stop when there isn’t a valid front measurement because it cant tell weather or not if there is an obstacle ahed. If we just assume the path to be clear of any obstacles, the robot would probably just crash.

## System Layers

The decision functions determines the speed based on its LiDAR readings. While the supplied ROS node sends that speed data to /student_cmd_vel, and the command guard checks it before sending the command to /cmd_vel

