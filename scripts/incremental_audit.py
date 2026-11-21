"""Audit of the incremental-search comparison: an optimised LPA*, intervals, memory, and a profile.

Extends scripts/incremental_baseline.py (which is left as it was) with

  * LPAFast: the same algorithm with flat lists, precomputed neighbours and heuristic, and the
    vertex update inlined. It must expand exactly the same vertices as the dictionary version.
  * per-episode rows, so every ratio gets a 95% interval from a bootstrap over maps
    (a map contributes up to three episodes: block, slow, unlock);
  * the size of the state each method keeps between commits (pickled bytes of its leg table);
  * --profile: a cProfile breakdown of the dictionary LPA*.

Six methods receive identical inputs and are checked to agree on every leg cost after every commit:
  astar_all, astar_index, lpa_all, lpa_index, lpaf_all, lpaf_index.   Post hoc.

Usage:  python3 scripts/incremental_audit.py --sizes 15 31 51 --seeds 1000 1300 --out results/incremental_audit.json
        python3 scripts/incremental_audit.py --profile 31 --seeds 1000 1030
"""
import argparse
import cProfile
import heapq
import io
import json
import os
import pickle
import pstats
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from cpr.experiment import make_episode, source_hash
from cpr.planner import INF, Leg, Stats, astar, cost_array
from incremental_baseline import LPA, Recorder, changed_cells

pc = time.perf_counter
METHODS = ("astar_all", "astar_index", "lpa_all", "lpa_index", "lpaf_all", "lpaf_index")
_NB = {}


def nbrs_table(W):
    if W not in _NB:
        t = []
        for v in range(W * W):
            x, y, l = v % W, v // W, []
            if x + 1 < W:
                l.append(v + 1)
            if x > 0:
                l.append(v - 1)
            if y + 1 < W:
                l.append(v + W)
            if y > 0:
                l.append(v - W)
            t.append(tuple(l))
        _NB[W] = t
    return _NB[W]


