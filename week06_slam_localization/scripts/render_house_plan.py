"""Render a student route-planning diagram from the installed House model."""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


MODEL = Path("/opt/ros/jazzy/share/turtlebot3_gazebo/models/turtlebot3_house/model.sdf")
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "turtlebot3_house_plan.png"


def pose(element):
    text = element.findtext("pose", default="0 0 0 0 0 0")
    return [float(value) for value in text.split()]


def rectangle(cx, cy, width, depth, yaw):
    rotation = ((math.cos(yaw), -math.sin(yaw)), (math.sin(yaw), math.cos(yaw)))
    points = []
    for dx, dy in ((-width / 2, -depth / 2), (width / 2, -depth / 2),
                   (width / 2, depth / 2), (-width / 2, depth / 2)):
        points.append((cx + rotation[0][0] * dx + rotation[0][1] * dy,
                       cy + rotation[1][0] * dx + rotation[1][1] * dy))
    return points


def main():
    root = ET.parse(MODEL).getroot()
    house = root.find("model")
    if house is None:
        raise ValueError("House model is missing")
    footprints = []
    for link in house.findall("link"):
        lx, ly, lz, _, _, lyaw = pose(link)
        for collision in link.findall("collision"):
            size_text = collision.findtext("geometry/box/size")
            if not size_text:
                continue
            width, depth, height = (float(value) for value in size_text.split())
            x, y, z, _, _, yaw = pose(collision)
            center_z = lz + z
            if center_z - height / 2 > 0.18 or center_z + height / 2 < 0.10:
                continue
            cx = lx + math.cos(lyaw) * x - math.sin(lyaw) * y
            cy = ly + math.sin(lyaw) * x + math.cos(lyaw) * y
            footprints.append(rectangle(cx, cy, width, depth, lyaw + yaw))
    if not footprints:
        raise ValueError("No wall footprints found")

    fig, ax = plt.subplots(figsize=(8, 5.7), dpi=150)
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    for footprint in footprints:
        ax.add_patch(Polygon(footprint, closed=True, facecolor="#334155", edgecolor="#0f172a", linewidth=0.5))
    ax.scatter([-2.0], [-0.5], s=110, marker="o", color="#d94728", edgecolors="white", linewidths=1.3, zorder=4)
    ax.annotate("Robot start", (-2.0, -0.5), xytext=(8, 9), textcoords="offset points", color="#9a3412", fontsize=10, weight="bold")
    all_x = [x for shape in footprints for x, _ in shape]
    all_y = [y for shape in footprints for _, y in shape]
    ax.set_xlim(min(all_x) - 0.5, max(all_x) + 0.5)
    ax.set_ylim(min(all_y) - 0.5, max(all_y) + 0.5)
    ax.set_aspect("equal")
    ax.grid(color="#cbd5e1", linewidth=0.5, alpha=0.65)
    ax.set_axisbelow(True)
    ax.set_xlabel("World x (m)")
    ax.set_ylabel("World y (m)")
    ax.set_title("TurtleBot3 House wall plan", fontsize=14, weight="bold", color="#172554")
    fig.text(0.5, 0.02, "Simplified wall plan from the installed model. Check Gazebo for furniture and open paths.",
             ha="center", fontsize=8.5, color="#475569")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
