"""Executable search for counterexamples to Proposition 1, and a check of epsilon.

Part 1 (epsilon). Lists every way the code can produce a committed rule cost and confirms each is
>= 1 + eps with eps = 1/0.9 - 1: the belief cost formula over a grid of the belief simplex, sampled
rule sets (posterior sampling), the nominal costs of the non-revising agent, and every cost actually
committed in real episodes.

Part 2 (search). Exhaustive on small boards: every placement of two obstacle types on a 3x3 board
(open / type 0 / type 1 per cell), every pair of endpoints, every ordered pair of cost vectors drawn
from a set of values. For each revision it compares index-based invalidation with a fresh search.
  --floor ok        cost values all >= 1 + eps   (expected: zero counterexamples)
  --floor violated  adds the value 1.0           (expected: counterexamples exist)

Usage:  python3 scripts/counterexample_search.py --out results/counterexample_search.json
"""
import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from cpr.agents import Agent, Belief, DEFAULTS
from cpr.experiment import make_episode, source_hash
from cpr.planner import INF, MIN_OBSTACLE_EXTRA as EPS, Leg, Stats, astar, cost_array
from cpr.world import K, NOMINAL, OPEN, VALUES, World


def epsilon_audit():
    floor = 1 + EPS
    out = dict(eps=EPS, floor=floor)
    lows = []
    for W in (2, 3, 15, 31, 51):
        b = Belief(DEFAULTS, W)
        lo = INF
        n = 200
        for i in range(n + 1):
            for j in range(n + 1 - i):
                d = (i / n, j / n, (n - i - j) / n)
                lo = min(lo, b.cost_of(d))
        lows.append((W, lo))
    out["belief_cost_min_by_board"] = lows
    out["sampled_rule_cost_min"] = min(1 / v for v in VALUES if v > 0)
    out["nominal_cost_min"] = min(1 / v for v in NOMINAL if v > 0)
    committed, n_commits = INF, 0
    for W in (15, 31):
        for seed in range(1000, 1060):
            for cond in ("none", "block", "slow", "unlock", "ool"):
                ep = make_episode(W, seed, cond)
                if ep is None:
                    continue
                ag = Agent("repair", ep[0].clone())
                ag.start()
                committed = min(committed, min(ag.c))
                while not ag.done and ag.actions < 30 * W * W:
                    before = list(ag.c)
                    ag.step()
                    if ag.c != before:
                        n_commits += sum(x != y for x, y in zip(ag.c, before))
                        committed = min(committed, min(ag.c))
    out["committed_cost_min_in_real_episodes"] = committed
    out["commits_observed"] = n_commits
    out["all_at_or_above_floor"] = bool(all(lo >= floor - 1e-12 for _, lo in lows)
                                        and out["sampled_rule_cost_min"] >= floor - 1e-12
                                        and out["nominal_cost_min"] >= floor - 1e-12
                                        and committed >= floor - 1e-12)
    return out


def search(values, W=3):
    cells = W * W
    checked = found = stale_valonly = 0
    first = None
    pairs = [(a, b) for a in range(cells) for b in range(a + 1, cells)]
    for layout in itertools.product((OPEN, 0, 1), repeat=cells):
        if 0 not in layout and 1 not in layout:
            continue
        world = World(W, list(layout), 0, [], cells - 1, seed=0)
        ends = [(a, b) for a, b in pairs if layout[a] == OPEN and layout[b] == OPEN]
        if not ends:
            continue
        for c0, c1 in itertools.product(values, repeat=2):
            base = [c0, c1, 9.0, 9.0, 9.0]
            arr = cost_array(world, base, ())
            legs = {}
            for a, b in ends:
                c, path = astar(W, arr, a, b, Stats())
                legs[(a, b)] = Leg(world, a, b, c, path or [], set())
            for k in (0, 1):
                for new in values:
                    if new == base[k]:
                        continue
                    kind = "up" if new > base[k] else "down"
                    costs = list(base)
                    costs[k] = new
                    arr2 = cost_array(world, costs, ())
                    for (a, b), leg in legs.items():
                        fresh = astar(W, arr2, a, b, Stats())[0]
                        changed = not (fresh == leg.cost or abs(fresh - leg.cost) <= 1e-9)
                        checked += 1
                        if changed and not leg.affected([(kind, k)]):
                            found += 1
                            if first is None:
                                first = dict(layout=list(layout), a=a, b=b, costs=base, rule=k, new=new,
                                             cached=leg.cost, fresh=fresh)
                        if changed and k not in leg.val:
                            stale_valonly += 1
    return dict(values=[v if v < INF else "inf" for v in values], leg_revisions_checked=checked,
                index_misses=found, direct_support_only_misses=stale_valonly, first_counterexample=first)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/counterexample_search.json")
    a = ap.parse_args()
    ok_values = [1 + EPS, 1.5, 1 / 0.3, 12.0, INF]
    out = dict(source_sha256=source_hash(), epsilon=epsilon_audit(),
               floor_respected=search(ok_values), floor_violated=search([1.0] + ok_values))
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))
