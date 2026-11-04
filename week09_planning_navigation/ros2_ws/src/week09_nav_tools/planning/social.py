"""Human-aware potential-field path refinement and timestamped social metrics.

This is a heuristic, not a safety guarantee. Known simulated people are not a
human detector. Local minima and failed refinements are retained as outcomes.
"""
import math
from .core import edge_free, path_length, ROBOT_RADIUS

PEOPLE = ({'x': 0.0, 'y': -1.7, 'radius': .25},)
CONFIGS = {
    'baseline': {'human_gain':0.0, 'influence_m':1.0, 'step_m':.08},
    'social_1': {'human_gain':.7, 'influence_m':1.0, 'step_m':.08},
    'social_2': {'human_gain':1.3, 'influence_m':1.5, 'step_m':.08},
}


def field_forces(current,waypoint,people,config):
    """The exact artificial vectors used by refine and its teaching diagram."""
    dx,dy = waypoint[0]-current[0],waypoint[1]-current[1]
    norm = max(math.hypot(dx,dy),1e-6)
    attraction = (dx/norm,dy/norm)
    rx,ry = 0.0,0.0
    for person in people:
        px,py = current[0]-person['x'],current[1]-person['y']
        center = max(math.hypot(px,py),1e-6)
        gap = max(.05,center-person['radius']-ROBOT_RADIUS)
        reach = config['influence_m']
        if gap < reach:
            force = min(4.0,config['human_gain']*(1/gap-1/reach)/(gap*gap))
            rx += force*px/center
            ry += force*py/center
    return dict(attraction=attraction,repulsion=(rx,ry),resultant=(attraction[0]+rx,attraction[1]+ry))


def refine(path, grid, people, config, diagnostic=None):
    """Return a complete collision-checked route, or an explicit failure.

    Optional diagnostic retains the valid prefix for the teaching preview only.
    A failed prefix must never be passed to the robot as a completed route.
    """
    def failed(status,prefix):
        if diagnostic is not None:
            diagnostic.update(path=list(prefix),status=status)
        return [],status
    if len(path) < 2 or config['human_gain'] == 0:
        return path, 'unchanged'
    current, result, target = path[0], [path[0]], 1
    for _ in range(4000):
        # A cell-wide acceptance radius skipped turn vertices and cut into
        # inflated walls even with tiny repulsion. Reach the actual corner
        # before switching targets so field failures reflect field geometry.
        if math.dist(current,path[target]) < config['step_m']:
            if not edge_free(grid,current,path[target]):
                return failed('obstacle_local_minimum',result)
            current = path[target]
            result.append(current)
            target += 1
            if target == len(path):
                if edge_free(grid,current,path[-1]):
                    return result, 'succeeded'
                return failed('blocked_goal',result)
        fx,fy = field_forces(current,path[target],people,config)['resultant']
        magnitude = max(math.hypot(fx,fy),1e-6)
        step = config['step_m']
        candidate = (current[0]+step*fx/magnitude,current[1]+step*fy/magnitude)
        if not edge_free(grid,current,candidate):
            return failed('obstacle_local_minimum',result)
        if len(result)>20 and math.dist(candidate,result[-20]) < step*2:
            return failed('oscillation',result)
        current = candidate
        result.append(current)
    return failed('iteration_limit',result)


def trajectory_metrics(samples, people=(), personal_space=.75):
    """Samples contain simulation t, x, y. Clearance is body-to-body distance."""
    if not samples:
        return dict(distance_m=0, elapsed_s=0, minimum_person_clearance_m=None, personal_space_s=0, max_speed_near_people_mps=0)
    exposure, speeds, gaps = 0, [], []
    for i,s in enumerate(samples):
        gap = min((math.hypot(s['x']-p['x'],s['y']-p['y'])-p['radius']-ROBOT_RADIUS for p in people),default=math.inf)
        gaps.append(gap)
        if i:
            previous = samples[i-1]
            dt = max(0,s['t']-previous['t'])
            if gap < personal_space:
                exposure += dt
                if dt:
                    speeds.append(s.get('speed_mps',math.hypot(s['x']-previous['x'],s['y']-previous['y'])/dt))
    return dict(distance_m=path_length([(s['x'],s['y']) for s in samples]),
                elapsed_s=max(0,samples[-1]['t']-samples[0]['t']),
                minimum_person_clearance_m=min(gaps) if people else None,
                personal_space_s=exposure,max_speed_near_people_mps=max(speeds,default=0))
