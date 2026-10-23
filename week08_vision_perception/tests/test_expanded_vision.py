import unittest
import numpy as np
import cv2
from perception.dataset import samples,tuning_image,source_mask,REFERENCE_BOX
from perception.classical import Settings,process
from perception.representations import classify,segment
from perception.visual_experiments import encode,decode
from perception.learned import suppress_duplicates
from evaluation.metrics import mask_metrics,detection_pr


class ExpandedVisionTests(unittest.TestCase):
    def test_mask_scores_and_empty_convention(self):
        a = np.array([[1,1],[0,0]],bool)
        b = np.array([[1,0],[1,0]],bool)
        result = mask_metrics(a,b)
        self.assertAlmostEqual(result['mask_iou'],1/3)
        self.assertEqual(result['dice'],.5)
        self.assertEqual((result['extra_pixels'],result['missed_pixels']),(1,1))
        self.assertEqual(mask_metrics(np.zeros((2,2)),np.zeros((2,2)))['dice'],1)
        with self.assertRaises(ValueError): mask_metrics(a,np.zeros((3,3)))

    def test_ap_penalizes_false_high_scores_and_duplicate_boxes(self):
        rows = [{'expected':True,'reference_box':[0,0,10,10],
                 'detections':[{'confidence':.9,'bbox':[30,30,10,10]},
                               {'confidence':.8,'bbox':[0,0,10,10]},
                               {'confidence':.7,'bbox':[0,0,10,10]}]}]
        result = detection_pr(rows)
        self.assertAlmostEqual(result['ap50'],.5)
        self.assertEqual([p['recall'] for p in result['points']],[0,1,1])
        self.assertAlmostEqual(result['points'][-1]['precision'],1/3)

    def test_pixel_annotations_are_independent_aligned_silhouettes(self):
        items = {i['image_id']:i for i in samples()}
        self.assertEqual(sum(i['reference_mask'] is not None for i in items.values()),29)
        self.assertIsNone(items['independent_mug']['reference_mask'])
        mask = source_mask()
        self.assertLess(mask.sum(),REFERENCE_BOX[2]*REFERENCE_BOX[3])
        occluded = items['occluded_1']['reference_mask']
        self.assertFalse(occluded[30:116,275:311].any())
        changed = items['background_1']['image']
        original = tuning_image()
        self.assertTrue(np.array_equal(changed[mask],original[mask]))
        self.assertTrue((changed[~mask] != original[~mask]).any())
        self.assertLess(items['far_1']['reference_mask'].sum(),mask.sum()/4)

    def test_preprocessing_and_shape_filters_change_actual_pipeline(self):
        image = np.zeros((100,200,3),np.uint8)
        cv2.rectangle(image,(20,40),(180,55),(220,220,220),-1)
        self.assertTrue(process(image,Settings(min_area=50))['detected'])
        self.assertFalse(process(image,Settings(min_area=50,min_circularity=.9))['detected'])
        self.assertFalse(process(image,Settings(min_area=50,brightness=-80))['detected'])
        result = process(image,Settings(min_area=50,smoothing='median',blur_kernel=3))
        candidate = next(r for r in result['candidates'] if r['eligible'])
        self.assertIsNotNone(candidate['centroid'])
        self.assertGreater(candidate['circularity'],0)

    def test_frozen_models_and_saved_segmentation_scores(self):
        image = tuning_image()
        prediction = classify(image)
        self.assertEqual(len(prediction['top5']),5)
        self.assertTrue(0 <= prediction['cup_score'] <= 1)
        probability = segment(image)
        restored = decode(encode(probability))
        self.assertEqual(restored.shape,image.shape[:2])
        self.assertLessEqual(np.abs(restored-probability).max(),1/255)
        with self.assertRaises(ValueError): decode('not a saved mask')

    def test_nms_overlap_control_changes_retained_proposals(self):
        detections = [{'label':'cup','confidence':.9,'bbox':[0,0,10,10]},
                      {'label':'cup','confidence':.8,'bbox':[1,0,10,10]},
                      {'label':'cup','confidence':.7,'bbox':[30,0,10,10]}]
        self.assertEqual(len(suppress_duplicates(detections,.3)),2)
        self.assertEqual(len(suppress_duplicates(detections,.9)),3)
