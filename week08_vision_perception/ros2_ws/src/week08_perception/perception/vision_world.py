"""Generate self-contained modern Gazebo teaching worlds from the original artwork."""
from pathlib import Path
import xml.etree.ElementTree as ET
from perception.dataset import ROOT


def build_world(mode, model_path, output, yaw=0.):
    if mode not in ('pillars','practice','track'): raise ValueError('Choose pillars, practice or track')
    robot = ET.parse(model_path).getroot().find('model')
    robot.set('name','lab7_robot')
    # Lower image cost than the original 1920 by 1080 camera.
    camera = robot.find(".//sensor[@type='camera']")
    if camera is None: raise ValueError('Installed Waffle model has no camera')
    camera.find('update_rate').text = '10'
    camera.find('camera/image/width').text = '640'
    camera.find('camera/image/height').text = '360'
    ET.SubElement(camera,'pose').text = '0 0 0 0 '+('0' if mode == 'pillars' else '0.4')+' 0'
    # Keep the camera and IMU only. The mission does not need a rendered lidar scan.
    for link in robot.findall('link'):
        for sensor in list(link.findall('sensor')):
            if sensor.get('type') in ('gpu_lidar','gpu_ray','ray'): link.remove(sensor)
    start = {'pillars':(0,0,yaw), 'practice':(0,-5.3,1.5708+yaw), 'track':(2.4,-2.5,3.14159+yaw)}[mode]
    pose = robot.find('pose')
    if pose is None: pose = ET.SubElement(robot,'pose')
    pose.text = f'{start[0]} {start[1]} .015 0 0 {start[2]}'
    root = ET.Element('sdf',version='1.9')
    world = ET.SubElement(root,'world',name='lab7_vision')
    for name in ('Physics','UserCommands','SceneBroadcaster','Sensors','Imu'):
        filename = {'Physics':'physics','UserCommands':'user-commands','SceneBroadcaster':'scene-broadcaster','Sensors':'sensors','Imu':'imu'}[name]
        plugin = ET.SubElement(world,'plugin',filename=f'gz-sim-{filename}-system',name=f'gz::sim::systems::{name}')
        if name == 'Sensors': ET.SubElement(plugin,'render_engine').text = 'ogre2'
    physics = ET.SubElement(world,'physics',name='physics',type='ignored')
    ET.SubElement(physics,'max_step_size').text = '.002'
    ET.SubElement(physics,'real_time_factor').text = '1'
    scene = ET.SubElement(world,'scene')
    ET.SubElement(scene,'ambient').text = '.65 .65 .65 1'
    ET.SubElement(scene,'background').text = '.65 .7 .75 1'
    ET.SubElement(scene,'shadows').text = 'false'
    light = ET.SubElement(world,'light',name='sun',type='directional')
    ET.SubElement(light,'pose').text = '0 0 10 0 0 0'
    ET.SubElement(light,'diffuse').text = '.8 .8 .8 1'
    ET.SubElement(light,'specular').text = '.1 .1 .1 1'
    ET.SubElement(light,'direction').text = '-.3 .2 -1'
    floor = ET.SubElement(world,'model',name='floor')
    ET.SubElement(floor,'static').text = 'true'
    link = ET.SubElement(floor,'link',name='floor')
    size = '6 6' if mode == 'pillars' else '4 12' if mode == 'practice' else '8 8'
    for tag in ('collision','visual'):
        part = ET.SubElement(link,tag,name=tag)
        plane = ET.SubElement(ET.SubElement(part,'geometry'),'plane')
        ET.SubElement(plane,'normal').text = '0 0 1'
        ET.SubElement(plane,'size').text = size
        if tag == 'visual':
            material = ET.SubElement(part,'material')
            if mode == 'pillars':
                ET.SubElement(material,'ambient').text = '.5 .5 .5 1'
                ET.SubElement(material,'diffuse').text = '.5 .5 .5 1'
            else:
                ET.SubElement(material,'diffuse').text = '1 1 1 1'
                metal = ET.SubElement(ET.SubElement(material,'pbr'),'metal')
                ET.SubElement(metal,'albedo_map').text = (ROOT/'assets/robot_worlds'/('practice.png' if mode == 'practice' else 'track.png')).as_uri()
                ET.SubElement(metal,'metalness').text = '0'
                ET.SubElement(metal,'roughness').text = '1'
    if mode == 'pillars':
        colors = [('turquoise',-.6,-.6,'0 1 1 1'),('green',-.6,.6,'0 1 0 1'),('blue',.6,-.6,'0 0 1 1'),('red',.6,.6,'1 0 0 1')]
        for name,x,y,color in colors:
            pillar = ET.SubElement(world,'model',name=name)
            ET.SubElement(pillar,'static').text = 'true'
            ET.SubElement(pillar,'pose').text = f'{x} {y} .25 0 0 0'
            link = ET.SubElement(pillar,'link',name=name)
            for tag in ('collision','visual'):
                part = ET.SubElement(link,tag,name=tag)
                cylinder = ET.SubElement(ET.SubElement(part,'geometry'),'cylinder')
                ET.SubElement(cylinder,'radius').text = '.15'
                ET.SubElement(cylinder,'length').text = '.5'
                if tag == 'visual':
                    material = ET.SubElement(part,'material')
                    ET.SubElement(material,'ambient').text = color
                    ET.SubElement(material,'diffuse').text = color
    world.append(robot)
    overview = ET.SubElement(world,'model',name='overview')
    ET.SubElement(overview,'static').text = 'true'
    ET.SubElement(overview,'pose').text = '0 0 11 0 1.570796 0'
    sensor = ET.SubElement(ET.SubElement(overview,'link',name='camera'),'sensor',name='overview',type='camera')
    ET.SubElement(sensor,'topic').text = '/lab7/world_view'
    ET.SubElement(sensor,'update_rate').text = '1'
    camera = ET.SubElement(sensor,'camera')
    ET.SubElement(camera,'horizontal_fov').text = '1.3'
    image = ET.SubElement(camera,'image')
    ET.SubElement(image,'width').text = '512'
    ET.SubElement(image,'height').text = '512'
    clip = ET.SubElement(camera,'clip')
    ET.SubElement(clip,'near').text = '.1'
    ET.SubElement(clip,'far').text = '30'
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(root)
    ET.ElementTree(root).write(output,encoding='utf-8',xml_declaration=True)
    import json, uuid
    active = output.parent/'active.json'
    active.write_text(json.dumps({'mode':mode,'run_id':uuid.uuid4().hex,'yaw_offset':yaw}),encoding='utf-8')
    return output
