"""Leg search, the leg table with rule supports, and ordering."""
import heapq
from itertools import permutations

from .world import WALL

INF = float("inf")
MIN_OBSTACLE_EXTRA = 1.0 / 0.9 - 1.0   # an obstacle cell costs at least this much more than 1


class Stats:
    def __init__(self):
        self.expansions = 0
        self.searches = 0


def astar(W, cost, a, b, stats):
    """Cheapest path from cell a to cell b; cost[v] is the cost of entering v.
    Returns (cost, path excluding a and including b) or (INF, None)."""
    bx, by = b % W, b // W
    h0 = abs(a % W - bx) + abs(a // W - by)
    g, parent, closed = {a: 0.0}, {}, set()
    heap, exp = [(h0, h0, a)], 0
    while heap:
        _, _, u = heapq.heappop(heap)
        if u in closed:
            continue
        closed.add(u)
        exp += 1
        if u == b:
            break
        ux, uy, gu = u % W, u // W, g[u]
        for vx, vy in ((ux + 1, uy), (ux - 1, uy), (ux, uy + 1), (ux, uy - 1)):
            if 0 <= vx < W and 0 <= vy < W:
                v = vy * W + vx
                c = cost[v]
                if c == INF or v in closed:
                    continue
                ng = gu + c
                if ng < g.get(v, INF) - 1e-12:
                    g[v], parent[v] = ng, u
                    hv = abs(vx - bx) + abs(vy - by)
                    heapq.heappush(heap, (ng + hv, hv, v))
    stats.expansions += exp
    stats.searches += 1
    if b not in closed:
        return INF, None
    path, u = [], b
    while u != a:
        path.append(u)
        u = parent[u]
    path.reverse()
    return g[b], path


class Leg:
    """A cached subplan together with the rule hypotheses it depends on.

    val: types the path enters (validity support: the leg's cost changes if any changes).
    blk: types that could shorten the leg if they became cheaper (optimality support).
    """
    __slots__ = ("a", "b", "cost", "path", "cells", "val", "blk")

    def __init__(self, world, a, b, cost, path, patched):
        self.a, self.b, self.cost, self.path = a, b, cost, path
        self.cells = set(path)
        grid, W = world.grid, world.W
        self.val = frozenset(grid[v] for v in path if grid[v] >= 0)
        ax, ay, bx, by = a % W, a // W, b % W, b // W
        blk = set()
        for k, cells in enumerate(world.type_cells):
            if k in self.val:
                continue
            for x in cells:
                if x in patched:
                    continue
                xx, xy = x % W, x // W
                if abs(ax - xx) + abs(ay - xy) + abs(xx - bx) + abs(xy - by) + MIN_OBSTACLE_EXTRA < cost - 1e-9:
                    blk.add(k)
                    break
        self.blk = frozenset(blk)

    def affected(self, events):
        """events: iterable of ('up'|'down', type) or ('patch', cell)."""
        for kind, x in events:
            if kind == "patch":
                if x in self.cells:
                    return True
            elif x in self.val or (kind == "down" and x in self.blk):
                return True
        return False

    def oriented(self, frm):
        if frm == self.a:
            return list(self.path)
        return self.path[-2::-1] + [self.a]


def cost_array(world, type_cost, patched):
    grid = world.grid
    arr = [1.0 if t == -1 else (INF if t == WALL else type_cost[t]) for t in grid]
    for c in patched:
        arr[c] = INF
    return arr


def best_order(first_cost, fixed_cost, remaining, tower):
    """Cheapest visiting order of the remaining shrines, ending at the tower.
    first_cost[s]: cost from the current position to s (or to the tower if none remain)."""
    rem = sorted(remaining)
    if not rem:
        return [], first_cost[tower]
    best, best_cost = None, INF
    for perm in permutations(rem):
        c = first_cost[perm[0]]
        for i in range(len(perm) - 1):
            c += fixed_cost[(min(perm[i], perm[i + 1]), max(perm[i], perm[i + 1]))]
            if c >= best_cost:
                break
        else:
            c += fixed_cost[(min(perm[-1], tower), max(perm[-1], tower))]
            if c < best_cost - 1e-9:
                best, best_cost = perm, c
    return (list(best) if best is not None else []), best_cost
