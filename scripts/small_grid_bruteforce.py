"""Brute-force check of Proposition 1 on small grids, with every leg between open cells.

Exhaustive enumeration stops being possible past 3x3 (a 5x5 grid with walls and five obstacle
types has 7^25 layouts), so 4x4 and 5x5 grids are sampled at random instead. For each layout the
table holds a leg for EVERY pair of open cells. A sequence of commits follows; one commit may
raise some rules, lower others, block or unlock a rule, and add a per-cell exception, all at once.
After each commit the index decides which legs to recompute, and every leg cost in the table is
compared with a single-source Bellman-Ford that shares no code with the planner.

Costs are drawn from the boundary values the proof depends on (exactly 1 + epsilon, infinity) as
well as from a continuous range.   Post hoc.

Usage:  python3 scripts/small_grid_bruteforce.py --layouts 20000 --out results/small_grid_bruteforce.json
"""
import argparse
import json
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from cpr.experiment import source_hash
from cpr.planner import INF, MIN_OBSTACLE_EXTRA, Leg, Stats, astar, cost_array
from cpr.world import K, OPEN, WALL, World

FLOOR = 1.0 + MIN_OBSTACLE_EXTRA
FIXED = (FLOOR, FLOOR, 1.2, 1.5, 2.0, 1 / 0.3, 12.0, INF, INF)


def draw_cost(rng):
    return rng.choice(FIXED) if rng.random() < 0.7 else FLOOR + rng.random() * 6


def all_costs(W, arr, a):
    """Bellman-Ford from a; independent of cpr.planner.astar."""
    dist, frontier = {a: 0.0}, [a]
    while frontier:
        nxt = []
        for u in frontier:
            x, y = u % W, u // W
            for vx, vy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= vx < W and 0 <= vy < W:
                    v = vy * W + vx
                    if arr[v] < INF and dist[u] + arr[v] < dist.get(v, INF) - 1e-12:
                        dist[v] = dist[u] + arr[v]
                        nxt.append(v)
        frontier = nxt
    return dist


def one(t):
    W, seed = t
    rng = random.Random(seed * 7919 + W)
    n = W * W
    grid = []
    for _ in range(n):
        r = rng.random()
        grid.append(WALL if r < 0.10 else (rng.randrange(K) if r < 0.55 else OPEN))
    opens = [c for c in range(n) if grid[c] == OPEN]
    tot = dict(layouts=0, commits=0, mixed=0, with_exception=0, to_or_from_inf=0, checks=0, redone=0, stale=0,
               stale_direct_only=0, unreachable=0, at_floor=0, first=None)
    if len(opens) < 2 or all(t < 0 for t in grid):
        return tot
    tot["layouts"] = 1
    world = World(W, grid, opens[0], [], opens[-1], seed)
    costs, patched = [draw_cost(rng) for _ in range(K)], set()
    arr = cost_array(world, costs, patched)
    table, shadow = {}, {}                 # shadow: the same table maintained with direct support only
    for i, a in enumerate(opens):
        for b in opens[i + 1:]:
            c, path = astar(W, arr, a, b, Stats())
            table[(a, b)] = Leg(world, a, b, c, path or [], set())
            shadow[(a, b)] = Leg(world, a, b, c, path or [], set())
    for _ in range(6):
        events, kinds = [], set()
        for k in rng.sample(range(K), rng.choice((1, 2, 2, 3, 5))):
            new = draw_cost(rng)
            if new != costs[k]:
                kind = "up" if new > costs[k] else "down"
                events.append((kind, k)); kinds.add(kind)
                tot["to_or_from_inf"] += (new == INF) or (costs[k] == INF)
                tot["at_floor"] += new == FLOOR
                costs[k] = new
        if rng.random() < 0.3:
            cand = [c for c in range(n) if grid[c] >= 0 and c not in patched]
            if cand:
                x = rng.choice(cand)
                patched.add(x); events.append(("patch", x)); tot["with_exception"] += 1
        if not events:
            continue
        tot["commits"] += 1
        tot["mixed"] += len(kinds) == 2
        arr = cost_array(world, costs, patched)
        for key, leg in list(table.items()):
            if leg.affected(events):
                c, path = astar(W, arr, key[0], key[1], Stats())
                table[key] = Leg(world, key[0], key[1], c, path or [], set(patched))
                tot["redone"] += 1
        for key, leg in list(shadow.items()):
            if any((kind == "patch" and x in leg.cells) or (kind != "patch" and x in leg.val) for kind, x in events):
                c, path = astar(W, arr, key[0], key[1], Stats())
                shadow[key] = Leg(world, key[0], key[1], c, path or [], set(patched))
        truth = {a: all_costs(W, arr, a) for a in opens[:-1]}
        for key, leg in table.items():
            ref = truth[key[0]].get(key[1], INF)
            tot["checks"] += 1
            tot["unreachable"] += ref == INF
            if not (ref == leg.cost or abs(ref - leg.cost) <= 1e-9):
                tot["stale"] += 1
                if tot["first"] is None:
                    tot["first"] = dict(W=W, seed=seed, leg=key, cached=leg.cost, truth=ref, events=events)
            s = shadow[key].cost
            if not (ref == s or abs(ref - s) <= 1e-9):
                tot["stale_direct_only"] += 1
    return tot


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[4, 5])
    ap.add_argument("--layouts", type=int, default=20000)
    ap.add_argument("--out", default="results/small_grid_bruteforce.json")
    a = ap.parse_args()
    out = dict(source_sha256=source_hash(), floor=FLOOR, by_size={})
    with Pool() as pool:
        for W in a.sizes:
            agg = None
            for r in pool.imap_unordered(one, [(W, s) for s in range(a.layouts)], chunksize=64):
                if agg is None:
                    agg = dict(r)
                    continue
                for k, v in r.items():
                    if k == "first":
                        agg[k] = agg[k] or v
                    else:
                        agg[k] += v
            out["by_size"][W] = agg
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))
