"""Visual explanations that prepare students for the ROS experiments."""
from io import BytesIO
from math import cos, radians, sin
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
OCCUPANCY_COLORS = LinearSegmentedColormap.from_list(
    "occupancy", ["#d9f1ff", "#a6acb0", "#202b33"]
)


def _figure(st, figure, width=660):
    """Use an explicit display width so a plot fits on a laptop screen."""
    output = BytesIO()
    figure.savefig(output, format="png", dpi=105, bbox_inches="tight")
    plt.close(figure)
    st.image(output.getvalue(), width=width)


def _ray_cells(start, end, width, height):
    x0, y0 = start
    x1, y1 = end
    steps = max(abs(x1 - x0), abs(y1 - y0)) * 8 + 1
    cells = []
    for fraction in np.linspace(0, 1, steps):
        x = round(x0 + (x1 - x0) * fraction)
        y = round(y0 + (y1 - y0) * fraction)
        if 0 <= x < width and 0 <= y < height and (x, y) not in cells:
            cells.append((x, y))
    return cells


def _probability_grid(width, height, rays):
    """A teaching model: one free update per traversed cell and one hit update."""
    log_odds = np.zeros((height, width), dtype=float)
    for start, end, hit in rays:
        cells = _ray_cells(start, end, width, height)
        for x, y in cells[:-1] if hit else cells:
            log_odds[y, x] -= 0.6
        if hit and cells:
            x, y = cells[-1]
            log_odds[y, x] += 1.1
    return 1 / (1 + np.exp(-log_odds))


def _grid_figure(st, grid, robot=(1, 5), rays=(), width=650):
    fig, ax = plt.subplots(figsize=(6.4, 3.1))
    ax.imshow(grid, cmap=OCCUPANCY_COLORS, vmin=0, vmax=1, origin="lower")
    ax.scatter([robot[0]], [robot[1]], color="#d93535", s=100, marker="^", zorder=5)
    for start, end, _ in rays:
        ax.plot([start[0], end[0]], [start[1], end[1]], color="#e39d00", lw=1.6)
    ax.set_xticks(range(grid.shape[1]))
    ax.set_yticks(range(grid.shape[0]))
    ax.tick_params(labelsize=7)
    ax.grid(color="white", lw=0.6, alpha=0.8)
    ax.set(xlabel="Grid column", ylabel="Grid row")
    _figure(st, fig, width)


def motion(st):
    st.header("Guided Tutorial 1: Motion estimates and dead reckoning")
    st.write("**Dead reckoning means estimating the robot's current position and heading by starting with a previous pose and adding estimated motion.** Wheel encoders measure wheel rotation. The robot converts those rotations into an estimated distance and turn. It does not directly measure where it ended up on the floor.")
    st.write("When both wheels move equally, a differential-drive robot moves straight. Unequal wheel speeds make a curve. Equal speeds in opposite directions rotate the robot. Wheel slip, incorrect wheel size, and uneven flooring can make the estimated motion differ from the actual motion.")
    st.latex(r"v_L=v_R\Rightarrow\text{straight},\quad v_L\ne v_R\Rightarrow\text{curve},\quad v_L=-v_R\Rightarrow\text{rotate}")
    st.subheader("Compare estimated paths")
    st.write("In this model, the robot first turns to face right, then actually drives straight along the blue line. The heading control sets an error in the robot's *estimate of that initial turn*. The robot does not keep turning while it drives. Each move is actually 1 m long. The distance control adds an overestimate to each 1 m move.")
    left, middle, right = st.columns(3)
    with left:
        distance_bias = st.slider("Distance overestimate per move, cm", 0, 5, 2, key="t1.distance_bias")
    with middle:
        heading_bias = st.slider("Estimated heading error after the initial turn, degrees", 0, 12, 4, key="t1.heading_bias")
    with right:
        moves = st.slider("Number of 1 m straight moves", 1, 10, 10, key="t1.moves")
    current = (distance_bias, heading_bias, moves)
    history = list(st.session_state.get("t1.history", []))
    if not history or tuple(history[-1]) != current:
        history.append(current)
    st.session_state["t1.history"] = history
    if st.button("Clear comparison lines", key="t1.clear"):
        history = [current]
        st.session_state["t1.history"] = history
    fig, ax = plt.subplots(figsize=(7, 3.1))
    ax.plot([0, 10.7], [0, 0], color="#1767a6", lw=2.5, label="Actual straight path")
    for index, (bias, heading, count) in enumerate(history, 1):
        distance = np.linspace(0, count * (1 + bias / 100), 40)
        angle = radians(heading)
        ax.plot(distance * cos(angle), distance * sin(angle), lw=1.8,
                label=f"{index}: {bias} cm, {heading}°, {count} moves")
    ax.set_xlim(0, 10.7)
    ax.set_ylim(0, 3)
    ax.set(xlabel="Forward position in metres", ylabel="Sideways position in metres")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, loc="upper left", ncol=2)
    _figure(st, fig, 720)
    st.caption("Each slider change adds an estimated path. Use Clear comparison lines to start a new comparison. The blue actual path remains fixed. The vertical axis always runs from 0 to 3 m.")
    st.metric("Accumulated distance overestimate", f"{moves * distance_bias / 100:.2f} m")
    st.write("For example, set 2 cm of overestimate and 10 moves to see 0.20 m of accumulated distance error. Then vary only the heading error. A small heading error produces a growing sideways displacement even though the actual robot continues straight.")
    st.info("Connection to SLAM: a LiDAR range can be correct relative to the robot while the robot's estimated pose is wrong. Placing that scan at the wrong pose can bend or duplicate a wall in the map.")


