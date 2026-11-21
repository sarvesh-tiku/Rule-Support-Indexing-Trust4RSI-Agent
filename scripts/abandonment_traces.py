"""Reproducible traces of every game-level episode in which a revising agent abandoned a reachable goal.

For each such episode: the level, start, condition and outcome seed (enough to replay it), every
obstacle attempt in order with its result and the posterior it produced, every commit, and the state
at the moment the agent stopped.

Usage:  python3 scripts/abandonment_traces.py --draws 50 --out results/abandonment_traces.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import game_levels as g
from cpr.agents import Agent
from cpr.experiment import source_hash
from cpr.planner import INF
from cpr.world import K

NAMES = g.KIND_ORDER


def trace(world, kind="repair"):
    ag = Agent(kind, world)
    ag.start()
    events = []
    while not ag.done and ag.actions < 30 * world.W * world.W:
        v, pos, c0, patched0, retr0 = ag.path[0], ag.pos, list(ag.c), set(ag.patched), ag.retractions
        k = world.grid[v]
        ag.step()
        if k >= 0:
            ev = dict(action=ag.actions, cell=[v % world.W, v // world.W], rule=NAMES[k], true_success=world.true_p(v),
                      entered=ag.pos == v or (ag.pos != pos),
                      posterior_free_slow_blocked=[round(x, 4) for x in ag.belief.b[k]])
            commits = [dict(rule=NAMES[j], old=c0[j] if c0[j] < INF else "inf", new=ag.c[j] if ag.c[j] < INF else "inf")
                       for j in range(K) if ag.c[j] != c0[j]]
            if commits:
                ev["commits"] = commits
            if ag.patched - patched0:
                ev["cell_exception_added"] = True
            if ag.retractions > retr0:
                ev["cell_exceptions_retracted"] = True
            events.append(ev)
    return ag, events


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=50)
    ap.add_argument("--out", default="results/abandonment_traces.json")
    a = ap.parse_args()
    out = []
    for name in g.LEVELS:
        for ch in ("C1", "C2", "C3"):
            for cond in g.CONDITIONS:
                for seed in range(a.draws):
                    world = g.build(name, ch, seed)
                    if not g.inject(world, cond) or not g.solvable(world):
                        break
                    ag, events = trace(world.clone())
                    if not ag.failed:
                        continue
                    inf = [k for k in range(K) if ag.c[k] == INF]
                    wrong = [k for k in inf if world.p_true[k] > 0]
                    streak = {}
                    for k in wrong:
                        n = 0
                        for ev in reversed([e for e in events if e["rule"] == NAMES[k]]):
                            if ev["entered"]:
                                break
                            n += 1
                        streak[NAMES[k]] = n
                    other, _ = trace(world.clone(), "replan")
                    out.append(dict(level=name, start=ch, condition=cond, seed=seed, actions_before_stopping=ag.actions,
                                    rules_committed_infinite=[NAMES[k] for k in inf],
                                    wrongly_infinite={NAMES[k]: world.p_true[k] for k in wrong},
                                    final_failure_streak=streak, cell_exception_retractions=ag.retractions,
                                    full_replanning_also_abandons=bool(other.failed),
                                    full_replanning_same_actions=other.actions == ag.actions, attempts=events))
    summary = dict(source_sha256=source_hash(), abandoned=len(out),
                   by_cause={}, streaks=sorted(s for e in out for s in e["final_failure_streak"].values()),
                   replanning_also_abandons=sum(e["full_replanning_also_abandons"] for e in out))
    for e in out:
        key = ", ".join(f"{r} (true success {p})" for r, p in e["wrongly_infinite"].items())
        summary["by_cause"][key] = summary["by_cause"].get(key, 0) + 1
    json.dump(dict(summary=summary, episodes=out), open(a.out, "w"), indent=1)
    print(json.dumps(summary, indent=1))
    e = out[0]
    print("example:", e["level"], e["start"], e["condition"], "seed", e["seed"])
    for ev in e["attempts"]:
        print("  ", ev["action"], ev["rule"], "entered" if ev["entered"] else "failed", ev["posterior_free_slow_blocked"],
              ev.get("commits", ""), "EXC+" if ev.get("cell_exception_added") else "", "RETRACT" if ev.get("cell_exceptions_retracted") else "")
