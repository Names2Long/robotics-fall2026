"""Offline experiment orchestration and reusable evidence receipts."""
import json
from pathlib import Path
import subprocess
import sys
import hashlib
import time
from planning.core import START, GOAL, make_map, inflate, fingerprint

ROOT = Path(__file__).resolve().parents[1]


def student_search(source, planner, grid, start=START, goal=GOAL, timeout=12):
    source = Path(source).resolve()
    request = dict(source=str(source),planner=planner,grid=grid,start=start,goal=goal)
    try:
        process = subprocess.run([sys.executable,str(ROOT/'scripts/offline_worker.py')], input=json.dumps(request),
                                 text=True,capture_output=True,timeout=timeout,cwd=ROOT)
        if process.returncode:
            return {'status':'implementation_error','error':process.stderr[-2000:],'path':[]}
        return json.loads(process.stdout.strip().splitlines()[-1])
    except subprocess.TimeoutExpired:
        return {'status':'resource_limit','error':f'Worker exceeded {timeout} seconds','path':[]}
    except (ValueError,IndexError) as exc:
        return {'status':'implementation_error','error':str(exc),'path':[]}


def cases():
    result = {}
    for name in ('diagnostic','open','constrained','unreachable'):
        grid = inflate(make_map('open' if name in ('diagnostic','unreachable') else name))
        start,goal = START,GOAL
        if name == 'diagnostic':
            grid = [[1]*7,[1,0,0,0,0,0,1],[1]*7]
            start,goal = (1,1),(1,5)
        if name == 'unreachable':
            # Small disconnected chambers allow even IDDFS to exhaust the
            # reachable component. Both endpoints remain visibly free.
            grid = [[int(r in (0,4) or c in (0,8) or c==4) for c in range(9)] for r in range(5)]
            start,goal = (2,1),(2,7)
        result[name] = (grid,start,goal)
    return result


def run_offline(source):
    source = Path(source)
    rows = []
    for name,(grid,start,goal) in cases().items():
        for planner in ('bfs','dfs','iddfs','astar'):
            row = student_search(source,planner,grid,start,goal)
            row.update(map=name,planner=planner,map_hash=fingerprint(grid))
            rows.append(row)
    return dict(schema=2,kind='offline',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                created_unix=time.time(),rows=rows)
