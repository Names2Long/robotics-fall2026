from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import yaml
from planning.worlds import generate
from planning.core import make_map,START,cell_to_world,MAX_SPEED


class WorldTests(unittest.TestCase):
    def test_generated_map_geometry_and_common_footprint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            model = root/'models/turtlebot3_burger/model.sdf'
            model.parent.mkdir(parents=True)
            model.write_text('<sdf version="1.9"><model name="robot"><pose>0 0 0 0 0 0</pose></model></sdf>')
            data = {name:{'ros__parameters':{}} for name in ('map_server','amcl','controller_server','planner_server')}
            data['collision_monitor'] = {'ros__parameters':{'scan':{}}}
            for name in ('local_costmap','global_costmap'):
                data[name] = {name:{'ros__parameters':{}}}
            params = root/'base.yaml'
            params.write_text(yaml.safe_dump(data))
            world,mapfile,config = generate('constrained',root/'out',root/'models',params)
            metadata = yaml.safe_load(mapfile.read_text())
            self.assertEqual(metadata['resolution'],.05)
            pixels = (root/'out/map.pgm').read_bytes().split(b'\n',3)[3]
            self.assertEqual(len(pixels),200*160)
            raw = make_map('constrained')
            for r in range(32):
                for c in range(40):
                    self.assertEqual(pixels[(31-r)*5*200+c*5],0 if raw[r][c] else 254)
            generated = yaml.safe_load(config.read_text())
            self.assertEqual(generated['global_costmap']['global_costmap']['ros__parameters']['robot_radius'],.18)
            self.assertIn('SmacPlanner2D',generated['planner_server']['ros__parameters']['GridBased']['plugin'])
            robot = ET.parse(world).getroot().find("world/model[@name='burger']")
            pose = [float(v) for v in robot.findtext('pose').split()]
            self.assertEqual(tuple(pose[:2]),cell_to_world(START))
            self.assertEqual(len(robot.findall('pose')),1)
            visuals = ET.parse(world).getroot().findall('world/model/link/visual')
            self.assertTrue(all(v.find('material/diffuse') is not None for v in visuals))
            self.assertGreaterEqual(len({v.findtext('material/diffuse') for v in visuals}),3)
            self.assertEqual(generated['controller_server']['ros__parameters']['FollowPath']['desired_linear_vel'],MAX_SPEED)
            self.assertEqual(generated['velocity_smoother']['ros__parameters']['max_velocity'][0],MAX_SPEED)
            self.assertEqual(generated['controller_server']['ros__parameters']['goal_checker']['plugin'],
                             'nav2_controller::PositionGoalChecker')


if __name__=='__main__':
    unittest.main()
