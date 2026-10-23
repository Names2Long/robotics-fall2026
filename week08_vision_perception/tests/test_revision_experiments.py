import ast
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import cv2
import numpy as np
from perception.line_program import STARTER,load_program
from perception.vision_control import VisionController
from perception.robot_evidence import validate_bundle

ROOT = Path(__file__).resolve().parents[1]


class RevisionExperimentTests(unittest.TestCase):
    def test_student_code_changes_real_controller_commands(self):
        weak,steer = load_program(STARTER)
        stronger,steer2 = load_program(STARTER.replace('GAIN = 0.08','GAIN = 1.0'))
        obs = {'valid':True,'error':.5,'finish':False}
        a = VisionController(weak,steer).step(obs,0,1)
        b = VisionController(stronger,steer2).step(obs,0,1)
        self.assertLess(abs(a['angular']),abs(b['angular']))
        self.assertEqual(weak.speed,.16)
        config,wrong_sign = load_program(STARTER.replace('return -gain * error','return gain * error'))
        self.assertGreater(VisionController(config,wrong_sign).step(obs,0,1)['angular'],0)

    def test_code_errors_stop_and_safeguards_remain(self):
        config,broken = load_program(STARTER.replace('return -gain * error','return gain / 0'))
        c = VisionController(config,broken)
        out = c.step({'valid':True,'error':.5,'finish':False},0,1)
        self.assertEqual((out['state'],out['linear'],out['angular']),('CODE_ERROR',0.,0.))
        self.assertEqual(c.step(None,1,2,False)['linear'],0)
        for source in (STARTER+'\nimport os',STARTER.replace('return -gain * error','return print(error)'),STARTER.replace('SPEED = 0.16','SPEED = 2.0')):
            with self.assertRaises(ValueError): load_program(source)

    def test_new_program_evidence_requires_different_track_experiments(self):
        from dataclasses import asdict
        from test_live_vision import report_fixture
        p = report_fixture('line_following','practice')
        a = report_fixture('line_following','track')
        a['program'] = STARTER
        a['config'] = asdict(load_program(STARTER)[0])
        from perception.robot_evidence import artifacts
        self.assertEqual(dict(artifacts(a))['controller.py'].decode(),STARTER)
        with self.assertRaises(ValueError): validate_bundle({'kind':'line_following','reports':[p,a]},'line_following')
        b = copy.deepcopy(a)
        b['run_id'] = 'second'
        b['program'] = STARTER.replace('GAIN = 0.08','GAIN = 0.8')
        b['config'] = asdict(load_program(b['program'])[0])
        validate_bundle({'kind':'line_following','reports':[p,a,b]},'line_following')

    def test_reference_covers_all_operations_and_matches_common_mask(self):
        spec = importlib.util.spec_from_file_location('playground_reference',ROOT/'scripts/playground_reference.py')
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)
        from perception.dataset import tuning_image,source_mask
        image = tuning_image()
        outputs,measures = reference.demonstrate(image,source_mask())
        mask = cv2.inRange(cv2.cvtColor(image,cv2.COLOR_BGR2HSV),np.array([0,70,25]),np.array([35,255,180]))
        self.assertTrue(np.array_equal(outputs['raw_mask'],mask))
        for name in ('erosion','dilation','opening','closing'):
            for size in (1,3,5,9): self.assertIn(f'{name}_{size}',outputs)
        self.assertNotEqual(measures['box_center'],measures['centroid'])
        self.assertTrue(np.array_equal(image,tuning_image()))

    def test_reflection_prompt_matches_lab_6_exactly(self):
        from lab.final_reflection import PROMPTS
        tree = ast.parse((ROOT.parent/'week06_slam_localization/lab/final_reflection.py').read_text(encoding='utf-8'))
        original = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROMPTS' for t in node.targets))
        self.assertEqual(PROMPTS,original)