def _topological_example(st):
    fig, ax = plt.subplots(figsize=(5, 2.1))
    places = {"Room A": (0, 1), "Hallway": (1.5, 1), "Room B": (3, 1), "Charging dock": (1.5, 0)}
    for first, second in (("Room A", "Hallway"), ("Hallway", "Room B"), ("Hallway", "Charging dock")):
        x1, y1 = places[first]
        x2, y2 = places[second]
        ax.plot([x1, x2], [y1, y2], color="#52677a", lw=2)
    for label, (x, y) in places.items():
        ax.text(x, y, label, ha="center", va="center", fontsize=9,
                bbox={"boxstyle": "round,pad=0.35", "fc": "#d9e9f5", "ec": "#52677a"})
    ax.set_xlim(-0.6, 3.6)
    ax.set_ylim(-0.5, 1.5)
    ax.axis("off")
    _figure(st, fig, 480)


def maps(st):
    st.header("Guided Tutorial 2: Map representations")
    st.write("A **topological map** names places and shows which places connect. The example below says that the hallway connects two rooms and a charging dock. It does not say exactly how far apart they are or show the shape of their walls.")
    _topological_example(st)
    st.write("A **metric map** represents locations with coordinates and distances. Lab 6 builds a metric occupancy grid. Each cell stores evidence about whether that small area is occupied. A value near 0 means likely free and near 1 means likely occupied. In these diagrams, gray 0.5 cells have not been observed. In a real map, conflicting observations can also produce a probability near 0.5, so unknown status must be tracked separately.")
    st.write("Try each tab in order. The diagrams are simplified. Real SLAM also handles sensor noise, pose uncertainty, and repeated scans.")
    tabs = st.tabs(("1. One ray", "2. Multiple rays", "3. Range limit", "4. Missed object", "5. Cell size", "6. Probability"))
    with tabs[0]:
        st.write("A single LiDAR ray passes through cells that are probably free, then returns from a surface. Cells beyond that return receive no information from this ray.")
        endpoint = st.slider("Obstacle cell", 3, 10, 7, key="t2.endpoint")
        rays = [((1, 5), (endpoint, 5), True)]
        _grid_figure(st, _probability_grid(13, 11, rays), rays=rays)
        st.caption("Blue cells were crossed by the ray. The dark endpoint received occupied evidence. Gray cells remain unknown.")
    with tabs[1]:
        st.write("A scan contains many rays at different angles. Repeated rays reveal more surfaces and leave fewer unknown cells. They can also reinforce or contradict earlier evidence.")
        count = st.slider("Number of rays", 1, 9, 5, key="t2.ray_count")
        angles = np.linspace(-35, 35, count)
        rays = []
        for angle in angles:
            end_y = int(round(5 + 8 * np.tan(radians(float(angle)))))
            end_y = max(0, min(10, end_y))
            rays.append(((1, 5), (9, end_y), True))
        _grid_figure(st, _probability_grid(13, 11, rays), rays=rays)
        st.caption("This example places returns along a wall at column 9. Increase the ray count to see more of it.")
    with tabs[2]:
        st.write("A sensor has a maximum useful range. If an object lies farther away, a beam can pass through observable space without reporting an obstacle. The region beyond the limit remains unknown, not free.")
        limit = st.slider("Maximum ray length in cells", 2, 10, 5, key="t2.limit")
        hit = limit >= 8
        end = (9, 5) if hit else (1 + limit, 5)
        rays = [((1, 5), end, hit)]
        _grid_figure(st, _probability_grid(13, 11, rays), rays=rays)
        st.caption("The object is at column 9. A range below 8 cells does not reach it.")
    with tabs[3]:
        st.write("Even an object within range can fall between sampled beam directions. A small distant object covers a narrow angle, so sparse rays may miss it.")
        count = st.slider("Number of rays across a 30 degree view", 2, 15, 2, key="t2.sparse_count")
        angles = np.linspace(-15, 15, count)
        object_distance = 8.0
        object_radius = 0.32
        hits = [abs(object_distance * np.tan(radians(float(angle)))) <= object_radius for angle in angles]
        fig, ax = plt.subplots(figsize=(6.5, 2.8))
        for angle, hit in zip(angles, hits):
            ax.plot([0, 9], [0, 9 * np.tan(radians(float(angle)))],
                    color="#bf5028" if hit else "#e2a000", lw=1.4)
        ax.add_patch(plt.Circle((object_distance, 0), object_radius, color="#263238"))
        ax.scatter([0], [0], marker="^", color="#d93535", s=100)
        ax.set_xlim(0, 9)
        ax.set_ylim(-2.6, 2.6)
        ax.set(xlabel="Distance from robot in metres", ylabel="Sideways distance in metres")
        ax.grid(alpha=0.25)
        _figure(st, fig)
        st.info("Object detected by a ray" if any(hits) else "Object missed between rays")
    with tabs[4]:
        st.write("Grid resolution trades detail for storage and computation. A narrow obstacle may occupy several fine cells but be averaged into one coarse cell. Neither view recovers detail that the LiDAR never observed.")
        cell_size = st.select_slider("Cell width in metres", options=(0.25, 0.5, 1.0), value=0.5, key="t2.cell_size")
        width = int(round(6 / cell_size))
        height = int(round(3 / cell_size))
        grid = np.zeros((height, width))
        for row in range(height):
            for column in range(width):
                x = (column + 0.5) * cell_size
                y = (row + 0.5) * cell_size
                grid[row, column] = 1.0 if 3.0 <= x <= 3.4 and 0.8 <= y <= 2.2 else 0.0
        fig, ax = plt.subplots(figsize=(6.2, 2.8))
        ax.imshow(grid, origin="lower", extent=(0, 6, 0, 3), cmap=OCCUPANCY_COLORS, vmin=0, vmax=1, interpolation="nearest")
        ax.add_patch(plt.Rectangle((3.0, 0.8), 0.4, 1.4, fill=False, color="#d93535", lw=2, label="Actual obstacle"))
        ax.set_xticks(np.arange(0, 6.01, cell_size))
        ax.set_yticks(np.arange(0, 3.01, cell_size))
        ax.tick_params(labelsize=6)
        ax.grid(color="white", alpha=0.7, lw=0.5)
        ax.legend(fontsize=8)
        ax.set(xlabel="Width in metres", ylabel="Height in metres")
        _figure(st, fig)
        st.caption("The red outline is the same physical obstacle in every view. The dark cells depend on grid resolution.")
    with tabs[5]:
        st.write("Occupancy is a belief, not a permanent black or white label. A ray passing through a cell is evidence that it is free. A return in that cell is evidence that it is occupied. Conflicting observations update the belief rather than overwriting it with a single answer.")
        a, b = st.columns(2)
        with a:
            free_count = st.slider("Rays that passed through the cell", 0, 8, 2, key="t2.free_count")
        with b:
            hit_count = st.slider("Rays that returned from the cell", 0, 8, 2, key="t2.hit_count")
        log_odds = hit_count * 1.1 - free_count * 0.6
        probability = 1 / (1 + np.exp(-log_odds))
        fig, ax = plt.subplots(figsize=(6.2, 1.8))
        ax.barh([0], [probability], color="#263238", height=0.5)
        ax.barh([0], [1 - probability], left=[probability], color="#d9f1ff", height=0.5)
        ax.axvline(0.5, color="#b72f32", ls="--", lw=1)
        ax.set_xlim(0, 1)
        ax.set_yticks([])
        ax.set_xlabel("Estimated probability of occupancy")
        _figure(st, fig)
        st.metric("Estimated probability that the cell is occupied", f"{probability:.0%}")
        st.caption("The update strengths are chosen for this demonstration. A real mapper uses a sensor model and also accounts for uncertain robot pose.")
    st.info("Every LiDAR observation must be placed using an estimated robot pose. A correct range at the wrong pose can put free and occupied evidence into the wrong cells.")


