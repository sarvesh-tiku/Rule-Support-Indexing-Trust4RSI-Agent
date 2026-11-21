"""Why revising agents abandoned reachable goals on the game levels, and a staged-commit safeguard.

Root cause (see the trace printed by --trace): the agent commits a rule as certainly blocked once
its posterior passes kappa = 0.95. Where that rule guards the only way to a waypoint, the plan
cost becomes infinite and the agent stops. A slow obstacle (success 0.3) fails 13 times in a row
with probability 0.7^13 = 0.97%, which is enough to cross kappa.

Safeguard (StagedAgent): a commit that would make the goal unreachable is staged, not applied.
The rule keeps a finite cost computed from the same posterior, is marked contested, and the agent
keeps acting on it. It gives up only when a contested rule's posterior passes a second, stricter
threshold (default 0.999). This cannot make an unreachable goal reachable; it buys a lower chance
of wrongly abandoning at the price of extra failed attempts when the goal really is unreachable.

Usage:  python3 scripts/abandonment.py --draws 50 --out results/abandonment.json
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
from cpr.world import K, VALUES


class StagedAgent(Agent):
    def __init__(self, kind, world, strict=0.999):
        super().__init__(kind, world)
        self.strict, self.contested = strict, set()
        self.staged = self.gave_up_strict = 0
        normal = self.belief.cost

        def cost(k):
            if k in self.contested:
                d = self.belief.b[k]
                if d[2] >= self.strict:
                    return INF
                return d[0] / VALUES[0] + d[1] / VALUES[1] + d[2] * self.belief.block_cost
            return normal(k)
        self.belief.cost = cost

    def step(self):
        super().step()
        if not self.failed:
            return
        # The commit just applied made the goal unreachable. Stage it instead.
        newly = [k for k in range(K) if self.c[k] == INF and k not in self.contested
                 and self.belief.b[k][2] < self.strict]
        if not newly:
            self.gave_up_strict += 1      # every rule in the way is past the strict threshold
            return
        self.failed = self.done = False
        self.contested.update(newly)
        self.staged += len(newly)
        for k in newly:
            self.c[k] = self.belief.cost(k)
        self.patched.clear()
        self.fail.clear()
        self.full_replan()
        if self.plan_cost == INF:
            self.failed = self.done = True


def play(agent):
    agent.start()
    cap = 30 * agent.W * agent.W
    while not agent.done and agent.actions < cap:
        agent.step()
    return dict(done=bool(agent.done and not agent.failed), abandoned=bool(agent.failed), actions=agent.actions,
                post=agent.stats.expansions - agent.exp_initial, staged=getattr(agent, "staged", 0))


def collect(solvable_wanted, draws):
    rows = []
    for name in g.LEVELS:
        for ch in ("C1", "C2", "C3"):
            for cond in g.CONDITIONS:
                for seed in range(draws):
                    world = g.build(name, ch, seed)
                    if not g.inject(world, cond) or g.solvable(world) != solvable_wanted:
                        break
                    row = dict(level=name, start=ch, condition=cond, seed=seed)
                    for label, make in (("repair", lambda w: Agent("repair", w)),
                                        ("replan", lambda w: Agent("replan", w)),
                                        ("repair_staged", lambda w: StagedAgent("repair", w)),
                                        ("replan_staged", lambda w: StagedAgent("replan", w))):
                        row[label] = play(make(world.clone()))
                    rows.append(row)
    return rows


def summarise(rows):
    n = len(rows)
    out = dict(episodes=n)
    for a in ("repair", "replan", "repair_staged", "replan_staged"):
        out[a] = dict(finished=sum(r[a]["done"] for r in rows), abandoned=sum(r[a]["abandoned"] for r in rows),
                      mean_actions=round(sum(r[a]["actions"] for r in rows) / n, 2),
                      mean_post_expansions=round(sum(r[a]["post"] for r in rows) / n, 1),
                      episodes_with_staged_commit=sum(r[a]["staged"] > 0 for r in rows))
    same = [r for r in rows if r["repair_staged"]["staged"] == 0]
    out["untouched_episodes"] = len(same)
    out["untouched_identical_actions"] = sum(r["repair_staged"]["actions"] == r["repair"]["actions"] for r in same)
    out["staged_repair_equals_staged_replan_actions"] = sum(
        r["repair_staged"]["actions"] == r["replan_staged"]["actions"] for r in rows)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=50)
    ap.add_argument("--out", default="results/abandonment.json")
    a = ap.parse_args()
    reach, unreach = collect(True, a.draws), collect(False, a.draws)
    out = dict(source_sha256=source_hash(), draws=a.draws, strict=0.999,
               reachable_goal=summarise(reach), unreachable_goal=summarise(unreach))
    json.dump(dict(out, rows=dict(reachable=reach, unreachable=unreach)), open(a.out, "w"))
    print(json.dumps(out, indent=1))