class LPAFast:
    """LPA* with the same keys, tie-breaking and update order as incremental_baseline.LPA."""

    def __init__(self, W, arr, a, b):
        n = W * W
        self.W, self.a, self.b, self.arr = W, a, b, arr
        self.nb = nbrs_table(W)
        bx, by = b % W, b // W
        # two terms, added in the same order as the dictionary version, so floating-point ties break alike
        self.hx = [abs(v % W - bx) for v in range(n)]
        self.hy = [abs(v // W - by) for v in range(n)]
        self.g, self.rhs, self.inq = [INF] * n, [INF] * n, [None] * n
        self.rhs[a] = 0.0
        self.heap, self.expansions = [], 0
        self.inq[a] = (0.0 + self.hx[a] + self.hy[a], 0.0)
        self.heap.append((self.inq[a], a))

    def _touch(self, vs):
        g, rhs, inq, heap, arr, nb, a = self.g, self.rhs, self.inq, self.heap, self.arr, self.nb, self.a
        hx, hy = self.hx, self.hy
        push = heapq.heappush
        for s in vs:
            if s != a:
                c = arr[s]
                if c == INF:
                    r = INF
                else:
                    r = INF
                    for w in nb[s]:
                        if g[w] < r:
                            r = g[w]
                    r += c
                rhs[s] = r
            gs, rs = g[s], rhs[s]
            if gs != rs:
                m = gs if gs < rs else rs
                k = (m + hx[s] + hy[s], m)
                inq[s] = k
                push(heap, (k, s))
            else:
                inq[s] = None

    def set_costs(self, arr, changed):
        self.arr = arr
        self._touch(changed)

    def solve(self):
        g, rhs, inq, heap, nb, b = self.g, self.rhs, self.inq, self.heap, self.nb, self.b
        pop, touch, exp = heapq.heappop, self._touch, 0
        while heap:
            k, u = heap[0]
            if inq[u] != k:
                pop(heap)
                continue
            gb, rb = g[b], rhs[b]
            m = gb if gb < rb else rb
            if not (k < (m, m) or rb != gb):
                break
            pop(heap)
            inq[u] = None
            exp += 1
            if g[u] > rhs[u]:
                g[u] = rhs[u]
                touch(nb[u])
            else:
                g[u] = INF
                touch((u,) + nb[u])
        self.expansions += exp
        return g[b] if rhs[b] == g[b] else rhs[b]

    def cost(self):
        return self.g[self.b]

    def path(self):
        g = self.g
        if g[self.b] == INF:
            return []
        out, v = [], self.b
        while v != self.a:
            out.append(v)
            v = min(self.nb[v], key=g.__getitem__)
        out.reverse()
        return out

    def __getstate__(self):          # what must be kept between commits (neighbour table is shared)
        return (self.W, self.a, self.b, self.hx, self.hy, self.g, self.rhs, self.inq, self.heap)


def replay(world, log):
    W = world.W
    res = {m: dict(exp=0, time=0.0, legs=0) for m in METHODS}
    init = {m: dict(exp=0, time=0.0) for m in METHODS}
    first = log[0]
    if any(e["events"] is None for e in log[1:]):
        return None                           # a full rebuild inside the episode: nothing incremental to compare
    arr = cost_array(world, first["c"], first["patched"])
    keys0 = first["keys"]
    cost_all, legs_idx = {}, {}
    for name in ("astar_all", "astar_index"):
        t = pc(); st = Stats()
        for key in keys0:
            c, path = astar(W, arr, key[0], key[1], st)
            if name == "astar_all":
                cost_all[key] = c
            else:
                legs_idx[key] = Leg(world, key[0], key[1], c, path or [], set(first["patched"]))
        init[name]["time"] = pc() - t; init[name]["exp"] = st.expansions
    inc = {}
    for name, cls in (("lpa_all", LPA), ("lpa_index", LPA), ("lpaf_all", LPAFast), ("lpaf_index", LPAFast)):
        t = pc(); S, legs, sync = {}, {}, {}
        for key in keys0:
            L = cls(W, arr, key[0], key[1]); c = L.solve()
            S[key] = L
            if name.endswith("index"):
                legs[key] = Leg(world, key[0], key[1], c, L.path(), set(first["patched"]))
                sync[key] = (list(first["c"]), set(first["patched"]))
        init[name]["time"] = pc() - t; init[name]["exp"] = sum(L.expansions for L in S.values())
        inc[name] = (S, legs, sync)
    prev, checks = first, 0
    for entry in log[1:]:
        keys, events = entry["keys"], entry["events"]
        arr = cost_array(world, entry["c"], entry["patched"])
        delta = changed_cells(world, prev["c"], entry["c"], prev["patched"], entry["patched"])
        t = pc(); st = Stats()
        for key in keys:
            cost_all[key] = astar(W, arr, key[0], key[1], st)[0]
        r = res["astar_all"]; r["time"] += pc() - t; r["exp"] += st.expansions; r["legs"] += len(keys)
        t = pc(); st = Stats(); n = 0
        for key in keys:
            if legs_idx[key].affected(events):
                c, path = astar(W, arr, key[0], key[1], st)
                legs_idx[key] = Leg(world, key[0], key[1], c, path or [], set(entry["patched"])); n += 1
        r = res["astar_index"]; r["time"] += pc() - t; r["exp"] += st.expansions; r["legs"] += n
        for name in ("lpa_all", "lpaf_all"):
            S = inc[name][0]
            t = pc(); e0 = sum(S[key].expansions for key in keys)
            for key in keys:
                S[key].set_costs(arr, delta); S[key].solve()
            r = res[name]; r["time"] += pc() - t; r["exp"] += sum(S[key].expansions for key in keys) - e0
            r["legs"] += len(keys)
        for name in ("lpa_index", "lpaf_index"):
            S, legs, sync = inc[name]
            t = pc(); e0 = sum(S[key].expansions for key in keys); n = 0
            for key in keys:
                if legs[key].affected(events):
                    c_old, p_old = sync[key]
                    S[key].set_costs(arr, changed_cells(world, c_old, entry["c"], p_old, entry["patched"]))
                    c = S[key].solve()
                    legs[key] = Leg(world, key[0], key[1], c, S[key].path(), set(entry["patched"]))
                    sync[key] = (list(entry["c"]), set(entry["patched"])); n += 1
            r = res[name]; r["time"] += pc() - t; r["exp"] += sum(S[key].expansions for key in keys) - e0
            r["legs"] += n
        for key in keys:
            ref = cost_all[key]
            got = (legs_idx[key].cost, inc["lpa_all"][0][key].g.get(key[1], INF), inc["lpa_index"][1][key].cost,
                   inc["lpaf_all"][0][key].cost(), inc["lpaf_index"][1][key].cost)
            for x in got:
                assert x == ref or abs(x - ref) <= 1e-6, (key, ref, got)
            checks += 1
        prev = entry
    for a, b in (("lpa_all", "lpaf_all"), ("lpa_index", "lpaf_index")):
        assert res[a]["exp"] == res[b]["exp"] and init[a]["exp"] == init[b]["exp"], (a, res[a], res[b])
    size = dict(astar_all=len(pickle.dumps(cost_all)), astar_index=len(pickle.dumps(legs_idx)),
                lpa_all=len(pickle.dumps(_state(inc["lpa_all"][0]))),
                lpa_index=len(pickle.dumps((_state(inc["lpa_index"][0]), inc["lpa_index"][1]))),
                lpaf_all=len(pickle.dumps(inc["lpaf_all"][0])),
                lpaf_index=len(pickle.dumps((inc["lpaf_index"][0], inc["lpaf_index"][1]))))
    return dict(res=res, init=init, commits=len(log) - 1, checks=checks, bytes=size)


def _state(S):
    return {k: (L.g, L.rhs, L.inq, L.heap) for k, L in S.items()}


def record(W, seed, cond):
    ep = make_episode(W, seed, cond)
    if ep is None:
        return None
    world = ep[0]
    ag = Recorder(world.clone())
    ag.start()
    while not ag.done and ag.actions < 30 * W * W:
        ag.step()
    return world, ag.log


def task(t):
    W, seed, cond = t
    rec = record(W, seed, cond)
    if rec is None:
        return None
    out = replay(*rec)
    if out is None:
        return dict(W=W, seed=seed, condition=cond, skipped=True)
    return dict(W=W, seed=seed, condition=cond, **out)


def ratio_ci(rows, num, den, rng, B=5000):
    """Ratio of totals with a 95% interval from resampling maps (seeds)."""
    by = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        by[r["seed"]][0] += num(r)
        by[r["seed"]][1] += den(r)
    a = np.array(list(by.values()))
    idx = rng.integers(0, len(a), size=(B, len(a)))
    boot = a[idx, 0].sum(axis=1) / a[idx, 1].sum(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return [round(float(a[:, 0].sum() / a[:, 1].sum()), 3), round(float(lo), 3), round(float(hi), 3)]


def profile(W, seeds):
    recs = [r for s in range(*seeds) for c in ("block", "slow", "unlock") if (r := record(W, s, c))]
    out = {}
    for name, cls in (("lpa_dict", LPA), ("lpa_fast", LPAFast)):
        pr = cProfile.Profile()
        pr.enable()
        for world, log in recs:
            if any(e["events"] is None for e in log[1:]):
                continue
            arr = cost_array(world, log[0]["c"], log[0]["patched"])
            S = {k: cls(world.W, arr, k[0], k[1]) for k in log[0]["keys"]}
            for L in S.values():
                L.solve()
            prev = log[0]
            for e in log[1:]:
                arr = cost_array(world, e["c"], e["patched"])
                d = changed_cells(world, prev["c"], e["c"], prev["patched"], e["patched"])
                for k in e["keys"]:
                    S[k].set_costs(arr, d); S[k].solve()
                prev = e
        pr.disable()
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(8)
        out[name] = s.getvalue()
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[15, 31, 51])
    ap.add_argument("--seeds", type=int, nargs=2, default=[1000, 1300])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--profile", type=int)
    ap.add_argument("--out", default="results/incremental_audit.json")
    a = ap.parse_args()
    if a.profile:
        for name, text in profile(a.profile, a.seeds).items():
            print("=====", name)
            print(text)
        sys.exit()
    tasks = [(W, s, c) for W in a.sizes for s in range(*a.seeds) for c in ("block", "slow", "unlock")]
    with Pool(a.procs) as pool:
        rows = [r for r in pool.imap_unordered(task, tasks, chunksize=4) if r]
    rng = np.random.default_rng(0)
    out = dict(source_sha256=source_hash(), seeds=a.seeds, procs=a.procs, bootstrap="maps, 5000 resamples", by_size={})
    for W in a.sizes:
        sel = [r for r in rows if r["W"] == W and not r.get("skipped")]
        n = len(sel)
        s = dict(episodes=n, maps=len({r["seed"] for r in sel}),
                 skipped_full_rebuild=sum(1 for r in rows if r["W"] == W and r.get("skipped")),
                 commits=sum(r["commits"] for r in sel), leg_cost_checks=sum(r["checks"] for r in sel))
        for m in METHODS:
            s[m] = dict(expansions=round(sum(r["res"][m]["exp"] for r in sel) / n, 1),
                        ms=round(1000 * sum(r["res"][m]["time"] for r in sel) / n, 3),
                        legs_searched=round(sum(r["res"][m]["legs"] for r in sel) / n, 2),
                        initial_ms=round(1000 * sum(r["init"][m]["time"] for r in sel) / n, 3),
                        state_kib=round(sum(r["bytes"][m] for r in sel) / n / 1024, 1))
            if m != "astar_all":
                s[m]["expansions_vs_astar_all"] = ratio_ci(sel, lambda r: r["res"][m]["exp"], lambda r: r["res"]["astar_all"]["exp"], rng)
                s[m]["time_vs_astar_all"] = ratio_ci(sel, lambda r: r["res"][m]["time"], lambda r: r["res"]["astar_all"]["time"], rng)
        for tag, x, y in (("index_on_top_of_lpa", "lpa_index", "lpa_all"), ("index_on_top_of_lpaf", "lpaf_index", "lpaf_all"),
                          ("lpaf_index_vs_astar_index", "lpaf_index", "astar_index"), ("lpaf_vs_lpa", "lpaf_all", "lpa_all")):
            s[tag] = dict(expansions=ratio_ci(sel, lambda r: r["res"][x]["exp"], lambda r: r["res"][y]["exp"], rng),
                          time=ratio_ci(sel, lambda r: r["res"][x]["time"], lambda r: r["res"][y]["time"], rng))
        s["initial_time_lpaf_vs_astar"] = ratio_ci(sel, lambda r: r["init"]["lpaf_all"]["time"], lambda r: r["init"]["astar_all"]["time"], rng)
        out["by_size"][W] = s
    print(json.dumps(out, indent=1))
    json.dump(dict(out, rows=rows), open(a.out, "w"))
