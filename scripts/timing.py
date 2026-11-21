"""Wall-clock time by phase for full replanning and indexed repair, single process.

Phases are timed by wrapping the functions the agents call:
  search    A* leg searches
  index     building a cached leg's support sets (val, blk)  -> index maintenance
  lookup    testing cached legs against a revision (Leg.affected)  -> index use
  ordering  solving the waypoint order
  other     everything else in the episode (simulation, belief updates, bookkeeping)
Both agents build the same Leg objects, so the replanning agent also pays `index` although it
never reads the supports; "replan_no_index" subtracts that to give a replanner without the index.
Each episode is run `--repeats` times and the fastest run is kept. Post hoc.

Usage:  python3 scripts/timing.py --sizes 15 31 51 --seeds 1000 1300 --repeats 3 --out results/timing.json
"""
import argparse
import json
import os
import platform
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import cpr.agents as A
from cpr.experiment import make_episode, source_hash

T = dict(search=0.0, index=0.0, lookup=0.0, ordering=0.0)
pc = time.perf_counter
_astar, _order, _Leg = A.astar, A.best_order, A.Leg


def astar(*a, **k):
    t = pc(); r = _astar(*a, **k); T["search"] += pc() - t; return r


def best_order(*a, **k):
    t = pc(); r = _order(*a, **k); T["ordering"] += pc() - t; return r


class Leg(_Leg):
    __slots__ = ()

    def __init__(self, *a, **k):
        t = pc(); super().__init__(*a, **k); T["index"] += pc() - t

    def affected(self, events):
        t = pc(); r = super().affected(events); T["lookup"] += pc() - t; return r


A.astar, A.best_order, A.Leg = astar, best_order, Leg


def run(kind, world):
    for k in T:
        T[k] = 0.0
    ag = A.Agent(kind, world)
    t0 = pc()
    ag.start()
    t_init = pc() - t0
    init = dict(T)
    cap = 30 * world.W * world.W
    while not ag.done and ag.actions < cap:
        ag.step()
    total = pc() - t0
    post = {k: T[k] - init[k] for k in T}
    post["other"] = (total - t_init) - sum(post.values())
    return dict(total=total, initial=t_init, post_total=total - t_init, **{"post_" + k: v for k, v in post.items()},
                expansions=ag.stats.expansions - ag.exp_initial, legs_recomputed=ag.legs_recomputed,
                legs_reused=ag.legs_reused, commits=ag.triggers, repairs=ag.repairs + ag.full_replans,
                actions=ag.actions)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[15, 31, 51])
    ap.add_argument("--seeds", type=int, nargs=2, default=[1000, 1300])
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--out", default="results/timing.json")
    a = ap.parse_args()
    out = dict(source_sha256=source_hash(), python=platform.python_version(), machine=platform.machine(),
               repeats=a.repeats, by_size={})
    for W in a.sizes:
        rows = []
        for seed in range(*a.seeds):
            for cond in ("block", "slow", "unlock"):
                ep = make_episode(W, seed, cond)
                if ep is None:
                    continue
                world = ep[0]
                row = {}
                for kind in ("replan", "repair"):
                    best = None
                    for _ in range(a.repeats):
                        r = run(kind, world.clone())
                        if best is None or r["post_total"] < best["post_total"]:
                            best = r
                    row[kind] = best
                rows.append(row)
        n = len(rows)
        m = lambda kind, key: sum(r[kind][key] for r in rows) / n
        ms = lambda kind, key: round(1000 * m(kind, key), 4)
        s = dict(episodes=n)
        for kind in ("replan", "repair"):
            s[kind] = dict(ms_initial_plan=ms(kind, "initial"), ms_after_initial=ms(kind, "post_total"),
                           ms_search=ms(kind, "post_search"), ms_index_build=ms(kind, "post_index"),
                           ms_index_lookup=ms(kind, "post_lookup"), ms_ordering=ms(kind, "post_ordering"),
                           ms_other=ms(kind, "post_other"), expansions=round(m(kind, "expansions"), 1),
                           legs_recomputed=round(m(kind, "legs_recomputed"), 2), legs_reused=round(m(kind, "legs_reused"), 2),
                           commits=round(m(kind, "commits"), 2), repairs=round(m(kind, "repairs"), 2),
                           ms_per_repair=round(1000 * sum(r[kind]["post_total"] - r[kind]["post_other"] for r in rows)
                                               / max(1, sum(r[kind]["repairs"] for r in rows)), 4))
        plan = lambda kind: m(kind, "post_total") - m(kind, "post_other")       # planning-related time only
        s["ratio_expansions"] = round(m("repair", "expansions") / m("replan", "expansions"), 3)
        s["ratio_time_after_initial"] = round(m("repair", "post_total") / m("replan", "post_total"), 3)
        s["ratio_planning_time"] = round(plan("repair") / plan("replan"), 3)
        s["ratio_planning_time_vs_replan_without_index"] = round(
            plan("repair") / (plan("replan") - m("replan", "post_index")), 3)
        s["index_share_of_repair_planning_time"] = round(
            (m("repair", "post_index") + m("repair", "post_lookup")) / plan("repair"), 3)
        s["identical_actions"] = sum(r["repair"]["actions"] == r["replan"]["actions"] for r in rows)
        out["by_size"][W] = s
        print(W, json.dumps(s, indent=1), flush=True)
    json.dump(out, open(a.out, "w"), indent=1)
