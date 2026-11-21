"""Does the rule-support index add anything on top of incremental search?

Replays the model revisions of real held-out episodes and maintains the table of cached legs
with four methods that receive identical inputs:

  astar_all     A* from scratch on every leg at every commit            (full replanning)
  astar_index   A* only on the legs the index invalidates               (this paper)
  lpa_all       Lifelong Planning A* on every leg at every commit       (incremental search, no index)
  lpa_index     LPA* only on the legs the index invalidates             (both combined)

Only the leg table is compared: legs from the agent's current position are searched afresh by
every method and the ordering step is the same, so they are left out. After every commit all four
tables are checked to hold the same costs. LPA* follows Koenig, Likhachev and Furcy (2004) with a
Manhattan heuristic; a cell-entry cost change makes that one vertex inconsistent. Post hoc.

Usage:  python3 scripts/incremental_baseline.py --sizes 15 31 51 --seeds 1000 1300 --out results/incremental.json
"""
import argparse
import heapq
import json
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from cpr.agents import Agent
from cpr.experiment import make_episode, source_hash
from cpr.planner import INF, Leg, Stats, astar, cost_array

pc = time.perf_counter


class LPA:
    """LPA* between fixed cells a and b on a W x W grid with a cost for entering each cell."""

    def __init__(self, W, arr, a, b):
        self.W, self.a, self.b = W, a, b
        self.arr = list(arr)
        self.g, self.rhs, self.inq, self.heap = {}, {a: 0.0}, {}, []
        self.expansions = 0
        self.bx, self.by = b % W, b // W
        self._push(a)

    def _key(self, v):
        m = min(self.g.get(v, INF), self.rhs.get(v, INF))
        return (m + abs(v % self.W - self.bx) + abs(v // self.W - self.by), m)

    def _push(self, v):
        k = self._key(v)
        self.inq[v] = k
        heapq.heappush(self.heap, (k, v))

    def _nbrs(self, v):
        W, x, y = self.W, v % self.W, v // self.W
        if x + 1 < W:
            yield v + 1
        if x > 0:
            yield v - 1
        if y + 1 < W:
            yield v + W
        if y > 0:
            yield v - W

    def _update(self, v):
        if v != self.a:
            c = self.arr[v]
            if c == INF:
                r = INF
            else:
                g = self.g
                r = min((g.get(u, INF) for u in self._nbrs(v)), default=INF) + c
            self.rhs[v] = r
        if self.g.get(v, INF) != self.rhs.get(v, INF):
            self._push(v)
        else:
            self.inq.pop(v, None)

    def set_costs(self, arr, changed):
        self.arr = list(arr)
        for v in changed:
            self._update(v)

    def solve(self):
        g, rhs, heap, inq, b = self.g, self.rhs, self.heap, self.inq, self.b
        while heap:
            k, u = heap[0]
            if inq.get(u) != k:
                heapq.heappop(heap)
                continue
            if not (k < self._key(b) or rhs.get(b, INF) != g.get(b, INF)):
                break
            heapq.heappop(heap)
            del inq[u]
            self.expansions += 1
            if g.get(u, INF) > rhs.get(u, INF):
                g[u] = rhs[u]
                for s in self._nbrs(u):
                    self._update(s)
            else:
                g[u] = INF
                self._update(u)
                for s in self._nbrs(u):
                    self._update(s)
        return g.get(b, INF) if rhs.get(b, INF) == g.get(b, INF) else rhs.get(b, INF)

    def path(self):
        if self.g.get(self.b, INF) == INF:
            return []
        out, v = [], self.b
        while v != self.a:
            out.append(v)
            v = min(self._nbrs(v), key=lambda u: self.g.get(u, INF))
        out.reverse()
        return out


class Recorder(Agent):
    """Indexed-repair agent that records every commit it makes."""

    def __init__(self, world):
        super().__init__("repair", world)
        self.log = []

    def full_replan(self):
        super().full_replan()
        self.log.append(dict(events=None, c=list(self.c), patched=set(self.patched), keys=self._keys()))

    def scoped_repair(self, events, force):
        super().scoped_repair(events, force)
        self.log.append(dict(events=list(events), c=list(self.c), patched=set(self.patched), keys=self._keys()))


def changed_cells(world, c_old, c_new, p_old, p_new):
    cells = set(p_old ^ p_new)
    for k, (x, y) in enumerate(zip(c_old, c_new)):
        if x != y:
            cells.update(world.type_cells[k])
    return cells


def replay(world, log):
    W = world.W
    res = {m: dict(exp=0, time=0.0, legs=0) for m in ("astar_all", "astar_index", "lpa_all", "lpa_index")}
    init = {m: dict(exp=0, time=0.0) for m in res}
    first = log[0]
    arr = cost_array(world, first["c"], first["patched"])
    A, C, D, E, Eleg, Esync = {}, {}, {}, {}, {}, {}
    for key in first["keys"]:
        for name, store in (("astar_all", A), ("astar_index", C)):
            st = Stats(); t = pc()
            c, path = astar(W, arr, key[0], key[1], st)
            store[key] = Leg(world, key[0], key[1], c, path or [], set(first["patched"])) if name == "astar_index" else c
            init[name]["time"] += pc() - t; init[name]["exp"] += st.expansions
        for name, store in (("lpa_all", D), ("lpa_index", E)):
            t = pc()
            L = LPA(W, arr, key[0], key[1]); c = L.solve()
            if name == "lpa_index":
                Eleg[key] = Leg(world, key[0], key[1], c, L.path(), set(first["patched"]))
                Esync[key] = (list(first["c"]), set(first["patched"]))
            store[key] = L
            init[name]["time"] += pc() - t; init[name]["exp"] += L.expansions
    prev, checks = first, 0
    for entry in log[1:]:
        if entry["events"] is None:          # a full rebuild inside the episode (exception retraction): restart all
            return None
        keys, events = entry["keys"], entry["events"]
        arr = cost_array(world, entry["c"], entry["patched"])
        delta = changed_cells(world, prev["c"], entry["c"], prev["patched"], entry["patched"])
        # A* on everything
        t = pc(); st = Stats()
        for key in keys:
            A[key] = astar(W, arr, key[0], key[1], st)[0]
        res["astar_all"]["time"] += pc() - t; res["astar_all"]["exp"] += st.expansions; res["astar_all"]["legs"] += len(keys)
        # index + A*
        t = pc(); st = Stats(); n = 0
        for key in keys:
            if C[key].affected(events):
                c, path = astar(W, arr, key[0], key[1], st)
                C[key] = Leg(world, key[0], key[1], c, path or [], set(entry["patched"])); n += 1
        res["astar_index"]["time"] += pc() - t; res["astar_index"]["exp"] += st.expansions; res["astar_index"]["legs"] += n
        # LPA* on everything
        t = pc(); e0 = sum(D[key].expansions for key in keys)
        for key in keys:
            D[key].set_costs(arr, delta); D[key].solve()
        res["lpa_all"]["time"] += pc() - t; res["lpa_all"]["exp"] += sum(D[key].expansions for key in keys) - e0
        res["lpa_all"]["legs"] += len(keys)
        # index + LPA*
        t = pc(); e0 = sum(E[key].expansions for key in keys); n = 0
        for key in keys:
            if Eleg[key].affected(events):
                c_old, p_old = Esync[key]
                E[key].set_costs(arr, changed_cells(world, c_old, entry["c"], p_old, entry["patched"]))
                c = E[key].solve()
                Eleg[key] = Leg(world, key[0], key[1], c, E[key].path(), set(entry["patched"]))
                Esync[key] = (list(entry["c"]), set(entry["patched"])); n += 1
        res["lpa_index"]["time"] += pc() - t; res["lpa_index"]["exp"] += sum(E[key].expansions for key in keys) - e0
        res["lpa_index"]["legs"] += n
        for key in keys:
            ref = A[key]
            for got in (C[key].cost, D[key].g.get(key[1], INF), Eleg[key].cost):
                assert got == ref or abs(got - ref) <= 1e-6, (key, ref, got)
            checks += 1
        prev = entry
    return dict(res=res, init=init, commits=len(log) - 1, checks=checks)


def task(t):
    W, seed, cond = t
    ep = make_episode(W, seed, cond)
    if ep is None:
        return None
    world = ep[0]
    ag = Recorder(world.clone())
    ag.start()
    while not ag.done and ag.actions < 30 * W * W:
        ag.step()
    out = replay(world, ag.log)
    if out is None:
        return dict(W=W, skipped=True)
    return dict(W=W, seed=seed, condition=cond, **out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[15, 31, 51])
    ap.add_argument("--seeds", type=int, nargs=2, default=[1000, 1300])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--out", default="results/incremental.json")
    a = ap.parse_args()
    tasks = [(W, s, c) for W in a.sizes for s in range(*a.seeds) for c in ("block", "slow", "unlock")]
    with Pool(a.procs) as pool:
        rows = [r for r in pool.imap_unordered(task, tasks, chunksize=4) if r]
    out = dict(source_sha256=source_hash(), seeds=a.seeds, procs=a.procs, by_size={})
    for W in a.sizes:
        sel = [r for r in rows if r["W"] == W and not r.get("skipped")]
        n = len(sel)
        s = dict(episodes=n, skipped_full_rebuild=sum(1 for r in rows if r["W"] == W and r.get("skipped")),
                 commits=sum(r["commits"] for r in sel), leg_cost_checks=sum(r["checks"] for r in sel))
        for m in ("astar_all", "astar_index", "lpa_all", "lpa_index"):
            s[m] = dict(expansions=round(sum(r["res"][m]["exp"] for r in sel) / n, 1),
                        ms=round(1000 * sum(r["res"][m]["time"] for r in sel) / n, 3),
                        legs_searched=round(sum(r["res"][m]["legs"] for r in sel) / n, 2),
                        initial_expansions=round(sum(r["init"][m]["exp"] for r in sel) / n, 1),
                        initial_ms=round(1000 * sum(r["init"][m]["time"] for r in sel) / n, 3))
        base = s["astar_all"]
        for m in ("astar_index", "lpa_all", "lpa_index"):
            s[m]["expansions_vs_astar_all"] = round(s[m]["expansions"] / base["expansions"], 3)
            s[m]["time_vs_astar_all"] = round(s[m]["ms"] / base["ms"], 3)
        s["index_on_top_of_lpa"] = dict(expansions=round(s["lpa_index"]["expansions"] / s["lpa_all"]["expansions"], 3),
                                        time=round(s["lpa_index"]["ms"] / s["lpa_all"]["ms"], 3))
        out["by_size"][W] = s
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))
