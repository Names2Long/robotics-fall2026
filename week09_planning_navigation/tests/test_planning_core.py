import json
import math
import os
from pathlib import Path
import tempfile
import io
import zipfile
import unittest
from collections import deque
from unittest.mock import patch

from planning.core import *
from planning.sampling import sampling_plan
from planning.social import PEOPLE,CONFIGS,refine,trajectory_metrics
from evaluation.experiments import offline_checks,navigation_checks,social_checks
from lab.storage import load,save,submission_root,export


def bfs(ctx):
    queue,parent = deque([ctx.start]),{ctx.start:None}
    while queue:
        cur = queue.popleft()
        if cur==ctx.goal:
            return reconstruct(parent,cur)
        for nxt in ctx.expand(cur,len(queue)+1):
            if nxt not in parent:
                parent[nxt] = cur
                queue.append(nxt)
    return []


class CoreTests(unittest.TestCase):
    def test_maps_connected_and_conversions(self):
        for name in ('open','constrained'):
            grid = inflate(make_map(name))
            path = reference_path(grid)
            self.assertTrue(path)
            self.assertEqual(path[0],START)
            self.assertEqual(path[-1],GOAL)
            for cell in path:
                self.assertEqual(world_to_cell(cell_to_world(cell)),cell)
            self.assertTrue(all(edge_free(grid,cell_to_world(a),cell_to_world(b)) for a,b in zip(path,path[1:])))

    def test_instrumentation_and_invalid_paths(self):
        grid = inflate(make_map('open'))
        row = evaluate_student(bfs,grid)
        self.assertEqual(row['status'],'succeeded')
        self.assertEqual(row['optimality_ratio'],1)
        self.assertGreater(row['expanded'],0)
        self.assertEqual(evaluate_student(lambda ctx:[START,GOAL],grid)['status'],'invalid_path')
        self.assertEqual(evaluate_student(lambda ctx:[],grid)['status'],'missed_path')
        grid[GOAL[0]][GOAL[1]] = 1
        self.assertEqual(evaluate_student(bfs,grid)['status'],'no_path')

    def test_sampling_edges_and_repeatability(self):
        for name in ('open','constrained'):
            grid = inflate(make_map(name))
            for kind in ('rrt','prm'):
                a = sampling_plan(kind,grid,START,GOAL,0)
                b = sampling_plan(kind,grid,START,GOAL,0)
                self.assertEqual(a['path'],b['path'])
                self.assertEqual(a['status'],'succeeded')
                self.assertTrue(all(edge_free(grid,p,q) for p,q in zip(a['path'],a['path'][1:])))

    def test_person_clearance_and_exposure(self):
        rows = [{'t':0,'x':0,'y':0},{'t':2,'x':1,'y':0}]
        metrics = trajectory_metrics(rows,[{'x':1,'y':.5,'radius':.25}])
        self.assertAlmostEqual(metrics['minimum_person_clearance_m'],.07)
        self.assertEqual(metrics['personal_space_s'],2)
        self.assertEqual(metrics['distance_m'],1)
        self.assertEqual(metrics['max_speed_near_people_mps'],.5)

    def test_fields_are_checked_or_explicit_failures(self):
        grid = inflate(make_map('open',PEOPLE))
        path = [cell_to_world(p) for p in reference_path(grid)]
        self.assertEqual(refine(path,grid,PEOPLE,CONFIGS['baseline'])[0],path)
        for name in ('social_1','social_2'):
            result,status = refine(path,grid,PEOPLE,CONFIGS[name])
            self.assertIn(status,('succeeded','obstacle_local_minimum','oscillation','iteration_limit','blocked_goal'))
            self.assertTrue(all(edge_free(grid,p,q) for p,q in zip(result,result[1:])))

    def test_empty_completion_checks_fail(self):
        for checks in (offline_checks({}),navigation_checks([],''),social_checks([])):
            self.assertFalse(all(ok for _,ok in checks))

    def test_failed_social_preview_retains_a_checked_prefix(self):
        grid = inflate(make_map('constrained',PEOPLE))
        path = [cell_to_world(p) for p in reference_path(grid)]
        diagnostic = {}
        result,status = refine(path,grid,PEOPLE,CONFIGS['social_2'],diagnostic)
        if not result:
            self.assertEqual(diagnostic['status'],status)
            self.assertGreater(len(diagnostic['path']),1)
            self.assertTrue(all(edge_free(grid,a,b) for a,b in zip(diagnostic['path'],diagnostic['path'][1:])))

    def test_small_field_does_not_cut_constrained_path_corners(self):
        grid = inflate(make_map('constrained',PEOPLE))
        path = [cell_to_world(p) for p in reference_path(grid)]
        result,status = refine(path,grid,PEOPLE,dict(human_gain=.05,influence_m=1.0,step_m=.08))
        self.assertEqual(status,'succeeded')
        self.assertEqual(result[0],path[0])
        self.assertEqual(result[-1],path[-1])
        self.assertTrue(all(edge_free(grid,a,b) for a,b in zip(result,result[1:])))

    def test_autosave_recovery_and_zip(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'WEEK09_SUBMISSION_DIR':temp}):
            state = dict(stage='mission_1',student={'name':'Test','email':'test'},responses={'answer':'preserve'},evidence={},completed_missions=[],settings={})
            save(state)
            save(state)
            path = Path(temp)/'autosave/responses.json'
            path.write_text('{bad')
            recovered = load()
            self.assertEqual(recovered['responses']['answer'],'preserve')
            self.assertTrue(path.with_suffix('.damaged.json').exists())
            save(recovered)
            data = export(state)
            self.assertTrue(data.startswith(b'PK'))
            self.assertEqual(json.loads((Path(temp)/'manifest.json').read_text())['status'],'draft')

    def test_reports_and_export_hashes(self):
        from lab.application import write_reports
        from lab.storage import sha
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'WEEK09_SUBMISSION_DIR':temp}):
            row = evaluate_student(bfs,inflate(make_map('open')))
            row.update(map='open',planner='bfs')
            write_reports('mission_1',{'rows':[row]})
            self.assertTrue((Path(temp)/'mission_1/open_offline.png').exists())
            self.assertIn('planning_s',(Path(temp)/'mission_1/metrics.csv').read_text())
            state = dict(stage='mission_1',student={},responses={},evidence={},completed_missions=[],settings={})
            data = export(state)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                manifest = json.loads(archive.read('student_submission/manifest.json'))
                self.assertEqual(manifest['files']['mission_1/metrics.csv'],sha(Path(temp)/'mission_1/metrics.csv'))
                self.assertIn('student_submission/mission_1/open_offline.png',archive.namelist())

    def test_export_excludes_interpreter_cache(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'WEEK09_SUBMISSION_DIR':temp}):
            cached = Path(temp)/'mission_1/__pycache__/planners.cpython-312.pyc'
            cached.parent.mkdir(parents=True)
            cached.write_bytes(b'not submission evidence')
            state = dict(stage='intro',student={},responses={},evidence={},completed_missions=[],settings={})
            with zipfile.ZipFile(io.BytesIO(export(state))) as archive:
                self.assertFalse(any('__pycache__' in name for name in archive.namelist()))


if __name__ == '__main__':
    unittest.main()
