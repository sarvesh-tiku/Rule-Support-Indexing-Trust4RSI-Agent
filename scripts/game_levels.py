"""Post-hoc check on the four larger Dice Adventure level layouts (not pre-registered).

The layouts (walls, obstacle positions, shrines, tower, character starts) are the game's.
The task and the rules are the simulator's: one agent starts where a character starts,
visits the three shrines in any order and ends on the tower, and the game's five obstacle
kinds are given the simulator's nominal rule values in the fixed order of KIND_ORDER.
Game mechanics (dice, health, sight, turns, three cooperating characters) are not modelled.

Usage:  python3 scripts/game_levels.py --draws 50 --out results/game_levels.json
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from cpr.agents import nominal_plan_legs, run_episode
from cpr.experiment import source_hash
from cpr.planner import INF, Stats, astar
from cpr.world import K, NOMINAL, OPEN, WALL, World

# Rows run from the top of the board down; two characters per cell.
# ## wall, ** tower, K1-K3 shrines, C1-C3 character starts, S1 stone, T1 trap, M1-M3 monsters.
LEVELS = {
    "8x11": "..C3..C1........|....##K1........|....##....######|....##........##|....##..K3..**..|"
            "....T1..........|######....M1....|..K2S1....######|....##C2..T1....|....##....##....|"
            "######....##....",
    "9x9": "##..C1C2##......##|K3T1..M2####M1..K1|##..M1........S1##|......M2....T1....|"
           "..M2....C3....**##|##S1##....M1##..##|..##..S1..T1##..##|####....####..M2##|"
           "......M1....K2..##",
    "11x8": "......M2**K2T1M1M2##..|T1..S1####T1....####..|K1S1..............S1M3|"
            "M1##......S1......S1S1|....##S1##M2##S1......|..M1##..##..##..##....|"
            "..##....##..##..##..T1|..T1..C1C2C3....##S1K3",
    "11x11": "..K2..##########......|..##M1....M1....M1##..|........##..########..|"
             "##T1######..####......|M2....##..C1..##T1##..|......S1..**......##..|"
             "..######C2..C3##..S1S1|......####..####..##..|####..T1......##......|"
             "K3##..##..M2..T1####K1|......##....##........",
}
KIND_ORDER = ("S1", "T1", "M1", "M2", "M3")   # nominal: free, free, slow, blocked, blocked
AGENTS = ("oracle", "reactive", "replan", "repair", "repair_probe")
CONDITIONS = ("none", "block", "slow", "unlock")


def build(name, start_char, seed):
    rows = [[r[i:i + 2] for i in range(0, len(r), 2)] for r in LEVELS[name].split("|")]
    h, w = len(rows), len(rows[0])
    W = max(h, w)
    grid, starts, shrines, tower = [WALL] * (W * W), {}, [], None
    for y, row in enumerate(rows):
        for x, tok in enumerate(row):
            c = y * W + x
            grid[c] = WALL if tok == "##" else (KIND_ORDER.index(tok) if tok in KIND_ORDER else OPEN)
            if tok[0] == "C":
                starts[tok] = c
            elif tok[0] == "K":
                shrines.append(c)
            elif tok == "**":
                tower = c
    return World(W, grid, starts[start_char], shrines, tower, seed)


def inject(world, condition):
    """Same definitions as cpr.experiment.make_episode, against the initial plan."""
    legs = nominal_plan_legs(world)
    first_val, first_any = {}, {}
    for i, leg in enumerate(legs):
        for k in leg.val:
            first_val.setdefault(k, i)
            first_any.setdefault(k, i)
        for k in leg.blk:
            first_any.setdefault(k, i)
    if condition == "none":
        return True
    if condition in ("block", "slow"):
        cands = sorted((i, k) for k, i in first_val.items() if NOMINAL[k] == 0.9)
        if not cands:
            return False
        world.p_true[cands[0][1]] = 0.0 if condition == "block" else 0.3
    else:
        cands = sorted((i, k) for k, i in first_any.items() if NOMINAL[k] == 0.0)
        if not cands:
            return False
        world.p_true[cands[0][1]] = 0.9
    return True


def solvable(world):
    """Unlike the generated maps, game levels can need an obstacle crossing, so a violation can
    make the task impossible. Such configurations are excluded and counted."""
    arr = [INF if t == WALL or (t >= 0 and world.p_true[t] == 0) else 1.0 for t in world.grid]
    return all(astar(world.W, arr, world.start, p, Stats())[0] < INF for p in world.shrines + [world.tower])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=50)
    ap.add_argument("--out", default="results/game_levels.json")
    a = ap.parse_args()
    rows, skipped = [], []
    for name in LEVELS:
        for ch in ("C1", "C2", "C3"):
            for cond in CONDITIONS:
                for seed in range(a.draws):
                    world = build(name, ch, seed)
                    if not inject(world, cond):
                        skipped.append((name, ch, cond, "no rule fits the condition"))
                        break
                    if not solvable(world):
                        skipped.append((name, ch, cond, "goal unreachable under the true rules"))
                        break
                    r = {ag: run_episode(ag, world.clone()) for ag in AGENTS}
                    rows.append(dict(level=name, start=ch, condition=cond, seed=seed,
                                     **{f"{ag}_{m}": r[ag][m] for ag in AGENTS for m in ("actions", "completed")},
                                     **{f"{ag}_post": r[ag]["expansions"] - r[ag]["exp_initial"] for ag in AGENTS},
                                     repairs=r["repair"]["repairs"]))
    def summarise(sel):
        n = len(sel)
        if not n:
            return None
        mean = lambda key: sum(x[key] for x in sel) / n
        return dict(n=n, completed=all(x[f"{ag}_completed"] for x in sel for ag in AGENTS),
                    identical_actions=sum(x["repair_actions"] == x["replan_actions"] for x in sel),
                    work_ratio=round(mean("repair_post") / mean("replan_post"), 3) if mean("replan_post") else None,
                    repair_post=round(mean("repair_post"), 1), replan_post=round(mean("replan_post"), 1),
                    repairs=round(mean("repairs"), 2),
                    probe_minus_noprobe=round(mean("repair_probe_actions") - mean("repair_actions"), 2),
                    revise_minus_norevise=round(mean("repair_actions") - mean("reactive_actions"), 2),
                    oracle_actions=round(mean("oracle_actions"), 1))
    viol = [x for x in rows if x["condition"] != "none"]
    out = dict(source_sha256=source_hash(), draws=a.draws, kind_order=KIND_ORDER, nominal=NOMINAL,
               episodes=len(rows), skipped=skipped, violations_pooled=summarise(viol),
               by_level={n: summarise([x for x in viol if x["level"] == n]) for n in LEVELS},
               by_condition={c: summarise([x for x in rows if x["condition"] == c]) for c in CONDITIONS},
               cells_available=sorted({(x["level"], x["start"], x["condition"]) for x in rows}))
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("episodes", "skipped", "violations_pooled", "by_level", "by_condition")}, indent=1))
