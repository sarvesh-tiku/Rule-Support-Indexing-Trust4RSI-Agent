"""Uncertainty and threshold sensitivity for the staged-commit safeguard.  Post hoc.

Part 1 re-reads the independent validation run (results/safeguard_validation.json, threshold 0.999
fixed in advance) and attaches 95% intervals from a bootstrap over maps (one map gives up to four
episodes). For a count of zero the bootstrap is useless, so an exact one-sided 95% upper bound is
given, computed on maps (the conservative unit) and on episodes.

Part 2 is a sensitivity sweep of the second threshold on a THIRD set of maps (new seeds), so the
validation set above stays untouched by any threshold comparison.

Usage:  python3 scripts/safeguard_audit.py --seeds 30000 30600 --out results/safeguard_audit.json
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

import game_levels as g
from abandonment import StagedAgent
from cpr.agents import Agent
from cpr.experiment import source_hash
from safeguard_validation import bottleneck_map, play

THRESHOLDS = (0.99, 0.999, 0.9999, 0.99999)
rng = np.random.default_rng(0)


def clustered(rows, f, B=5000):
    """Mean of f over episodes with a 95% interval from resampling maps."""
    by = defaultdict(lambda: [0.0, 0])
    for r in rows:
        by[(r["W"], r["seed"])][0] += f(r)
        by[(r["W"], r["seed"])][1] += 1
    a = np.array(list(by.values()), float)
    idx = rng.integers(0, len(a), size=(B, len(a)))
    boot = a[idx, 0].sum(axis=1) / a[idx, 1].sum(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return [round(float(a[:, 0].sum() / a[:, 1].sum()), 4), round(float(lo), 4), round(float(hi), 4)]


def zero_upper(n):
    """Exact one-sided 95% upper bound on a rate when 0 of n independent units showed the event."""
    return round(1 - 0.05 ** (1 / n), 5)


def describe(rows, policies, base="commit_095"):
    reach = [r for r in rows if r["reachable"]]
    unre = [r for r in rows if not r["reachable"]]
    out = dict(reachable_episodes=len(reach), reachable_maps=len({(r["W"], r["seed"]) for r in reach}),
               unreachable_episodes=len(unre), unreachable_maps=len({(r["W"], r["seed"]) for r in unre}), policies={})
    for p in policies:
        d = dict(false_abandon_count=sum(r[p]["gave_up"] for r in reach),
                 false_abandon_rate=clustered(reach, lambda r: float(r[p]["gave_up"])),
                 reachable_mean_actions=clustered(reach, lambda r: r[p]["actions"]),
                 unreachable_not_abandoned=sum(not r[p]["gave_up"] for r in unre),
                 unreachable_mean_actions=clustered(unre, lambda r: r[p]["actions"]))
        if d["false_abandon_count"] == 0:
            d["false_abandon_upper95"] = dict(by_maps=zero_upper(out["reachable_maps"]), by_episodes=zero_upper(len(reach)))
        if p != base:
            d["reachable_extra_actions_vs_base"] = clustered(reach, lambda r: r[p]["actions"] - r[base]["actions"])
            d["unreachable_extra_actions_vs_base"] = clustered(unre, lambda r: r[p]["actions"] - r[base]["actions"])
        out["policies"][p] = d
    return out


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
    row["commit_095"] = play(Agent("repair", world.clone()))
    for th in THRESHOLDS:
        row[f"staged_{th}"] = play(StagedAgent("repair", world.clone(), strict=th))
    return row


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", default="results/safeguard_validation.json")
    ap.add_argument("--sizes", type=int, nargs="+", default=[11, 15, 21])
    ap.add_argument("--seeds", type=int, nargs=2, default=[30000, 30600])
    ap.add_argument("--out", default="results/safeguard_audit.json")
    a = ap.parse_args()
    val = json.load(open(a.validation))
    out = dict(source_sha256=source_hash(),
               validation=dict(seeds=val["seeds"], **describe(val["rows"], ("commit_095", "staged_0999"))))
    tasks = [(W, s, c) for W in a.sizes for s in range(*a.seeds) for c in g.CONDITIONS]
    with Pool() as pool:
        rows = [r for r in pool.imap_unordered(task, tasks, chunksize=8) if r]
    out["sweep"] = dict(seeds=a.seeds, sizes=a.sizes,
                        **describe(rows, ("commit_095",) + tuple(f"staged_{t}" for t in THRESHOLDS)))
    print(json.dumps(out, indent=1))
    json.dump(dict(out, sweep_rows=rows), open(a.out, "w"))