def rviz(st):
    st.header("Guided Tutorial 3: Read SLAM in RViz")
    st.write("RViz is a viewer for ROS data. Gazebo shows the simulated world. LaserScan shows a current measurement, Odometry shows an estimated robot pose, and Map shows accumulated evidence. These are different kinds of information even when they appear together on one screen.")
    st.image(str(ROOT / "assets" / "turtlebot3_house_plan.png"), caption="Simplified wall plan of TurtleBot3 House. The robot starts near x = -2 m, y = -0.5 m. Check Gazebo for furniture and the live scene.", width=700)
    st.subheader("Open the live displays in the virtual desktop")
    st.write("1. Open the virtual desktop supplied by the course launcher. In its first terminal, change to `/workspace/week06_slam_localization` and start mapping with the command below. Wait for Gazebo and SLAM Toolbox to start. Leave that terminal running.")
    st.code("cd /workspace/week06_slam_localization\nbash scripts/launch_mapping.sh", language="bash")
    st.write("2. Open a second terminal in the virtual desktop and run the command below. It sets ROS domain 26, checks for `/scan`, `/odom`, `/map`, and `/tf`, then opens RViz. Do not start teleoperation yet. You will save your route prediction in Mission 1 before driving.")
    st.code("cd /workspace/week06_slam_localization\nbash scripts/launch_rviz.sh", language="bash")
    st.write("If the command reports missing topics, leave the mapping terminal open and read its error output. Retry after Gazebo and SLAM Toolbox finish starting. If you already have an empty RViz window that shows only `/clicked_point`, `/goal_pose`, and `/initialpose`, close that window and use the command above. That symptom means RViz was started without the Lab 6 ROS domain. In RViz, set Global Options, Fixed Frame to `map`.")
    st.write("3. In RViz, click **Add** at the bottom of the Displays panel. On **By topic**, expand `/map` and add Map, expand `/scan` and add LaserScan, and expand `/odom` and add Odometry. In the Displays panel, click Odometry and change **Keep** from 100 to **1**. This shows the robot's current estimated location without a long trail of old arrows. You do not need RobotModel or TF displays for this lab.")
    st.write("4. Click Map, LaserScan, and Odometry in the Displays panel. Check each Topic and Status. A red status means the data or frame is unavailable. Pan or zoom to inspect the scan relative to the map and the estimated robot location. Keep Gazebo, SLAM, and RViz running when you continue to Mission 1. Do not start another mapping launch there.")
    selected = st.selectbox("What should you inspect in RViz?", ("LaserScan /scan", "Odometry /odom", "Occupancy grid /map", "Unknown region"), key="t3.display")
    explanations = {
        "LaserScan /scan": "Recent range measurements relative to the robot. Select LaserScan and check that its Topic is /scan and its Status is OK.",
        "Odometry /odom": "The estimated robot position and heading. Select Odometry, check that its Topic is /odom, and set Keep to 1 so only the current pose arrow remains.",
        "Occupancy grid /map": "An estimate assembled from many scans. Select Map, set Topic to /map, and watch cells change as the robot explores.",
        "Unknown region": "Gray or unfilled cells have insufficient evidence. Unknown is not the same as free.",
    }
    st.info(explanations[selected])
    st.write("In Mission 1, compare new scan returns against already mapped walls. Watch for alignment, doubled edges, unexplored pockets, and changes to existing structure during a revisit. A map image alone does not prove its geometry is correct.")


RENDERERS = {
    "tutorial_1": motion,
    "tutorial_2": maps,
    "tutorial_3": rviz,
}


def render(st):
    RENDERERS[st.session_state["stage"]](st)
