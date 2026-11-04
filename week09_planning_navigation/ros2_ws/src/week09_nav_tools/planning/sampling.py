"""Provided seeded sampling planners. Both use the same inflated collision map."""
import heapq
import math
import random
import time
from .core import cell_to_world, edge_free, free, world_to_cell, path_length


def sampling_plan(kind, grid, start, goal, seed=0, samples=450):
    rng = random.Random(seed)
    a, b = cell_to_world(start), cell_to_world(goal)
    nodes, parent = [a], {0: None}
    began = time.perf_counter()
    build_s = 0.0
    query_started = began
    path, checks = [], 0
    if kind == 'rrt':
        for _ in range(samples*5):
            target = b if rng.random() < .15 else (rng.uniform(-4.5,4.5),rng.uniform(-3.5,3.5))
            idx = min(range(len(nodes)), key=lambda i: math.dist(nodes[i],target))
            distance = math.dist(nodes[idx],target)
            if distance < 1e-9:
                continue
            step = min(.45/distance,1)
            nxt = tuple(nodes[idx][j]+step*(target[j]-nodes[idx][j]) for j in (0,1))
            checks += 1
            if edge_free(grid,nodes[idx],nxt):
                parent[len(nodes)] = idx
                nodes.append(nxt)
                if math.dist(nxt,b) < .6 and edge_free(grid,nxt,b):
                    path, cur = [b], len(nodes)-1
                    while cur is not None:
                        path.append(nodes[cur])
                        cur = parent[cur]
                    path.reverse()
                    break
    elif kind == 'prm':
        nodes.append(b)
        for _ in range(samples*5):
            p = (rng.uniform(-4.5,4.5),rng.uniform(-3.5,3.5))
            if free(grid,world_to_cell(p)):
                nodes.append(p)
            if len(nodes) >= samples+2:
                break
        graph = [dict() for _ in nodes]
        for i,p in enumerate(nodes):
            nearest = sorted(range(len(nodes)),key=lambda j: math.dist(p,nodes[j]))[1:13]
            for j in nearest:
                checks += 1
                if edge_free(grid,p,nodes[j]):
                    graph[i][j] = graph[j][i] = math.dist(p,nodes[j])
        costs, previous, queue = {0:0}, {0:None}, [(0,0)]
        build_s = time.perf_counter()-began
        query_started = time.perf_counter()
        while queue:
            cost,i = heapq.heappop(queue)
            if cost != costs[i]:
                continue
            if i == 1:
                while i is not None:
                    path.append(nodes[i])
                    i = previous[i]
                path.reverse()
                break
            for j,w in graph[i].items():
                if cost+w < costs.get(j,math.inf):
                    costs[j],previous[j] = cost+w,i
                    heapq.heappush(queue,(cost+w,j))
    else:
        raise ValueError(kind)
    return dict(path=path, status='succeeded' if path else 'no_path', planning_s=time.perf_counter()-began,
                build_s=build_s,query_s=time.perf_counter()-query_started,
                path_length_m=path_length(path), sampled_nodes=len(nodes), collision_checks=checks, seed=seed)
