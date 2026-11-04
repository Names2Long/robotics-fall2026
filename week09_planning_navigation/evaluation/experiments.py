"""Completion checks require interpretable evidence, not perfect robot performance."""
from planning.core import PLANNERS, make_map, inflate, fingerprint, EXPERIMENT_VERSION

OUTCOMES = {'succeeded','no_path','resource_limit','planning_failed','controller_failed','controller_rejected',
            'timeout','wall_timeout','scan_proximity_stop','goal_error_exceeded','field_obstacle_local_minimum',
            'field_oscillation','field_iteration_limit','field_blocked_goal'}


def offline_checks(evidence):
    from planning.experiments import cases
    current_maps = {name:fingerprint(grid) for name,(grid,_,_) in cases().items()}
    rows = evidence.get('rows',[])
    checks = [('All four planners on all four cases', {(r.get('planner'),r.get('map')) for r in rows} >=
               {(p,m) for p in PLANNERS[:4] for m in ('diagnostic','open','constrained','unreachable')})]
    checks.append(('All searches solve the short diagnostic corridor',all(any(r.get('planner')==p and r.get('map')=='diagnostic' and r.get('status')=='succeeded' for r in rows) for p in PLANNERS[:4])))
    for planner in PLANNERS[:4]:
        relevant = [r for r in rows if r.get('planner')==planner]
        checks.append((f'{planner.upper()}: implemented and instrumented', bool(relevant) and all(
            r.get('status') not in ('implementation_error','invalid_path','invalid_metrics','missed_path') for r in relevant)
            and any(r.get('expanded',0)>0 for r in relevant)))
    checks.append(('BFS and A* find shortest paths on reachable maps',all(
        any(r.get('planner')==p and r.get('map')==m and r.get('status')=='succeeded' and r.get('optimality_ratio')==1 for r in rows)
        for p in ('bfs','astar') for m in ('open','constrained'))))
    checks.append(('Results use the current test maps',bool(rows) and all(
        r.get('map') in current_maps and r.get('map_hash')==current_maps[r['map']] for r in rows)))
    return checks


def navigation_checks(rows,source_hash):
    valid = [r for r in rows if r.get('status') in OUTCOMES
             and r.get('experiment_version')==EXPERIMENT_VERSION
             and r.get('map') in ('open','constrained')
             and r.get('map_hash')==fingerprint(inflate(make_map(r['map'])))
             and (r.get('planner') not in PLANNERS[:4] or r.get('source_sha256')==source_hash)]
    combos = {(r.get('planner'),r.get('map')) for r in valid}
    controllers = {r.get('controller_hash') for r in valid if r.get('trajectory')}
    return [('Seven planners on both canonical maps',combos >= {(p,m) for p in PLANNERS for m in ('open','constrained')}),
            ('Executed trials use one recorded controller configuration',len(controllers)==1 and None not in controllers),
            ('No environment failures in the selected evidence',bool(rows) and len(rows)==len(valid))]


def social_checks(rows):
    valid = [r for r in rows if r.get('status') in OUTCOMES and r.get('experiment_version')==EXPERIMENT_VERSION]
    groups = {}
    for r in valid:
        key = (r.get('planner'),r.get('map'),r.get('seed'),r.get('map_hash'),r.get('source_sha256'),r.get('controller_hash'))
        groups.setdefault(key,{})[r.get('condition')] = r
    paired = [g for g in groups.values() if set(g)>={'baseline','social_1','social_2'} and
              g['baseline'].get('trajectory') and len({g[c].get('field_hash') for c in ('baseline','social_1','social_2')})==3]
    conditions = {}
    for group in paired:
        signature = tuple(group[c].get('field_hash') for c in ('baseline','social_1','social_2'))
        conditions.setdefault(signature,set()).add(group['baseline']['planner'])
    planners = max(conditions.values(),key=len,default=set())
    return [('Matched baseline and two distinct field configurations for at least two planners',len(planners)>=2),
            ('Selected trials have readable experiment outcomes',bool(rows) and len(valid)==len(rows))]
