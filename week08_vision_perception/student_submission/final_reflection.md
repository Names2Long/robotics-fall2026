This lab helped me understand how image processing connects to robot movement. Working with masks, centroids, and steering commands made robotics feel more concrete because I could see how camera information affected the robot’s behavior.

What stood out most was that a result could look successful while still having limitations. In the detector activity, lowering the circularity threshold produced a box around almost the entire image instead of identifying the mug. The line following robot also completed the track despite having substantial centering error. These results taught me to inspect the evidence rather than judge performance only by whether a box appeared or the robot reached the finish.

The setup and troubleshooting required patience. One controller failed to start because I used the practice command while the track world was running. Reading the error and correcting the command helped me understand the importance of matching the controller to its environment. Seeing the robot eventually complete the route made me more interested in learning how perception and control work together.

Addtionally, I would say that technical decisions matter for people. A robot that follows a colored line does not necessarily recognize a person or know how far away an obstacle is. Stopping when camera information is unavailable is useful, but additional sensing and testing would still be necessary around people.

Overall, I learned to treat failures and imperfect results as evidence that can guide the next part of the lab.