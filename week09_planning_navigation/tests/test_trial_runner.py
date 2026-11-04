"""Matching-result reuse is conservative and never hides setup failures."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from planning.core import EXPERIMENT_VERSION,fingerprint


@unittest.skipUnless(os.name=='posix','The ROS trial runner uses a Linux process lock')
class RunnerTests(unittest.TestCase):
    def test_exited_launcher_does_not_leave_a_live_grandchild(self):
        import signal
        import subprocess
        import sys
        import time
        script = Path(__file__).resolve().parents[1]/'scripts/run_trials.py'
        spec = importlib.util.spec_from_file_location('lab8_cleanup_integration',script)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        program = "import subprocess,signal,sys; signal.signal(signal.SIGINT,signal.SIG_IGN); child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); print(child.pid,flush=True)"
        parent = subprocess.Popen([sys.executable,'-c',program],stdout=subprocess.PIPE,text=True,start_new_session=True)
        try:
            child = int(parent.stdout.readline())
            parent.wait(timeout=5)
            runner.stop_group(parent)
            deadline = time.monotonic()+3
            while time.monotonic()<deadline:
                status = Path(f'/proc/{child}/stat')
                if not status.exists() or status.read_text().split()[2]=='Z':
                    break
                time.sleep(.05)
            else:
                self.fail('The grandchild was still running after its launcher exited')
        finally:
            try:
                os.killpg(parent.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            parent.wait()
            parent.stdout.close()

    def test_transport_is_private_and_cleanup_kills_remaining_children(self):
        import signal
        from unittest.mock import Mock,patch
        script = Path(__file__).resolve().parents[1]/'scripts/run_trials.py'
        spec = importlib.util.spec_from_file_location('lab8_trial_cleanup',script)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        original = os.environ.get('GZ_PARTITION')
        self.assertNotEqual(runner.trial_environment('first')['GZ_PARTITION'],runner.trial_environment('second')['GZ_PARTITION'])
        self.assertEqual(os.environ.get('GZ_PARTITION'),original)
        process = Mock(pid=12345)
        # Parent exits normally, but there may still be grandchildren.
        process.wait.return_value = 0
        with patch.object(runner.os,'killpg') as kill:
            runner.stop_group(process)
        self.assertEqual(kill.call_args_list[0].args,(12345,signal.SIGINT))
        self.assertEqual(kill.call_args_list[-1].args,(12345,signal.SIGKILL))

    def test_reuse_requires_matching_source_settings_protocol_and_outcome(self):
        script = Path(__file__).resolve().parents[1]/'scripts/run_trials.py'
        spec = importlib.util.spec_from_file_location('lab8_trial_runner',script)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        field = dict(human_gain=.1,influence_m=1.0,step_m=.08)
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory)/'run/result.json'
            result.parent.mkdir()
            row = dict(experiment_version=EXPERIMENT_VERSION,mission='3',map='open',planner='astar',seed=0,
                       condition='social_1',map_hash='map',source_sha256='source',field_hash=fingerprint(field),
                       timeout_s=180,status='succeeded')
            def reuse():
                return runner.reusable_result(directory,'3','open','astar',0,'social_1','map','source',field,180,{'succeeded'})
            result.write_text(json.dumps(row))
            self.assertTrue(reuse())
            for key,value in [('source_sha256','changed'),('experiment_version',EXPERIMENT_VERSION-1),
                              ('status','environment_error'),('timeout_s',240),('field_hash','changed')]:
                invalid = dict(row)
                invalid[key] = value
                result.write_text(json.dumps(invalid))
                self.assertFalse(reuse(),msg=key)


if __name__=='__main__':
    unittest.main()
