"""Canonical grid maps, coordinate conversions and checked search instrumentation.

Cells are (row, column). Row zero is the bottom of the map. Distances are metres.
Four-connected grid planners use unit edge costs and a fixed neighbour order.
"""
from dataclasses import dataclass
from collections import deque
import hashlib
import json
import math
import time

RESOLUTION = 0.25
ORIGIN = (-5.0, -4.0)
ROBOT_RADIUS = 0.18
START = (4, 4)
GOAL = (27, 35)
PLANNERS = ('bfs', 'dfs', 'iddfs', 'astar', 'rrt', 'prm', 'nav2')
EXPERIMENT_VERSION = 7
MAX_SPEED = 0.30
TRIAL_TIMEOUT = 180


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def make_map(name, people=()):
    if name not in ('open', 'constrained'):
        raise ValueError('Choose open or constrained')
    grid = [[0] * 40 for _ in range(32)]
    for r in range(32):
        for c in range(40):
            blocked = r in (0, 31) or c in (0, 39)
            if name == 'open':
                blocked |= (13 <= r < 18 and 15 <= c < 19) or (22 <= r < 25 and 28 <= c < 31)
            else:
                blocked |= (c == 14 and 1 <= r < 26) or (c == 26 and 7 <= r < 31)
            x, y = cell_to_world((r, c))
            blocked |= any(math.hypot(x-p['x'], y-p['y']) <= p.get('radius', .25)+.18 for p in people)
            grid[r][c] = int(blocked)
    return grid


def cell_to_world(cell):
    r, c = cell
    return (ORIGIN[0] + (c+.5)*RESOLUTION, ORIGIN[1] + (r+.5)*RESOLUTION)


def world_to_cell(point):
    return (math.floor((point[1]-ORIGIN[1])/RESOLUTION), math.floor((point[0]-ORIGIN[0])/RESOLUTION))


def inflate(grid, radius=ROBOT_RADIUS):
    # A square expansion is conservative for a circular robot.
    n = math.ceil(radius/RESOLUTION)
    return [[int(any(grid[rr][cc] for rr in range(max(0,r-n), min(len(grid),r+n+1))
                     for cc in range(max(0,c-n), min(len(grid[0]),c+n+1))))
             for c in range(len(grid[0]))] for r in range(len(grid))]


def free(grid, cell):
    r, c = cell
    return 0 <= r < len(grid) and 0 <= c < len(grid[0]) and not grid[r][c]


def edge_free(grid, a, b):
    length = math.dist(a, b)
    n = max(1, math.ceil(length/(RESOLUTION/5)))
    return all(free(grid, world_to_cell((a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n))) for i in range(n+1))


def path_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def densify(points,spacing=.10):
    result = []
    for a,b in zip(points,points[1:]):
        count = max(1,math.ceil(math.dist(a,b)/spacing))
        result.extend([(a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(count)])
    return result+[points[-1]] if points else []


def distance_to_path(point,points):
    """Distance to line segments, independent of planner waypoint density."""
    best = math.inf
    for a,b in zip(points,points[1:]):
        dx,dy = b[0]-a[0],b[1]-a[1]
        length2 = dx*dx+dy*dy
        t = max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/length2)) if length2 else 0
        best = min(best,math.dist(point,(a[0]+t*dx,a[1]+t*dy)))
    return best


def obstacle_clearance(point,grid):
    """Exact distance from point to occupied cell rectangles minus robot radius."""
    x,y = point
    best = math.inf
    for r,row in enumerate(grid):
        for c,occupied in enumerate(row):
            if occupied:
                cx,cy = cell_to_world((r,c))
                dx,dy = max(0,abs(x-cx)-RESOLUTION/2),max(0,abs(y-cy)-RESOLUTION/2)
                best = min(best,math.hypot(dx,dy))
    return best-ROBOT_RADIUS


def reference_path(grid, start=START, goal=GOAL):
    """Supplied BFS oracle for checking path length, not the student implementation."""
    if not free(grid,start) or not free(grid,goal):
        return []
    queue, parent = deque([start]), {start: None}
    while queue:
        cur = queue.popleft()
        if cur == goal:
            return reconstruct(parent, cur)
        for nxt in neighbours(grid, cur):
            if nxt not in parent:
                parent[nxt] = cur
                queue.append(nxt)
    return []


def neighbours(grid, cell):
    r, c = cell
    return [(rr, cc) for rr, cc in ((r,c+1),(r+1,c),(r,c-1),(r-1,c)) if free(grid,(rr,cc))]


def reconstruct(parent, goal):
    path = []
    while goal is not None:
        path.append(goal)
        goal = parent[goal]
    return path[::-1]


@dataclass
class SearchContext:
    grid: list
    start: tuple = START
    goal: tuple = GOAL
    budget: int = 250000
    expanded: int = 0
    peak_frontier: int = 0

    def expand(self, cell, frontier_size):
        """Call once per expanded node, including repeated IDDFS expansions."""
        self.expanded += 1
        self.peak_frontier = max(self.peak_frontier, frontier_size)
        if self.expanded > self.budget:
            raise TimeoutError('Expansion budget reached')
        return neighbours(self.grid, cell)

    def heuristic(self, cell):
        return abs(cell[0]-self.goal[0]) + abs(cell[1]-self.goal[1])


def evaluate_student(function, grid, start=START, goal=GOAL):
    ctx = SearchContext(grid, start, goal)
    t = time.perf_counter()
    status, error, path = 'succeeded', '', []
    elapsed = None
    try:
        path = [tuple(p) for p in function(ctx)]
        elapsed = time.perf_counter()-t
        if not path:
            status = 'no_path' if not reference_path(grid,start,goal) else 'missed_path'
        elif path[0] != start or path[-1] != goal or any(not free(grid,p) for p in path) or any(abs(a[0]-b[0])+abs(a[1]-b[1]) != 1 for a,b in zip(path,path[1:])):
            status = 'invalid_path'
        elif ctx.expanded == 0 and start != goal:
            status, error = 'invalid_metrics', 'Use ctx.expand to instrument each expansion'
    except TimeoutError as exc:
        status, error = 'resource_limit', str(exc)
    except Exception as exc:
        status, error = 'implementation_error', f'{type(exc).__name__}: {exc}'
    if elapsed is None:
        elapsed = time.perf_counter()-t
    optimum = reference_path(grid,start,goal)
    return dict(status=status, error=error, planning_s=elapsed, expanded=ctx.expanded,
                peak_frontier=ctx.peak_frontier, path=path, path_length_m=max(0,len(path)-1)*RESOLUTION,
                optimal_length_m=max(0,len(optimum)-1)*RESOLUTION,
                optimality_ratio=(len(path)-1)/(len(optimum)-1) if path and len(optimum)>1 else (1.0 if path==optimum and len(path)==1 else None))
