from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from missions import mission_1 as m1, mission_2 as m2, mission_3 as m3
from simulation.kinematics import SEQUENCES, integrate_sequence

class MissionTests(unittest.TestCase):
    def test_motion_gate(self):
        from lab.motion_trials import modeled_trial
        locked="2026-08-31T00:00:00+00:00"
        responses={"mission_1.predictions":{name:{"id":name,"saved_at":locked,"description":"Prediction"} for name in SEQUENCES},
                   "mission_1.sketch":{"data":"test"},
                   **{f"mission_1.compare.{name}":"Comparison" for name in SEQUENCES},
                   **{f"mission_1.{key}":"Explanation" for key in m1.REFLECTIONS}}
        runs=[modeled_trial(name,name) for name in SEQUENCES]
        self.assertTrue(m1.evaluate(runs,responses).passed)
        runs[0]["prediction_id"]="stale"
        self.assertFalse(m1.evaluate(runs,responses).passed)
    def test_frame_gate(self):
        from lab.frame_learning import reference_snapshot
        snapshot=reference_snapshot()
        responses={"mission_2.snapshot":snapshot,**{f"mission_2.{key}":"Explanation" for key in m2.REFLECTIONS}}
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/"camera_transform.py";source.write_text("# revised")
            lock={"integrity_valid":True};result={"file_present":True,"source_sha256":m2.current_hash(source),
                "unit_tests_passed":True,"test_count":5,"source_differs_from_original":True,"live_passed":True}
            self.assertTrue(m2.evaluate(result,lock,responses,source).passed)
            result["test_count"]=4
            self.assertFalse(m2.evaluate(result,lock,responses,source).passed)
    def test_ai_gate(self):
        lock={"pattern":"l_path","locked_at":"now","prompt_sha256":"a","output_sha256":"b","integrity_valid":True}; result={"pattern":"l_path","unit_tests_passed":True,"integration_passed":True,"commands_bounded":True,"final_stop_verified":True,"source_differs_from_original":True,"test_count":7}; responses={f"mission_3.{key}":"Substantive evidence-based individual analysis. "*3 for key in m3.REFLECTIONS}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for relative in ("week03_pattern/pattern.py","week03_pattern/pattern_node.py","test/test_student_pattern.py"):
                path=root/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_text("# source\n"+"x=1\n"*40,encoding="utf-8")
            lock['source_sha256']='original'
            result.update(source_sha256=m3.current_hash(root),shape_check_passed=True,model_stop_passed=True,test_count=9,
                          implementation_present=True,student_test_file_present=True,student_test_count=2)
            self.assertTrue(m3.evaluate(result,lock,responses,root).passed)
            result['final_stop_verified']=False
            self.assertFalse(m3.evaluate(result,lock,responses,root).passed)
            responses.update({'mission_3.live_pending':True,'mission_3.live_issue':'No ROS connection'})
            self.assertTrue(m3.evaluate(result,lock,responses,root).passed)
            (root/'week03_pattern/pattern.py').write_text('changed')
            self.assertFalse(m3.evaluate(result,lock,responses,root).passed)
if __name__=="__main__": unittest.main()
