"""Generate the Gazebo cup delivery room using the installed TurtleBot3 model."""
from pathlib import Path
import xml.etree.ElementTree as ET


def box(world, name, xyz, size, color, collision=True):
    model = ET.SubElement(world, "model", name=name)
    ET.SubElement(model, "static").text = "true"
    ET.SubElement(model, "pose").text = f"{xyz} 0 0 0"
    link = ET.SubElement(model, "link", name=name)
    for tag in (("collision", "visual") if collision else ("visual",)):
        part = ET.SubElement(link, tag, name=tag)
        ET.SubElement(ET.SubElement(ET.SubElement(part, "geometry"), "box"), "size").text = size
        if tag == "visual":
            material = ET.SubElement(part, "material")
            ET.SubElement(material, "ambient").text = color
            ET.SubElement(material, "diffuse").text = color


def build(model_path, output):
    root = ET.Element("sdf", version="1.9")
    world = ET.SubElement(root, "world", name="lab10_handover")
    for name, filename in (("Physics", "physics"), ("UserCommands", "user-commands"),
                           ("SceneBroadcaster", "scene-broadcaster"), ("Imu", "imu"), ("Sensors", "sensors")):
        plugin = ET.SubElement(world, "plugin", filename=f"gz-sim-{filename}-system",
                               name=f"gz::sim::systems::{name}")
        if name == "Sensors":
            ET.SubElement(plugin, "render_engine").text = "ogre2"
    physics = ET.SubElement(world, "physics", name="physics", type="ignored")
    ET.SubElement(physics, "max_step_size").text = ".002"
    ET.SubElement(physics, "real_time_factor").text = "1"
    scene = ET.SubElement(world, "scene")
    ET.SubElement(scene, "ambient").text = ".75 .75 .75 1"
    ET.SubElement(scene, "background").text = ".8 .85 .9 1"
    light = ET.SubElement(world, "light", name="sun", type="directional")
    ET.SubElement(light, "direction").text = "-.3 -.2 -1"
    ET.SubElement(light, "diffuse").text = ".9 .9 .9 1"
    box(world, "floor", "2.5 0 -.06", "8 4 .1", ".84 .87 .9 1")
    box(world, "back_wall", "2.5 -1.8 .5", "8 .1 1", ".4 .55 .65 1")
    box(world, "person_station", "0 .85 .4", ".65 .5 .8", ".2 .65 .35 1")
    box(world, "red_cup_table", "3 -.8 .3", ".7 .6 .6", ".65 .42 .22 1")
    box(world, "blue_cup_table", "5 -.8 .3", ".7 .6 .6", ".65 .42 .22 1")
    for name, x, color in (("red", 3, ".9 .1 .1 1"), ("blue", 5, ".1 .25 1 1")):
        box(world, name+"_cup", f"{x} -.8 .72", ".16 .16 .24", color)
        box(world, name+"_docking_pad", f"{x} 0 .001", ".4 .7 .005", color, collision=False)
    box(world, "handover_pad", "0 0 .001", ".4 .7 .005", ".2 .8 .4 1", collision=False)
    box(world, "correction_checkpoint", "2 0 .003", ".12 .8 .005", "1 .75 .1 1", collision=False)
    robot = ET.parse(model_path).getroot().find("model")
    robot.set("name", "lab10_robot")
    pose = robot.find("pose")
    if pose is None:
        pose = ET.SubElement(robot, "pose")
    pose.text = "0 0 .02 0 0 0"
    for link in robot.findall("link"):
        for sensor in list(link.findall("sensor")):
            if sensor.get("type") not in ("imu",):
                link.remove(sensor)
    world.append(robot)
    overview = ET.SubElement(world, "model", name="room_camera")
    ET.SubElement(overview, "static").text = "true"
    ET.SubElement(overview, "pose").text = "2.5 0 8 0 1.570796 1.570796"
    sensor = ET.SubElement(ET.SubElement(overview, "link", name="camera"),
                           "sensor", name="overview", type="camera")
    ET.SubElement(sensor, "topic").text = "/lab10/world_view"
    ET.SubElement(sensor, "update_rate").text = "2"
    camera = ET.SubElement(sensor, "camera")
    ET.SubElement(camera, "horizontal_fov").text = "1.1"
    image = ET.SubElement(camera, "image")
    ET.SubElement(image, "width").text = "800"
    ET.SubElement(image, "height").text = "400"
    clip = ET.SubElement(camera, "clip")
    ET.SubElement(clip, "near").text = ".1"
    ET.SubElement(clip, "far").text = "20"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root)
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
    return output
