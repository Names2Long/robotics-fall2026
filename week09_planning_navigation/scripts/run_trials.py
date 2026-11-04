"""Automated matched trials. Run through scripts/run_trials.sh in the ROS desktop.

Each attempt has a new directory and a fresh simulation/Nav2 process group.
Existing evidence is never overwritten. Launch logs remain with every attempt.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from planning.core import make_map,inflate,START,GOAL,cell_to_world,fingerprint,PLANNERS,EXPERIMENT_VERSION,MAX_SPEED,TRIAL_TIMEOUT
from planning.experiments import student_search
from planning.sampling import sampling_plan
from planning.social import PEOPLE,CONFIGS


def stop_group(process):
    try:
        os.killpg(process.pid,signal.SIGINT)
    except ProcessLookupError:
        process.wait()
        return
    try:
        process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        pass
    finally:
        # A launcher can exit before its Gazebo grandchildren. They still own
        # this group and must not remain alive for the next trial.
        try:
            os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def trial_environment(run_id):
    environment = os.environ.copy()
    environment['GZ_PARTITION'] = 'lab8_planning_'+run_id
    return environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mission',choices=['2','3'],default='2')
    parser.add_argument('--planners',nargs='+',choices=PLANNERS,default=list(PLANNERS))
    parser.add_argument('--maps',nargs='+',choices=['open','constrained'],default=['open','constrained'])
    parser.add_argument('--repeats',type=int,default=1)
    parser.add_argument('--timeout',type=float,default=TRIAL_TIMEOUT)
    parser.add_argument('--source',type=Path,default=ROOT/'student_submission/mission_1/planners.py')
    parser.add_argument('--fields',type=Path,default=ROOT/'config/potential_fields.json')
    parser.add_argument('--output',type=Path,default=ROOT/'runtime/trials')
    parser.add_argument('--gui',action='store_true',default=True,help='Gazebo is visible by default')
    parser.add_argument('--headless',action='store_false',dest='gui',help='Opt out of the Gazebo viewer')
    parser.add_argument('--skip-existing',action='store_true',help='Reuse matching valid results rather than run the same cell again')
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10 or args.timeout <= 0:
        parser.error('Use 1 to 10 repeats and a positive timeout')
    args.output.mkdir(parents=True,exist_ok=True)
    source_hash,source_snapshot = None,None
    if any(p in PLANNERS[:4] for p in args.planners):
        if not args.source.exists():
            parser.error('Save your Mission 1 Python source first, or supply --source with its location')
        source_bytes = args.source.read_bytes()
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        snapshots = ROOT/'runtime/source_snapshots'
        snapshots.mkdir(parents=True,exist_ok=True)
        source_snapshot = snapshots/(source_hash+'.py')
        source_snapshot.write_bytes(source_bytes)
    lock = (ROOT/'runtime/experiment.lock').open('w')
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('Another Lab 8 experiment is running. Stop it before starting another.')
    fields = json.loads(args.fields.read_text()) if args.mission=='3' else CONFIGS
    if args.mission=='3':
        if set(fields) != set(CONFIGS):
            parser.error('Keep baseline, social_1 and social_2 configurations')
        if fields['baseline'] != CONFIGS['baseline']:
            parser.error('Do not alter the human-unaware baseline')
        for config in fields.values():
            if not 0 <= config['human_gain'] <= 5 or not .1 <= config['influence_m'] <= 3 or not .01 <= config['step_m'] <= .15:
                parser.error('Field ranges: gain 0 to 5, influence .1 to 3 m, step .01 to .15 m')
    from evaluation.experiments import OUTCOMES
    conditions = list(fields) if args.mission=='3' else ['baseline']
    total = len(args.maps)*args.repeats*len(args.planners)*len(conditions)
    number = 0
    print(f'Lab 8 Mission {args.mission}: {total} trial cells. Gazebo {"visible" if args.gui else "headless"}. '
          f'Common speed limit {MAX_SPEED:.2f} m/s. Ctrl+C stops safely.',flush=True)
    for map_name in args.maps:
        people = list(PEOPLE) if args.mission=='3' else []
        grid = inflate(make_map(map_name,people))
        for seed in range(args.repeats):
            for planner in args.planners:
                print(f'Planning {planner.upper()} on {map_name}, repeat {seed}.',flush=True)
                planned = {}
                if planner in ('rrt','prm'):
                    planned = sampling_plan(planner,grid,START,GOAL,seed)
                elif planner != 'nav2':
                    planned = student_search(source_snapshot,planner,grid)
                    planned['path'] = [cell_to_world(p) for p in planned.get('path',[])] if planned['status']=='succeeded' else []
                for condition in (list(fields) if people else ['baseline']):
                    number += 1
                    print(f'[{number}/{total}] {map_name} / {planner} / {condition} / repeat {seed}. '
                          f'{total-number} cell(s) remain after this one.',flush=True)
                    if args.skip_existing and reusable_result(args.output,args.mission,map_name,planner,seed,condition,
                            fingerprint(grid),source_hash if planner in PLANNERS[:4] else None,fields[condition],args.timeout,OUTCOMES):
                        print('  Reusing matching recorded outcome. No simulation restart needed.',flush=True)
                        continue
                    attempt = args.output/f'{map_name}_{planner}_{seed}_{condition}_{uuid.uuid4().hex[:10]}'
                    attempt.mkdir()
                    environment = trial_environment(attempt.name)
                    request = dict(schema=2,experiment_version=EXPERIMENT_VERSION,mission=args.mission,run_id=attempt.name,map=map_name,planner=planner,seed=seed,
                                   gazebo_partition=environment['GZ_PARTITION'],
                                   condition=condition,people=people,grid=grid,map_hash=fingerprint(grid),
                                   controller=f'Regulated Pure Pursuit FollowPath {MAX_SPEED:.2f} m/s common controller',timeout_s=args.timeout,
                                   field_config=fields[condition],field_hash=fingerprint(fields[condition]),
                                   source_sha256=source_hash if planner in PLANNERS[:4] else None,
                                   planning_metrics={k:v for k,v in planned.items() if k!='path'},
                                   path=planned.get('path',[]),planning_status=planned.get('status'),planning_s=planned.get('planning_s'))
                    (attempt/'request.json').write_text(json.dumps(request,indent=2))
                    if planner in PLANNERS[:4]:
                        (attempt/'planners.py').write_bytes(source_snapshot.read_bytes())
                    if planner != 'nav2' and planned.get('status')!='succeeded':
                        request.update(status=planned.get('status','planning_failed'),kind='social' if people else 'navigation',error=planned.get('error',''))
                        request.pop('grid')
                        (attempt/'result.json').write_text(json.dumps(request,indent=2))
                        print(attempt.name,request['status'],flush=True)
                        continue
                    with (attempt/'launch.log').open('w') as log:
                        print(f'  Starting Gazebo, localization and Nav2. Logs: {attempt}',flush=True)
                        launch = subprocess.Popen(['ros2','launch','week09_nav_tools','experiment.launch.py',f'map_name:={map_name}',
                            f'output:={attempt.resolve()}',f'social:={str(bool(people)).lower()}',f'gui:={str(args.gui).lower()}'],
                            stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=environment)
                        try:
                            # Probe bounds action readiness and execution. No fixed sleep is needed.
                            probe = subprocess.Popen(['ros2','run','week09_nav_tools','experiment_probe','--ros-args','-p','use_sim_time:=true',
                                '-p',f'request:={attempt.resolve()}/request.json','-p',f'output:={attempt.resolve()}/result.json'],
                                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True,env=environment)
                            output = ''
                            try:
                                deadline = time.monotonic()+args.timeout*3+150
                                while True:
                                    try:
                                        output,_ = probe.communicate(timeout=min(10,max(.1,deadline-time.monotonic())))
                                        break
                                    except subprocess.TimeoutExpired:
                                        progress = attempt/'progress.json'
                                        try:
                                            detail = json.loads(progress.read_text())['message']
                                        except (OSError,ValueError,KeyError):
                                            detail = 'Waiting for startup and live ROS data'
                                        print(f'  {detail}. {total-number} trial cell(s) remain.',flush=True)
                                        if time.monotonic()>=deadline:
                                            raise
                            finally:
                                if probe.poll() is None:
                                    stop_group(probe)
                            (attempt/'probe.log').write_text(output)
                            if not (attempt/'result.json').exists():
                                request.update(status='environment_error',error='Probe exited without evidence. Read probe.log.')
                                request.pop('grid')
                                (attempt/'result.json').write_text(json.dumps(request,indent=2))
                        except subprocess.TimeoutExpired:
                            request.update(status='environment_error',error='Probe process exceeded its wall-clock deadline')
                            request.pop('grid')
                            (attempt/'result.json').write_text(json.dumps(request,indent=2))
                        except KeyboardInterrupt:
                            request.update(status='interrupted',error='Batch interrupted by the operator')
                            request.pop('grid',None)
                            (attempt/'result.json').write_text(json.dumps(request,indent=2))
                            raise
                        finally:
                            stop_group(launch)
                    print(attempt.name,json.loads((attempt/'result.json').read_text())['status'],flush=True)
                    # Allow DDS participants from the previous reset to leave the graph.
                    time.sleep(2)


def reusable_result(output,mission,map_name,planner,seed,condition,map_hash,source_hash,field,timeout,outcomes):
    """Reuse only this protocol, source, map, condition and execution deadline."""
    for path in Path(output).glob('*/result.json'):
        try:
            row = json.loads(path.read_text())
            if (row.get('experiment_version')==EXPERIMENT_VERSION and str(row.get('mission'))==str(mission)
                and row.get('map')==map_name and row.get('planner')==planner and row.get('seed')==seed
                and row.get('condition')==condition and row.get('map_hash')==map_hash
                and row.get('source_sha256')==source_hash and row.get('field_hash')==fingerprint(field)
                and row.get('timeout_s')==timeout and row.get('status') in outcomes):
                return True
        except (OSError,ValueError):
            continue
    return False


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Batch stopped. Recorded attempts have been preserved.')
