"""When does the rule-support index pay off?  Cost of a repair against how much of the table changed.

Every commit of the real held-out episodes is replayed on the table of cached legs by five methods:

  astar_all     A* on every leg                               (full replanning)
  astar_index   A* on the legs the index invalidates          (this paper)
  astar_direct  A* on the legs whose own path uses a revised rule (direct support only; may go stale)
  lpa_all       optimised LPA* on every leg
  lpa_index     optimised LPA* on the legs the index invalidates

Commits are then grouped by the fraction of cached legs whose optimal cost REALLY changed at that
commit (ground truth from astar_all): 0, (0,25], (25,50], (50,75], (75,100] percent. The fraction is
not controlled by us; it is whatever the episodes produced, so bins differ in size.  Post hoc.

Usage:  python3 scripts/coverage_sweep.py --sizes 15 31 51 --seeds 1000 1300 --out results/coverage_sweep.json
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from cpr.experiment import source_hash
from cpr.planner import INF, Leg, Stats, astar, cost_array
from incremental_audit import LPAFast, record
from incremental_baseline import changed_cells

pc = time.perf_counter
METHODS = ("astar_all", "astar_index", "astar_direct", "lpa_all", "lpa_index")
BINS = ("0", "(0,25]", "(25,50]", "(50,75]", "(75,100]")


def bin_of(frac):
    if frac == 0:
        return 0
    return min(4, 1 + int((frac - 1e-12) * 4))


def same(x, y):
    return x == y or abs(x - y) <= 1e-6


def replay(world, log):
    W, first = world.W, log[0]
    if any(e["events"] is None for e in log[1:]):
        return None
    arr = cost_array(world, first["c"], first["patched"])
    truth, idx, direct, Lall, Lidx, Lleg, sync = {}, {}, {}, {}, {}, {}, {}
    for key in first["keys"]:
        c, path = astar(W, arr, key[0], key[1], Stats())
        truth[key] = c
        idx[key] = Leg(world, key[0], key[1], c, path or [], set(first["patched"]))
        direct[key] = Leg(world, key[0], key[1], c, path or [], set(first["patched"]))
        Lall[key] = LPAFast(W, arr, key[0], key[1]); Lall[key].solve()
        Lidx[key] = LPAFast(W, arr, key[0], key[1]); c2 = Lidx[key].solve()
        Lleg[key] = Leg(world, key[0], key[1], c2, Lidx[key].path(), set(first["patched"]))
        sync[key] = (list(first["c"]), set(first["patched"]))
    out, prev = [], first
    for entry in log[1:]:
        keys, events = entry["keys"], entry["events"]
        arr = cost_array(world, entry["c"], entry["patched"])
        delta = changed_cells(world, prev["c"], entry["c"], prev["patched"], entry["patched"])
        rec = {}
        old = dict(truth)
        t = pc(); st = Stats()
        for key in keys:
            truth[key] = astar(W, arr, key[0], key[1], st)[0]
        rec["astar_all"] = (st.expansions, pc() - t, len(keys))
        t = pc(); st = Stats(); n = 0
        for key in keys:
            if idx[key].affected(events):
                c, path = astar(W, arr, key[0], key[1], st)
                idx[key] = Leg(world, key[0], key[1], c, path or [], set(entry["patched"])); n += 1
        rec["astar_index"] = (st.expansions, pc() - t, n)
        t = pc(); st = Stats(); n = 0
        for key in keys:
            leg = direct[key]
            if any((kind == "patch" and x in leg.cells) or (kind != "patch" and x in leg.val) for kind, x in events):
                c, path = astar(W, arr, key[0], key[1], st)
                direct[key] = Leg(world, key[0], key[1], c, path or [], set(entry["patched"])); n += 1
        rec["astar_direct"] = (st.expansions, pc() - t, n)
        t = pc(); e0 = sum(Lall[key].expansions for key in keys)
        for key in keys:
            Lall[key].set_costs(arr, delta); Lall[key].solve()
        rec["lpa_all"] = (sum(Lall[key].expansions for key in keys) - e0, pc() - t, len(keys))
        t = pc(); e0 = sum(Lidx[key].expansions for key in keys); n = 0
        for key in keys:
            if Lleg[key].affected(events):
                c_old, p_old = sync[key]
                Lidx[key].set_costs(arr, changed_cells(world, c_old, entry["c"], p_old, entry["patched"]))
                c = Lidx[key].solve()
                Lleg[key] = Leg(world, key[0], key[1], c, Lidx[key].path(), set(entry["patched"]))
                sync[key] = (list(entry["c"]), set(entry["patched"])); n += 1
        rec["lpa_index"] = (sum(Lidx[key].expansions for key in keys) - e0, pc() - t, n)
        for key in keys:
            assert same(idx[key].cost, truth[key]) and same(Lall[key].cost(), truth[key]) and same(Lleg[key].cost, truth[key])
        changed = sum(not same(old[key], truth[key]) for key in keys)
        stale = sum(not same(direct[key].cost, truth[key]) for key in keys)
        if keys:                             # late commits can find no cached leg still needed
            out.append(dict(legs=len(keys), changed=changed, stale_direct=stale, m=rec))
        prev = entry
    return out


def task(t):
    W, seed, cond = t
    r = record(W, seed, cond)
    if r is None:
        return None
    commits = replay(*r)
    if commits is None:
        return None
    return dict(W=W, seed=seed, condition=cond, commits=commits)


def ratio_ci(items, num, den, rng, B=4000):
    by = defaultdict(lambda: [0.0, 0.0])
    for seed, c in items:
        by[seed][0] += num(c)
        by[seed][1] += den(c)
    a = np.array(list(by.values()))
    if a[:, 1].sum() == 0:
        return None
    idx = rng.integers(0, len(a), size=(B, len(a)))
    d = a[idx, 1].sum(axis=1)
    boot = a[idx, 0].sum(axis=1)[d > 0] / d[d > 0]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return [round(float(a[:, 0].sum() / a[:, 1].sum()), 3), round(float(lo), 3), round(float(hi), 3)]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[15, 31, 51])
    ap.add_argument("--seeds", type=int, nargs=2, default=[1000, 1300])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--out", default="results/coverage_sweep.json")
    a = ap.parse_args()
    tasks = [(W, s, c) for W in a.sizes for s in range(*a.seeds) for c in ("block", "slow", "unlock")]
    with Pool(a.procs) as pool:
        rows = [r for r in pool.imap_unordered(task, tasks, chunksize=4) if r]
    rng = np.random.default_rng(0)
    out = dict(source_sha256=source_hash(), seeds=a.seeds, bins=BINS, by_size={})
    for W in list(a.sizes) + ["all"]:
        items = [(( r["W"], r["seed"]), c) for r in rows if W == "all" or r["W"] == W for c in r["commits"]]
        res = {}
        for b, name in enumerate(BINS):
            sel = [(s, c) for s, c in items if bin_of(c["changed"] / c["legs"]) == b]
            if not sel:
                res[name] = dict(commits=0)
                continue
            d = dict(commits=len(sel), maps=len({s for s, _ in sel}),
                     mean_changed_fraction=round(float(np.mean([c["changed"] / c["legs"] for _, c in sel])), 3),
                     commits_with_stale_direct=sum(c["stale_direct"] > 0 for _, c in sel),
                     stale_direct_legs=sum(c["stale_direct"] for _, c in sel))
            for m in METHODS:
                d[m] = dict(legs_searched_fraction=round(sum(c["m"][m][2] for _, c in sel) / sum(c["legs"] for _, c in sel), 3))
                if m != "astar_all":
                    d[m]["expansions_vs_astar_all"] = ratio_ci(sel, lambda c: c["m"][m][0], lambda c: c["m"]["astar_all"][0], rng)
                    d[m]["time_vs_astar_all"] = ratio_ci(sel, lambda c: c["m"][m][1], lambda c: c["m"]["astar_all"][1], rng)
            d["lpa_index_vs_lpa_all_time"] = ratio_ci(sel, lambda c: c["m"]["lpa_index"][1], lambda c: c["m"]["lpa_all"][1], rng)
            res[name] = d
        out["by_size"][str(W)] = res
    print(json.dumps(out, indent=1))
    json.dump(dict(out, rows=rows), open(a.out, "w"))
