# Original simulation artwork and adapted environments

Track and practice PNG/SVG files are copied without modification from the supplied csci39536-base/tuos_simulations repository. Original package attribution: Tom Howard, University of Sheffield, COM2009 teaching materials. The original repository identifies Creative Commons Attribution-NonCommercial 4.0 International. See ORIGINAL_LICENSE.md. These assets are not relicensed under the ROS node package's MIT license.

Original source metadata: https://github.com/tom-howard/tuos_ros/tree/main/tuos_simulations

The new world generator preserves the original 8 by 8 metre route, 4 by 12 metre straight practice surface, four pillar colors and pillar positions. World launch, local materials, lighting, camera configuration and ROS interfaces are adapted for ROS 2 Jazzy and modern Gazebo. The robot is the installed ROBOTIS TurtleBot3 Waffle model, retaining its package's own license. No external models are downloaded when the worlds start.

The magenta route has a red finish panel. Detecting red in the relevant camera region is a simulated finish cue, not a physical stopping-distance measurement. The straight practice surface has no red finish panel. End that test manually.
