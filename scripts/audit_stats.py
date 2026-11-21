"""Two checks on the reported run that the pre-registered analysis did not include.

1. Sampling unit. The pooled comparisons resample episodes, but one map contributes up to three
   episodes (block, slow, unlock). This recomputes the intervals resampling maps instead.
2. Wall-clock time per episode (recorded in the run; includes simulation and initial planning).

Usage:  python3 scripts/audit_stats.py results/final.jsonl results/audit_stats.json
"""
import json
import sys
from collections import defaultdict

import numpy as np

rows = [json.loads(l) for l in open(sys.argv[1])]
rows = [r for r in rows if "agent" in r]
ep = defaultdict(dict)
for r in rows:
    ep[(r["W"], r["seed"], r["condition"])][r["agent"]] = r
POOL = ("block", "slow", "unlock")
COMPARISONS = [("repair", "replan", "post"), ("repair_probe", "repair", "actions"), ("repair_probe", "psrl", "actions"),
               ("repair_probe", "ig_replan", "actions"), ("repair_probe", "replan_probe", "post")]


def metric(r, m):
    return r["expansions"] - r["exp_initial"] if m == "post" else r[m]


out = {"intervals": [], "wall": {}}
rng = np.random.default_rng(0)
for W in sorted({k[0] for k in ep}):
    by_map = defaultdict(list)
    for (w, seed, cond), ags in ep.items():
        if w == W and cond in POOL:
            by_map[seed].append(ags)
    seeds = sorted(by_map)
    for a, b, m in COMPARISONS:
        sums = np.array([sum(metric(e[a], m) - metric(e[b], m) for e in by_map[s]) for s in seeds], float)
        cnts = np.array([len(by_map[s]) for s in seeds], float)
        flat = np.array([metric(e[a], m) - metric(e[b], m) for s in seeds for e in by_map[s]], float)
        idx = rng.integers(0, len(seeds), size=(10000, len(seeds)))
        clus = sums[idx].sum(axis=1) / cnts[idx].sum(axis=1)
        idx2 = rng.integers(0, len(flat), size=(10000, len(flat)))
        epi = flat[idx2].mean(axis=1)
        out["intervals"].append(dict(W=W, a=a, b=b, metric=m, n_episodes=len(flat), n_maps=len(seeds),
                                     diff=round(flat.mean(), 2),
                                     episode_ci=[round(x, 2) for x in np.percentile(epi, [2.5, 97.5])],
                                     map_ci=[round(x, 2) for x in np.percentile(clus, [2.5, 97.5])]))
    sel = [e for (w, s, c), e in ep.items() if w == W and c in POOL]
    wall = {a: float(np.mean([e[a]["wall"] for e in sel])) for a in ("replan", "repair", "replan_probe", "repair_probe")}
    post = {a: float(np.mean([metric(e[a], "post") for e in sel])) for a in wall}
    out["wall"][W] = dict(mean_seconds={a: round(v, 4) for a, v in wall.items()},
                          wall_ratio_repair_over_replan=round(wall["repair"] / wall["replan"], 3),
                          expansions_ratio_repair_over_replan=round(post["repair"] / post["replan"], 3),
                          wall_ratio_probe_indexed_over_unindexed=round(wall["repair_probe"] / wall["replan_probe"], 3),
                          median_paired_wall_ratio=round(float(np.median([e["repair"]["wall"] / e["replan"]["wall"] for e in sel if e["replan"]["wall"] > 0])), 3))
json.dump(out, open(sys.argv[2], "w"), indent=1)
for r in out["intervals"]:
    print(r["W"], r["a"], "-", r["b"], r["metric"], r["diff"], "episode", r["episode_ci"], "map", r["map_ci"], f'n={r["n_episodes"]}/{r["n_maps"]} maps')
for W, v in out["wall"].items():
    print(W, v)
