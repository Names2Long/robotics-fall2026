import base64
import copy
import unittest
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from dataclasses import asdict
import cv2
import numpy as np
from perception.vision_control import VisionSettings, VisionController, observe, bounded_command, VERSION
from perception.robot_evidence import validate_bundle, validate_report, artifacts


def report_fixture(kind='pillar_search',world='pillars'):
    image = np.zeros((30,50,3),np.uint8)
    _,png = cv2.imencode('.png',image)
    return {'schema':VERSION,'run_id':'fixture-'+world,'kind':kind,'world':world,
            'config':asdict(VisionSettings(kind=kind)),'outcome':'interrupted','visited':[],
            'images':{'original':base64.b64encode(png).decode()},
            'rows':[{'elapsed':1.,'frame':1,'linear':0.,'angular':0.,'state':'WAIT_CAMERA'}]}


class LiveVisionTests(unittest.TestCase):
    def test_world_updates_existing_pose_instead_of_adding_ignored_duplicate(self):
        from perception.vision_world import build_world
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root/'model.sdf'
            model.write_text('<sdf><model name="robot"><pose>0 0 0 0 0 0</pose><link name="camera"><sensor type="camera"><update_rate>30</update_rate><camera><image><width>1920</width><height>1080</height></image></camera></sensor></link></model></sdf>')
            for mode in ('pillars','practice','track'):
                output = build_world(mode,model,root/(mode+'.sdf'))
                robot = ET.parse(output).find('.//model[@name="lab7_robot"]')
                self.assertEqual(len(robot.findall('pose')),1)
                if mode == 'practice': self.assertIn('-5.3',robot.find('pose').text)
                if mode == 'track': self.assertIn('2.4 -2.5',robot.find('pose').text)

    def test_pillar_centroid_sign_and_resolution_independence(self):
        for width in (320,640):
            image = np.zeros((240,width,3),np.uint8)
            cv2.rectangle(image,(int(width*.65),60),(int(width*.80),180),(255,0,0),-1)
            obs,images = observe(image,VisionSettings(),'blue')
            self.assertTrue(obs['valid'])
            self.assertGreater(obs['error'],0)
            result = VisionController(VisionSettings(colors='blue')).step(obs,0,1)
            self.assertLess(result['angular'],0)
            self.assertEqual(result['linear'],0)

    def test_pillars_require_distinct_frames_and_hold(self):
        controller = VisionController(VisionSettings(colors='blue'))
        obs = {'valid':True,'target':'blue','error':0.}
        for now in (0.,.2,1.,2.): controller.step(obs,now,1)
        self.assertFalse(controller.done)
        controller.step(obs,2.1,2)
        controller.step(obs,2.2,3)
        controller.step(obs,3.,4)
        self.assertTrue(controller.done)
        self.assertEqual(controller.visited,['blue'])

    def test_missing_stale_and_invalid_evidence_stop(self):
        for kind in ('pillar_search','line_following'):
            c = VisionController(VisionSettings(kind=kind))
            for obs,fresh in ((None,True),({'valid':True},False)):
                out = c.step(obs,0,1,fresh)
                self.assertEqual((out['linear'],out['angular']),(0.,0.))
        for pair in ((float('nan'),0),(0,float('inf')),('1',0)):
            self.assertEqual(bounded_command(*pair),(0.,0.))
        self.assertEqual(bounded_command(1,2),(.18,.6))

    def test_line_loss_and_finish_latch(self):
        c = VisionController(VisionSettings(kind='line_following'))
        obs = {'valid':False,'finish':False,'error':None}
        self.assertEqual(c.step(obs,0,1)['state'],'LINE_LOST')
        obs.update(valid=True,error=-.3)
        out = c.step(obs,1,2)
        self.assertGreater(out['angular'],0)
        self.assertGreater(out['linear'],0)
        obs['finish'] = True
        for f in (3,3,3): c.step(obs,2,f)
        self.assertFalse(c.done)
        for f in (4,5): out = c.step(obs,3,f)
        self.assertTrue(c.done)
        self.assertEqual(out['linear'],0)

    def test_line_mask_and_red_finish(self):
        image = np.zeros((270,480,3),np.uint8)
        image[170:260,200:240] = (255,0,255)
        config = VisionSettings(kind='line_following')
        obs,_ = observe(image,config)
        self.assertTrue(obs['valid'])
        image[170:260,:] = (0,0,255)
        obs,_ = observe(image,config)
        self.assertTrue(obs['finish'])

    def test_report_export_and_world_requirements(self):
        p = report_fixture()
        self.assertEqual(validate_report(p,'pillar_search')['outcome'],'interrupted')
        self.assertIn('camera_timeline.csv',dict(artifacts(p)))
        validate_bundle({'kind':'pillar_search','reports':[p]},'pillar_search')
        line = report_fixture('line_following','practice')
        with self.assertRaises(ValueError): validate_bundle({'kind':'line_following','reports':[line]},'line_following')
        validate_bundle({'kind':'line_following','reports':[line,report_fixture('line_following','track')]},'line_following')
        for key,value in (('outcome','running'),('rows',[]),('images',{})):
            broken = copy.deepcopy(p)
            broken[key] = value
            with self.assertRaises(ValueError): validate_report(broken,'pillar_search')


if __name__ == '__main__': unittest.main()
