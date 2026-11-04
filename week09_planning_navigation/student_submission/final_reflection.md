# Final reflection

Respond to any or all of these prompts:

1. What did this activity make you think about regarding your own interests in robotics, computing, engineering, or related work?
2. How did this activity affect your motivation to do similar kinds of work in the future?
3. What value do you see in connecting technical or computing work with human, ethical, or societal considerations?
4. What stood out to you about the activity, and why?
5. Is there anything else you would like to share about your experience with the activity?

## Response

This lab helped me connect programming decisions to how a robot actually moves. Implementing BFS, DFS, IDDFS and A* made search algorithms easier to understand because I could test their results and then see the routes used in simulation.

What stood out most was that a valid route was not always a useful route. DFS expanded fewer nodes than BFS on the constrained map, but its route was much longer and the robot failed during execution. This taught me to look beyond planning speed and consider route length, tracking, completion and clearance together.

The human aware navigation activity also changed how I thought about choosing  the best possible route. A robot should consider the people sharing its space, not just reach a destination quickly. My results showed that increasing clearance from a person could come with other trade offs. Such as passing closer to walls. Technical measurements therefore need to be interpreted in the context of human needs.

Setting up the environment and editing the planner file required a bit of patience. I used AI to help implement and explain the algorithms so I can have a better understanding. Then I ran the lab evaluations to check their behavior. Working through these steps made me more comfortable with testing and troubleshooting rather than assuming code would  just work.

Overall seeing the connection between search, control and human considerations made me more interested in robotics. I also learned to be careful about conclusions. One successful simulation does not prove reliability, and stationary simulated people do not represent unpredictable real world behavior. Further testing is  also a key step.

_Word count: 267_
