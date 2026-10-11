# Week 6: SLAM and Mapping

- email: ASIL.CHOWDHURY41@stu-mail.hunter.cuny.edu
- name: Ishraq Chowdhury

## final.course_reflection

This activity showed me that getting a robotics system running can take as much effort as the experiment itself. I encountered script permission errors, Docker connection problems, slow visual updates, and confusion about which terminal controlled each process. At one point, I stopped a process and the simulation closed. Recovering the environment interrupted my progress and made it harder to focus on the mapping.

The lab did not feel very user friendly to me. Managing separate terminals for mapping, RViz, teleoperation, and saving results was difficult, especially when their purposes were not clearly labeled. A single control panel with labeled start and stop buttons, clearer recovery instructions, and an automatic experiment timer would have made the experience easier. Delayed visual feedback was particularly frustrating because changing velocity commands did not clearly show whether the robot was moving. Despite these difficulties, comparing the saved maps helped me understand that issuing commands, observing movement, and producing a useful map are different things.

The experience made me less enthusiastic about repeating this particular setup and lab, but it highlighted the fact that usability and reliable feedback affect the quality of technical work. Overall, not the best lab I have done.

## final.synthesis

The robot combines motion estimates with LiDAR observations to construct an occupancy grid map of the TurtleBot3 House. LiDAR provides evidence about nearby surfaces and free space along observed rays, while motion estimates help place successive scans in a shared frame. Areas outside the sensor’s line of sight can remain unknown, so neither map establishes the complete house layout.

Mission 1, labeled corridors_then_rooms, produced 0.89 m^2 of known area and a known fraction of 7.65%. Mission 2, labeled wall_following, produced 11.63 m^2 of known area and a known fraction of 28.34%. Speckle fraction decreased from 16.67% to 5.51%, supporting my prediction that the second strategy would produce more extensive coverage with fewer isolated occupied patches. The recorded times were 4 and 10 minutes, respectively. However, Mission 1’s time was not measured, so the reported efficiency difference is uncertain. The longer second run also means route choice alone cannot explain the improvement.

Motion estimate error can accumulate and cause scans to misalign, potentially producing shifted or doubled walls. Revisiting recognizable geometry can help SLAM constrain that error. However, slow visual updates prevented me from reliably observing a correction, so I cannot claim a confirmed loop closure.

The supplied map preview contains straight occupied edges and connected free space, but also substantial unknown space and a scattered boundary. I would provisionally trust Mission 2 more because of its greater known area and lower speckle fraction. Nevertheless, neither its higher quality score nor its larger coverage proves geometric accuracy or safe navigation. Missing areas and uncertain boundaries would require further inspection before a later task.

## mission_1.drift_and_revisit

Because RViz was lagging and updating slowly, I could not reliably compare the live scan with previously mapped walls during the revisit. I could not tell whether an old wall shifted or doubled. Without a clear live observation or before and after images of the same area, I cannot claim that SLAM corrected drift or performed a loop closure.

## mission_1.limitations

The simulation and RViz were slow to load and update on my machine, which made it difficult to identify a specific poorly outlined area in the screenshot. The saved map contained about 92.35% unknown cells, although some may represent space outside the walls. Limited exploration or blocked LiDAR views could explain gaps, but I could not verify their locations or causes from the display. I cannot conclude that the performance issues caused the unknown cells.

## mission_1.route.original_prediction

I will drive slowly from the starting position through accessible corridors and into rooms with clear openings, observing walls and obstacles from multiple sides. I will revisit the first distinct doorway or junction I pass to check whether the map lines up with earlier observations. I predict coverage will be weak behind furniture, around hidden corners, and in rooms I do not enter. Alignment may be weaker along long corridors with similar looking walls, where accumulated motion error could make it harder to match scans.

## mission_1.route.prediction_draft

I will drive slowly from the starting position through accessible corridors and into rooms with clear openings, observing walls and obstacles from multiple sides. I will revisit the first distinct doorway or junction I pass to check whether the map lines up with earlier observations. I predict coverage will be weak behind furniture, around hidden corners, and in rooms I do not enter. Alignment may be weaker along long corridors with similar looking walls, where accumulated motion error could make it harder to match scans.

## mission_2.comparison

The table records 4 minutes for Mission 1 and 10 minutes for Mission 2. The wall following route produced more known area: 11.63 m^2 compared with 0.89 m^2. Known fraction increased from 7.65% to 28.34%, while speckle fraction decreased from 16.67% to 5.51%. These results support my prediction that the second route would provide more coverage and fewer isolated occupied patches, although it took longer. The reported known area per minute also increased from 0.22 to 1.16 m^2/min, suggesting better coverage for the time spent. However, Mission 1’s duration was not measured, so that efficiency comparison is tentative. The tradeoff was a longer run for a more extensive, less fragmented map. These metrics alone do not prove better geometric accuracy.

## mission_2.map_choice

I would provisionally choose the Mission 2 map for a later robot task because it contains more known area and a lower speckle fraction. The supplied map image shows a connected light free space region bounded by straight dark edges along its top and left sides, but substantial gray unknown space remains, and the boundary near the upper right appears scattered. I would inspect those incomplete areas before relying on the map for navigation. Without comparing both images side by side, I cannot conclude that Mission 2 has better wall alignment or fewer duplicate structures. Neither the images nor the higher quality score establishes true geometric accuracy without a reference map or verified measurements.

## mission_2.strategy.original_prediction

For Mission 2, I will follow connected walls and explore accessible openings as I reach them, rather than following corridors first and then entering rooms. I will slow down near corners and revisit a recognizable junction. I predict that overlapping views will produce clearer wall outlines and fewer gaps, although this route may take longer. I also hope the simulation and RViz respond more smoothly, since previously the terminal showed changing velocity commands while visual updates were delayed. I will check the robot’s visible movement rather than assume the commands confirm it moved.

## mission_2.strategy.prediction_draft

For Mission 2, I will follow connected walls and explore accessible openings as I reach them, rather than following corridors first and then entering rooms. I will slow down near corners and revisit a recognizable junction. I predict that overlapping views will produce clearer wall outlines and fewer gaps, although this route may take longer. I also hope the simulation and RViz respond more smoothly, since previously the terminal showed changing velocity commands while visual updates were delayed. I will check the robot’s visible movement rather than assume the commands confirm it moved.
