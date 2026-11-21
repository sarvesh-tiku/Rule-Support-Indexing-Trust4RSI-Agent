"""Direct-support-only repair: the simpler dependency tracker a reviewer would try first.

It invalidates a cached leg only when a rule the leg USES changes (val), ignoring the
optimality support (blk). Run on the same held-out maps and outcome draws as the main
experiment and compared, repair by repair, with a from-scratch plan under the same model.
Post hoc; not part of the pre-registered analysis.

Usage:  python3 scripts/valonly_baseline.py --sizes 15 31 51 --seeds 1000 1300 --out results/valonly.json
"""
import argparse
import json
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from cpr.agents import Agent
from cpr.experiment import CONDITIONS, make_episode, source_hash
from cpr.planner import Stats, astar, best_order


def uses(leg, events):
    return any((x in leg.cells) if kind == "patch" else (x in leg.val) for kind, x in events)


class ValOnly(Agent):
    def __init__(self, world):
        super().__init__("repair", world)
        self.stale_repairs = self.checked = 0
        self.excess = 0.0

    def scoped_repair(self, events, force):
        self.arr = self.build_arr()
        keys = self._keys()
        inv = [key for key in keys if uses(self.table[key], events)]
        cur_aff = self.mode != "plan" or self.cur_leg is None or uses(self.cur_leg, events)
        for key in inv:
            self.table[key] = self._search(key[0], key[1])
        self.legs_recomputed += len(inv)
        self.legs_reused += len(keys) - len(inv)
        self._anchor(not cur_aff)
        self.repairs += 1
        # evaluation only: what would a from-scratch plan cost under the same committed model?
        shadow = Stats()
        fresh = {key: astar(self.W, self.arr, key[0], key[1], shadow)[0] for key in keys}
        targets = sorted(self.remaining) or [self.tower]
        first = {s: astar(self.W, self.arr, self.pos, s, shadow)[0] for s in targets}
        _, best = best_order(first, fresh, self.remaining, self.tower)
        mine = self.current_plan_cost()
        self.checked += 1
        if mine > best + 1e-6:
            self.stale_repairs += 1
            self.excess += mine - best


def play(agent):
    agent.start()
    cap = 30 * agent.W * agent.W
    while not agent.done and agent.actions < cap:
        agent.step()
    return agent


def task(t):
    W, seed, cond = t
    ep = make_episode(W, seed, cond)
    if ep is None:
        return None
    world, _ = ep
    v = play(ValOnly(world.clone()))
    r = play(Agent("repair", world.clone()))
    return dict(W=W, seed=seed, condition=cond, v_actions=v.actions, r_actions=r.actions,
                v_done=bool(v.done and not v.failed), r_done=bool(r.done and not r.failed),
                v_post=v.stats.expansions - v.exp_initial, r_post=r.stats.expansions - r.exp_initial,
                repairs=v.checked, stale=v.stale_repairs, excess=v.excess)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[15, 31, 51])
    ap.add_argument("--seeds", type=int, nargs=2, default=[1000, 1300])
    ap.add_argument("--out", default="results/valonly.json")
    a = ap.parse_args()
    tasks = [(W, s, c) for W in a.sizes for s in range(*a.seeds) for c in CONDITIONS]
    with Pool() as pool:
        rows = [r for r in pool.imap_unordered(task, tasks, chunksize=8) if r]
    out = dict(source_sha256=source_hash(), seeds=a.seeds, by_size={})
    for W in a.sizes:
        for name, sel in (("all", [r for r in rows if r["W"] == W]),
                          ("unlock", [r for r in rows if r["W"] == W and r["condition"] == "unlock"])):
            n = len(sel)
            out["by_size"][f"{W}/{name}"] = dict(
                episodes=n, repairs=sum(r["repairs"] for r in sel), stale_repairs=sum(r["stale"] for r in sel),
                episodes_with_stale_plan=sum(r["stale"] > 0 for r in sel),
                episodes_actions_differ=sum(r["v_actions"] != r["r_actions"] for r in sel),
                mean_extra_actions=round(sum(r["v_actions"] - r["r_actions"] for r in sel) / n, 3),
                max_extra_actions=max(r["v_actions"] - r["r_actions"] for r in sel),
                unfinished=sum(not r["v_done"] for r in sel),
                work_ratio_vs_indexed=round(sum(r["v_post"] for r in sel) / sum(r["r_post"] for r in sel), 3))
    json.dump(dict(out, rows=rows), open(a.out, "w"))
    print(json.dumps(out, indent=1))
