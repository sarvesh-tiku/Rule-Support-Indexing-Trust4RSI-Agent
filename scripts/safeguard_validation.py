"""Independent test of the staged-commit safeguard on maps it was not designed on.

The safeguard in scripts/abandonment.py was written after inspecting 19 failures on four game
layouts. Here it is run unchanged (strict threshold 0.999, no tuning) on freshly generated maps
with new seeds. Unlike the main generator, these maps REQUIRE obstacle crossings: the waypoints
are reachable when obstacles are ignored but not through open cells alone.

Policies:
  commit_095     the original agent: a rule is committed as blocked at posterior 0.95
  staged_0999    the safeguard as designed
  never_abandon  staged commits with no give-up threshold (stops only at the action cap)

Each map and condition is one episode. Episodes are split by whether the goal is reachable under
the true rules.

Usage:  python3 scripts/safeguard_validation.py --sizes 11 15 21 --seeds 20000 20600 --out results/safeguard_validation.json
"""
import argparse
import json
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import game_levels as g
from abandonment import StagedAgent
from cpr.agents import Agent
from cpr.experiment import source_hash
from cpr.planner import INF, Stats, astar
from cpr.world import K, OPEN, WALL, World, _open_connected, _segment

N_WAYPOINTS = 3


def bottleneck_map(W, seed):
    """Random segments as in cpr.world.gen_map, but kept only if obstacles must be crossed."""
    rng = random.Random(seed * 104729 + W)
    for _ in range(4000):
        grid = [OPEN] * (W * W)
        for _ in range(max(2, W // 2)):
            for x, y in _segment(rng, W, rng.randint(max(2, W // 3), max(3, W // 2))):
                grid[y * W + x] = WALL
        for k in range(K):
            for _ in range(max(2, W // 5)):
                for x, y in _segment(rng, W, rng.randint(max(3, W // 3), max(4, W // 2))):
                    grid[y * W + x] = k
        opens = [c for c in range(W * W) if grid[c] == OPEN]
        if len(opens) < N_WAYPOINTS + 2:
            continue
        pts = rng.sample(opens, N_WAYPOINTS + 2)
        if _open_connected(W, grid, pts):
            continue
        arr = [INF if t == WALL else 1.0 for t in grid]
        if not all(astar(W, arr, pts[0], p, Stats())[0] < INF for p in pts[1:]):
            continue
        return World(W, grid, pts[0], pts[1:-1], pts[-1], seed)
    return None


def play(agent):
    agent.start()
    cap = 30 * agent.W * agent.W
    while not agent.done and agent.actions < cap:
        agent.step()
    return dict(finished=bool(agent.done and not agent.failed), gave_up=bool(agent.failed),
                hit_cap=not agent.done, actions=agent.actions, commits=agent.triggers,
                staged=getattr(agent, "staged", 0), post=agent.stats.expansions - agent.exp_initial)


def task(t):
    W, seed, cond = t
    world = bottleneck_map(W, seed)
    if world is None:
        return None
    try:
        if not g.inject(world, cond):
            return None
    except Exception:
        return None
    row = dict(W=W, seed=seed, condition=cond, reachable=g.solvable(world))
    for name, make in (("commit_095", lambda w: Agent("repair", w)),
                       ("staged_0999", lambda w: StagedAgent("repair", w)),
                       ("never_abandon", lambda w: StagedAgent("repair", w, strict=2.0))):
        row[name] = play(make(world.clone()))
    return row


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def summarise(rows):
    out = dict(episodes=len(rows), maps=len({(r["W"], r["seed"]) for r in rows}))
    for name in ("commit_095", "staged_0999", "never_abandon"):
        a = [r[name] for r in rows]
        out[name] = dict(finished=sum(x["finished"] for x in a), gave_up=sum(x["gave_up"] for x in a),
                         hit_action_cap=sum(x["hit_cap"] for x in a),
                         mean_actions=round(sum(x["actions"] for x in a) / len(a), 2) if a else None,
                         median_actions=pct([x["actions"] for x in a], 0.5), p95_actions=pct([x["actions"] for x in a], 0.95),
                         max_actions=max((x["actions"] for x in a), default=None),
                         mean_commits=round(sum(x["commits"] for x in a) / len(a), 2) if a else None,
                         episodes_with_staged_commit=sum(x["staged"] > 0 for x in a))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[11, 15, 21])
    ap.add_argument("--seeds", type=int, nargs=2, default=[20000, 20600])
    ap.add_argument("--out", default="results/safeguard_validation.json")
    a = ap.parse_args()
    tasks = [(W, s, c) for W in a.sizes for s in range(*a.seeds) for c in g.CONDITIONS]
    with Pool() as pool:
        rows = [r for r in pool.imap_unordered(task, tasks, chunksize=8) if r]
    out = dict(source_sha256=source_hash(), seeds=a.seeds, sizes=a.sizes, strict=0.999,
               reachable=summarise([r for r in rows if r["reachable"]]),
               unreachable=summarise([r for r in rows if not r["reachable"]]),
               reachable_by_condition={c: summarise([r for r in rows if r["reachable"] and r["condition"] == c])
                                       for c in g.CONDITIONS})
    json.dump(dict(out, rows=rows), open(a.out, "w"))
    print(json.dumps(out, indent=1))
