# Final synthesis

The robot combines motion estimates with LiDAR observations to construct an occupancy grid map of the TurtleBot3 House. LiDAR provides evidence about nearby surfaces and free space along observed rays, while motion estimates help place successive scans in a shared frame. Areas outside the sensor’s line of sight can remain unknown, so neither map establishes the complete house layout.

Mission 1, labeled corridors_then_rooms, produced 0.89 m^2 of known area and a known fraction of 7.65%. Mission 2, labeled wall_following, produced 11.63 m^2 of known area and a known fraction of 28.34%. Speckle fraction decreased from 16.67% to 5.51%, supporting my prediction that the second strategy would produce more extensive coverage with fewer isolated occupied patches. The recorded times were 4 and 10 minutes, respectively. However, Mission 1’s time was not measured, so the reported efficiency difference is uncertain. The longer second run also means route choice alone cannot explain the improvement.

Motion estimate error can accumulate and cause scans to misalign, potentially producing shifted or doubled walls. Revisiting recognizable geometry can help SLAM constrain that error. However, slow visual updates prevented me from reliably observing a correction, so I cannot claim a confirmed loop closure.

The supplied map preview contains straight occupied edges and connected free space, but also substantial unknown space and a scattered boundary. I would provisionally trust Mission 2 more because of its greater known area and lower speckle fraction. Nevertheless, neither its higher quality score nor its larger coverage proves geometric accuracy or safe navigation. Missing areas and uncertain boundaries would require further inspection before a later task.
