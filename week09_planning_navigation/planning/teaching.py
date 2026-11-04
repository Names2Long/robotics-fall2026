"""Small, bounded reference experiments for the ungraded planning playground.

These demonstrations do not replace student search implementations or change
the canonical Mission 1 or ROS trial maps. Cells use (row, column).
"""
from collections import deque
import heapq
import math
from planning.core import free, neighbours, reconstruct


def teaching_map():
    grid = [[int(r in (0,8) or c in (0,10)) for c in range(11)] for r in range(9)]
    for r in range(1,6):
        grid[r][5] = 1
    return grid


def search_trace(grid,start,goal,method='bfs',costs=None,budget=2500):
    """Record genuine queue/stack/heap operations and a bounded IDDFS search.

    Expansion counts increase when successors are examined. Goal removal does
    not expand its successors. IDDFS counts repeated expansions at new bounds.
    Weighted edge cost is the cost of entering the destination cell.
    """
    start,goal = tuple(start),tuple(goal)
    if method not in ('bfs','dfs','iddfs','dijkstra','astar'):
        raise ValueError('Unknown reference method')
    costs = costs or [[1]*len(grid[0]) for _ in grid]
    if any(not math.isfinite(v) or v<=0 for row in costs for v in row):
        raise ValueError('Traversal costs must be positive finite numbers')
    frames,expanded,peak = [],0,0
    def record(current,frontier,visited,path,status='running',depth=None):
        nonlocal peak
        peak = max(peak,len(frontier)+int(current is not None))
        frames.append(dict(current=current,frontier=list(dict.fromkeys(frontier)),explored=sorted(visited),
                           path=list(path),expanded=expanded,peak_frontier=peak,status=status,depth_limit=depth))
    if not free(grid,start) or not free(grid,goal):
        record(None,[],set(),[],'invalid_endpoint')
    elif method=='iddfs':
        done = False
        for depth in range(sum(not cell for row in grid for cell in row)):
            stack,seen,cutoff = [(start,[start],depth)],set(),False
            while stack:
                current,path,left = stack.pop()
                if current==goal:
                    record(current,[p[0] for p in stack],seen,path,'succeeded',depth)
                    done = True
                    break
                successors = [p for p in neighbours(grid,current) if p not in path]
                expanded += 1
                seen.add(current)
                if left:
                    stack.extend((p,path+[p],left-1) for p in reversed(successors))
                elif successors:
                    cutoff = True
                record(current,[p[0] for p in stack],seen,path,depth=depth)
                if expanded>=budget:
                    frames[-1]['status'] = 'resource_limit'
                    done = True
                    break
            if done:
                break
            if not cutoff:
                record(None,[],seen,[],'no_path',depth)
                break
    else:
        parent,best,visited = {start:None},{start:0},set()
        minimum = min(v for r,row in enumerate(costs) for c,v in enumerate(row) if not grid[r][c])
        heuristic = lambda p: (abs(p[0]-goal[0])+abs(p[1]-goal[1]))*minimum if method=='astar' else 0
        queue = deque([start])
        heap = [(heuristic(start),0,0,start)]
        counter = 0
        while heap if method in ('dijkstra','astar') else queue:
            if method in ('dijkstra','astar'):
                _,g,_,current = heapq.heappop(heap)
                if g!=best[current] or current in visited:
                    continue
            else:
                current = queue.pop() if method=='dfs' else queue.popleft()
            pending = lambda: [p[3] for p in heap if p[3] not in visited and p[1]==best[p[3]]] if method in ('dijkstra','astar') else list(queue)
            if current==goal:
                record(current,pending(),visited,reconstruct(parent,current),'succeeded')
                break
            visited.add(current)
            expanded += 1
            adjacent = neighbours(grid,current)
            if method=='dfs':
                adjacent.reverse()
            for nxt in adjacent:
                candidate = best[current]+costs[nxt[0]][nxt[1]]
                if method in ('dijkstra','astar'):
                    if candidate<best.get(nxt,math.inf):
                        best[nxt],parent[nxt] = candidate,current
                        counter += 1
                        heapq.heappush(heap,(candidate+heuristic(nxt),candidate,counter,nxt))
                elif nxt not in parent:
                    parent[nxt],best[nxt] = current,candidate
                    queue.append(nxt)
            record(current,pending(),visited,reconstruct(parent,current))
            if expanded>=budget:
                frames[-1]['status'] = 'resource_limit'
                break
        else:
            record(None,[],visited,[],'no_path')
    final = frames[-1]
    path = final['path'] if final['status']=='succeeded' else []
    return dict(method=method,frames=frames,status=final['status'],path=path,expanded=expanded,
                peak_frontier=peak,steps=len(path)-1 if path else None,
                total_cost=sum(costs[r][c] for r,c in path[1:]) if path else None)


def weighted_case(expensive=5):
    grid = [[int(r in (0,6) or c in (0,10)) for c in range(11)] for r in range(7)]
    costs = [[1]*11 for _ in range(7)]
    for c in range(2,9):
        costs[3][c] = expensive
    return grid,costs,(3,1),(3,9)


def footprint_case():
    # Two rooms joined by a three-cell-high passage. Larger inflation closes it.
    grid = [[int(r in (0,10) or c in (0,14)) for c in range(15)] for r in range(11)]
    for r in range(1,10):
        if r not in (4,5,6):
            grid[r][7] = 1
    return grid,(5,3),(5,11)


def small_cases():
    empty = [[0]*7 for _ in range(5)]
    detour = [row[:] for row in empty]
    for r in range(4):
        detour[r][3] = 1
    disconnected = [row[:] for row in empty]
    for r in range(5):
        disconnected[r][3] = 1
    occupied = [[0]*5 for _ in range(3)]
    occupied[2][4] = 1
    return {
        'Start equals goal':dict(grid=[[0]*3 for _ in range(3)],start=(1,1),goal=(1,1),note='Return the single starting cell with zero movement cost.'),
        'Empty grid':dict(grid=empty,start=(0,0),goal=(4,6),note='Boundary checks matter even without obstacles.'),
        'Required detour':dict(grid=detour,start=(1,1),goal=(1,5),note='A wall blocks the direct route, but a route around its end exists.'),
        'Occupied goal':dict(grid=occupied,start=(0,0),goal=(2,4),note='The goal itself is occupied. Return no path.'),
        'Disconnected goal':dict(grid=disconnected,start=(1,1),goal=(1,5),note='Both endpoints are free, but a full wall disconnects them. Return no path after exhausting the search.'),
        'Narrow passage':dict(grid=[[1]*9,[1,0,0,0,0,0,0,0,1],[1]*9],start=(1,1),goal=(1,7),note='A one-cell corridor tests legal neighbors and reconstruction. These small coding checks use point states, not the robot-size experiment.'),
    }
