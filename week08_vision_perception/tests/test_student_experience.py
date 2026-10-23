import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from perception.dataset import samples, tuning_image, fingerprint, REFERENCE_BOX
from perception.experiments import run, validate
from lab.pixel_picker import coordinates
from lab_config import LAB


class StudentExperienceTests(unittest.TestCase):
    def test_pixel_event_updates_both_slider_keys_only_once(self):
        from lab.pixel_picker import picker
        st = SimpleNamespace(session_state={})
        component = lambda **kwargs: {'x':300, 'y':50, 'token':'click-1'}
        with patch('streamlit.components.v1.declare_component', return_value=component):
            picker(st, tuning_image())
            self.assertEqual((st.session_state['lesson.pixel_x'], st.session_state['lesson.pixel_y']), (300,50))
            st.session_state['lesson.pixel_x'] = 20
            picker(st, tuning_image())
            self.assertEqual(st.session_state['lesson.pixel_x'],20)

    def test_click_coordinates_and_malformed_values(self):
        self.assertEqual(coordinates({'x':123.9,'y':40},480,320), (123,40))
        for value in (None, {}, {'x':float('nan'),'y':1}, {'x':-1,'y':0},
                      {'x':480,'y':0}, {'x':True,'y':1}, {'x':'1','y':2}, {'x':1,'y':320}):
            self.assertIsNone(coordinates(value,480,320))

    def test_scene_cache_is_immutable_and_metadata_independent(self):
        first, second = samples(), samples()
        self.assertIs(first[0]['image'], second[0]['image'])
        self.assertFalse(first[0]['image'].flags.writeable)
        first[0]['reference_box'][0] = 999
        self.assertNotEqual(first[0]['reference_box'], samples()[0]['reference_box'])
        a = tuning_image()
        a[:] = 0
        self.assertTrue(tuning_image().any())
        self.assertEqual(fingerprint(),fingerprint())

    def test_frozen_inference_is_reused_and_validation_not_aliased(self):
        evidence = run('learned')
        from perception.learned import FrozenDetector
        with patch.object(FrozenDetector,'predict',side_effect=AssertionError('Inference reran')):
            repeated = run('learned')
        self.assertEqual(evidence, repeated)
        first = validate(evidence,'learned')
        first['metrics']['sample_count'] = -1
        self.assertEqual(validate(evidence,'learned')['metrics']['sample_count'],31)
        repeated['rows'][0]['condition'] = 'not-a-condition'
        with self.assertRaises(ValueError): validate(repeated,'learned')

    def test_active_flow_has_one_investigation_not_behavior(self):
        self.assertEqual(LAB.stages, ('intro','preflight','concepts','investigation','pillar_search','line_following','final'))
        self.assertNotIn('mission_3', LAB.missions)
        from lab.completion import QUESTIONS
        self.assertNotIn('mission_3', QUESTIONS)

    def test_playground_has_separate_operations_and_no_inherited_pipeline(self):
        from pages.concepts import STEPS, EXPLANATIONS, FIXED_MASK
        self.assertEqual(len(STEPS),16)
        self.assertEqual(STEPS[4:6],('Resize','Crop'))
        self.assertIn('not a prediction', EXPLANATIONS[-1])
        self.assertIn('raw_mask',FIXED_MASK)
