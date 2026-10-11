# Mission 2

## Comparison

The table records 4 minutes for Mission 1 and 10 minutes for Mission 2. The wall following route produced more known area: 11.63 m^2 compared with 0.89 m^2. Known fraction increased from 7.65% to 28.34%, while speckle fraction decreased from 16.67% to 5.51%. These results support my prediction that the second route would provide more coverage and fewer isolated occupied patches, although it took longer. The reported known area per minute also increased from 0.22 to 1.16 m^2/min, suggesting better coverage for the time spent. However, Mission 1’s duration was not measured, so that efficiency comparison is tentative. The tradeoff was a longer run for a more extensive, less fragmented map. These metrics alone do not prove better geometric accuracy.

## Map Choice

I would provisionally choose the Mission 2 map for a later robot task because it contains more known area and a lower speckle fraction. The supplied map image shows a connected light free space region bounded by straight dark edges along its top and left sides, but substantial gray unknown space remains, and the boundary near the upper right appears scattered. I would inspect those incomplete areas before relying on the map for navigation. Without comparing both images side by side, I cannot conclude that Mission 2 has better wall alignment or fewer duplicate structures. Neither the images nor the higher quality score establishes true geometric accuracy without a reference map or verified measurements.

## Strategy.Original Prediction

For Mission 2, I will follow connected walls and explore accessible openings as I reach them, rather than following corridors first and then entering rooms. I will slow down near corners and revisit a recognizable junction. I predict that overlapping views will produce clearer wall outlines and fewer gaps, although this route may take longer. I also hope the simulation and RViz respond more smoothly, since previously the terminal showed changing velocity commands while visual updates were delayed. I will check the robot’s visible movement rather than assume the commands confirm it moved.

## Strategy.Prediction Draft

For Mission 2, I will follow connected walls and explore accessible openings as I reach them, rather than following corridors first and then entering rooms. I will slow down near corners and revisit a recognizable junction. I predict that overlapping views will produce clearer wall outlines and fewer gaps, although this route may take longer. I also hope the simulation and RViz respond more smoothly, since previously the terminal showed changing velocity commands while visual updates were delayed. I will check the robot’s visible movement rather than assume the commands confirm it moved.
