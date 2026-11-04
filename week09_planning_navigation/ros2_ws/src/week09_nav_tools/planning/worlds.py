"""Create matched occupancy maps and Gazebo worlds without downloaded models."""
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml
from .core import make_map, cell_to_world, START, RESOLUTION, ORIGIN, MAX_SPEED
from .social import PEOPLE


def material(visual,color):
    surface = ET.SubElement(visual,'material')
    ET.SubElement(surface,'ambient').text = color
    ET.SubElement(surface,'diffuse').text = color


def box(world,name,x,y,sx,sy,height=1,color='.45 .65 .82 1'):
    model = ET.SubElement(world,'model',name=name)
    ET.SubElement(model,'static').text = 'true'
    ET.SubElement(model,'pose').text = f'{x} {y} {height/2} 0 0 0'
    link = ET.SubElement(model,'link',name='body')
    for tag in ('collision','visual'):
        item = ET.SubElement(link,tag,name=tag)
        shape = ET.SubElement(ET.SubElement(item,'geometry'),'box')
        ET.SubElement(shape,'size').text = f'{sx} {sy} {height}'
        if tag == 'visual':
            material(item,color)


def generate(name, output, models, nav_params, social=False):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    people = PEOPLE if social else ()
    grid = make_map(name,people)
    # ROS map files have their first image row at the top.
    # Preserve physical geometry while giving Nav2 a normal 5-cm costmap.
    scale = 5
    pixels = bytes(0 if cell else 254 for row in reversed(grid) for _ in range(scale) for cell in row for _ in range(scale))
    (output/'map.pgm').write_bytes(b'P5\n200 160\n255\n'+pixels)
    mapfile = output/'map.yaml'
    mapfile.write_text(yaml.safe_dump(dict(image='map.pgm',resolution=RESOLUTION/scale,origin=[*ORIGIN,0.0],negate=0,
                                          occupied_thresh=.65,free_thresh=.25)),encoding='utf-8')
    root = ET.Element('sdf',version='1.9')
    world = ET.SubElement(root,'world',name='lab8')
    scene = ET.SubElement(world,'scene')
    ET.SubElement(scene,'ambient').text = '.65 .65 .65 1'
    ET.SubElement(scene,'background').text = '.78 .86 .94 1'
    for name_system,filename in [('Physics','physics'),('UserCommands','user-commands'),('SceneBroadcaster','scene-broadcaster'),('Sensors','sensors'),('Imu','imu')]:
        plugin = ET.SubElement(world,'plugin',filename=f'gz-sim-{filename}-system',name=f'gz::sim::systems::{name_system}')
        if name_system == 'Sensors':
            ET.SubElement(plugin,'render_engine').text = 'ogre2'
    physics = ET.SubElement(world,'physics',name='physics',type='ignored')
    ET.SubElement(physics,'max_step_size').text = '.002'
    ET.SubElement(physics,'real_time_factor').text = '1'
    light = ET.SubElement(world,'light',name='sun',type='directional')
    ET.SubElement(light,'direction').text = '-.3 .2 -1'
    ET.SubElement(light,'diffuse').text = '.8 .8 .8 1'
    box(world,'floor',0,0,12,10,.02,color='.82 .84 .80 1')
    raw = make_map(name)
    # Merge each contiguous occupied row into a single static wall segment.
    for r,row in enumerate(raw):
        c = 0
        while c < len(row):
            if not row[c]:
                c += 1
                continue
            first = c
            while c < len(row) and row[c]:
                c += 1
            x,y = cell_to_world((r,first))
            exterior = r in (0,31) or first==0 or c==40
            color = '.32 .48 .68 1' if exterior else '.72 .47 .24 1'
            box(world,f'wall_{r}_{first}',x+(c-first-1)*RESOLUTION/2,y,(c-first)*RESOLUTION,RESOLUTION,color=color)
    for i,p in enumerate(people):
        person = ET.SubElement(world,'model',name=f'person_{i}')
        ET.SubElement(person,'static').text = 'true'
        ET.SubElement(person,'pose').text = f"{p['x']} {p['y']} .65 0 0 0"
        link = ET.SubElement(person,'link',name='body')
        for tag in ('collision','visual'):
            item = ET.SubElement(link,tag,name=tag)
            cylinder = ET.SubElement(ET.SubElement(item,'geometry'),'cylinder')
            ET.SubElement(cylinder,'radius').text = str(p['radius'])
            ET.SubElement(cylinder,'length').text = '1.3'
            if tag == 'visual':
                material(item,'.95 .4 .12 1')
    robot = ET.parse(Path(models)/'turtlebot3_burger/model.sdf').getroot().find('model')
    robot.set('name','burger')
    pose = robot.find('pose')
    if pose is None:
        pose = ET.SubElement(robot,'pose')
    x,y = cell_to_world(START)
    pose.text = f'{x} {y} .02 0 0 0'
    world.append(robot)
    ET.indent(root)
    ET.ElementTree(root).write(output/'world.sdf',encoding='utf-8',xml_declaration=True)
    params = yaml.safe_load(Path(nav_params).read_text())
    params['map_server']['ros__parameters']['yaml_filename'] = str(mapfile.resolve())
    amcl = params['amcl']['ros__parameters']
    amcl.update(set_initial_pose=True,always_reset_initial_pose=True,initial_pose=dict(x=x,y=y,z=0.0,yaw=0.0))
    controller = params['controller_server']['ros__parameters']
    # A path-following controller handles right-angle student routes without
    # adding an unreported path-smoothing intervention to selected planners.
    controller['FollowPath'] = dict(plugin='nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController',
        desired_linear_vel=MAX_SPEED,lookahead_dist=.45,min_lookahead_dist=.3,max_lookahead_dist=.8,
        use_velocity_scaled_lookahead_dist=False,use_rotate_to_heading=True,rotate_to_heading_min_angle=.5,
        rotate_to_heading_angular_vel=.8,max_angular_accel=3.2,transform_tolerance=.5,
        use_collision_detection=True,max_allowed_time_to_collision_up_to_carrot=1.0,
        use_regulated_linear_velocity_scaling=True,regulated_linear_scaling_min_speed=.04,
        use_cost_regulated_linear_velocity_scaling=True,cost_scaling_dist=.3,cost_scaling_gain=1.0,
        inflation_cost_scaling_factor=3.0,min_approach_linear_velocity=.03)
    # The task specifies a destination position, not a parking orientation.
    # Do not fail an otherwise completed route while chasing an arbitrary
    # tangent/yaw supplied by the final planner segment.
    controller['goal_checker'] = dict(plugin='nav2_controller::PositionGoalChecker',
                                     xy_goal_tolerance=.25,stateful=True)
    # Downstream smoothing must not silently retain the old Burger speed cap.
    smoother = params.setdefault('velocity_smoother',{}).setdefault('ros__parameters',{})
    smoother['max_velocity'] = [MAX_SPEED,0.0,1.0]
    smoother['min_velocity'] = [-MAX_SPEED,0.0,-1.0]
    # Ten-Hz rendered lidar can arrive just over 0.2 s late in software rendering.
    # Keep stale-data stopping, but do not stop on normal transport jitter.
    params['collision_monitor']['ros__parameters']['scan']['source_timeout'] = .75
    params['planner_server']['ros__parameters']['GridBased'] = dict(
        plugin='nav2_smac_planner::SmacPlanner2D',tolerance=.25,allow_unknown=False,
        downsample_costmap=False,max_iterations=1000000,max_planning_time=5.0,
        cost_travel_multiplier=2.0,use_final_approach_orientation=True)
    for costmap in ('local_costmap','global_costmap'):
        params[costmap][costmap]['ros__parameters']['robot_radius'] = .18
    for section in params.values():
        if isinstance(section,dict) and 'ros__parameters' in section:
            section['ros__parameters']['use_sim_time'] = True
    paramsfile = output/'nav2.yaml'
    paramsfile.write_text(yaml.safe_dump(params),encoding='utf-8')
    return output/'world.sdf',mapfile,paramsfile
