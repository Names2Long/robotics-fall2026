from collections import deque
from heapq import heappush, heappop
from planning.core import free, reconstruct


def bfs(ctx):
    """Search in increasing number of edges using a FIFO queue."""
    if not free(ctx.grid, ctx.start) or not free(ctx.grid, ctx.goal):
        return []

    frontier = deque([ctx.start])
    parent = {ctx.start: None}

    while frontier:
        current = frontier.popleft()

        if current == ctx.goal:
            return reconstruct(parent, current)

        for nxt in ctx.expand(current, len(frontier) + 1):
            # Mark discovery when adding to the queue.
            if nxt not in parent:
                parent[nxt] = current
                frontier.append(nxt)

    return []


def dfs(ctx):
    """Search using a LIFO stack, with discovery-based cycle prevention."""
    if not free(ctx.grid, ctx.start) or not free(ctx.grid, ctx.goal):
        return []

    frontier = [ctx.start]
    parent = {ctx.start: None}

    while frontier:
        current = frontier.pop()

        if current == ctx.goal:
            return reconstruct(parent, current)

        # Push in the supplied order. The stack visits the last pushed first.
        for nxt in ctx.expand(current, len(frontier) + 1):
            if nxt not in parent:
                parent[nxt] = current
                frontier.append(nxt)

    return []


def iddfs(ctx):
    """Repeat depth-limited DFS until success or exhaustive failure."""
    if not free(ctx.grid, ctx.start) or not free(ctx.grid, ctx.goal):
        return []

    limit = 0

    while True:
        path = [ctx.start]
        on_path = {ctx.start}

        def depth_limited(current, remaining):
            if current == ctx.goal:
                return path.copy(), False

            # Active recursion frames form this search's stack.
            neighbours = ctx.expand(current, len(path))
            candidates = [nxt for nxt in neighbours if nxt not in on_path]

            if remaining == 0:
                # Unexplored continuations mean cutoff, not proven failure.
                return None, bool(candidates)

            cutoff = False

            for nxt in candidates:
                path.append(nxt)
                on_path.add(nxt)

                result, child_cutoff = depth_limited(nxt, remaining - 1)

                on_path.remove(nxt)
                path.pop()

                if result is not None:
                    return result, False

                cutoff = cutoff or child_cutoff

            return None, cutoff

        result, cutoff = depth_limited(ctx.start, limit)

        if result is not None:
            return result

        if not cutoff:
            return []

        # Keep the same ctx so repeated work remains counted.
        limit += 1


def astar(ctx):
    """Expand the lowest g + Manhattan-distance priority."""
    if not free(ctx.grid, ctx.start) or not free(ctx.grid, ctx.goal):
        return []

    frontier = []
    best_g = {ctx.start: 0}
    parent = {ctx.start: None}

    heappush(frontier, (ctx.heuristic(ctx.start), 0, ctx.start))

    while frontier:
        _, cost, current = heappop(frontier)

        # Ignore entries superseded by a cheaper route.
        if cost != best_g.get(current):
            continue

        if current == ctx.goal:
            return reconstruct(parent, current)

        for nxt in ctx.expand(current, len(frontier) + 1):
            new_cost = cost + 1

            if new_cost < best_g.get(nxt, float("inf")):
                best_g[nxt] = new_cost
                parent[nxt] = current
                priority = new_cost + ctx.heuristic(nxt)
                heappush(frontier, (priority, new_cost, nxt))

    return []