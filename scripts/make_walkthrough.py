"""Draws one real episode of the indexed-repair agent as a three-panel walkthrough.

Usage:  python3 scripts/make_walkthrough.py [--W 15] [--seed N] [--condition block] [--out paper/fig_walkthrough]
        python3 scripts/make_walkthrough.py --scan 1000 1300     # list candidate maps

Nothing here is simulated separately: the agent, map and random draws are the ones the
experiment uses, and the panels are snapshots taken inside the agent's own repair call.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from cpr.agents import Agent
from cpr.experiment import make_episode
from cpr.world import K, NOMINAL, WALL

TYPE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
VALUE_NAME = {0.9: "free", 0.3: "slow", 0.0: "blocked"}
INK, MUTED, WALLC = "#1f2328", "#8a9099", "#3d434b"
KEPT, REDONE = "#8a9099", "#c8102e"


class Traced(Agent):
    """Indexed-repair agent that records its route and a snapshot around each repair."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.trace, self.snaps, self.last_fail = [self.pos], [], None

    def route(self):
        """Cells of the current plan from the agent's position to the goal."""
        cells, seq = list(self.path), list(self.order) + [self.tower]
        for a, b in zip(seq, seq[1:]):
            cells += self.table[(min(a, b), max(a, b))].oriented(a)
        return cells

    def scoped_repair(self, events, force):
        keys = self._keys()
        inv = [key for key in keys if self.table[key].affected(events)]
        snap = dict(events=list(events), pos=self.pos, step=len(self.trace) - 1, fail=self.last_fail,
                    keys=keys, inv=inv, cost_before=self.plan_cost, order_before=list(self.order),
                    legs={key: [key[0]] + list(self.table[key].path) for key in keys},
                    route_before=self.route(), remaining=set(self.remaining),
                    exp_before=self.stats.expansions)
        super().scoped_repair(events, force)
        snap.update(route_after=self.route(), order_after=list(self.order), cost_after=self.plan_cost,
                    exp=self.stats.expansions - snap["exp_before"])
        self.snaps.append(snap)

    def step(self):
        v, before = self.path[0], self.pos
        self.last_fail = None
        if self.w.grid[v] >= 0:
            self.last_fail = v            # overwritten below if the move succeeded
        pos_holder = self
        # the repair (if any) happens inside super().step(), after the attempt
        orig = self.w.attempt

        def attempt(cell):
            ok = orig(cell)
            pos_holder.last_fail = None if ok else cell
            return ok
        self.w.attempt = attempt
        super().step()
        self.w.attempt = orig
        if self.pos != before:
            self.trace.append(self.pos)


def run(W, seed, condition, world=None):
    if world is None:
        ep = make_episode(W, seed, condition)
        if ep is None:
            return None
        world, meta = ep
    else:
        meta = dict(type=[k for k in range(K) if world.p_true[k] != NOMINAL[k]][0])
    ag = Traced("repair", world.clone())
    ag.start()
    first_route = ag.route()
    first_order = list(ag.order)
    full = Agent("replan", world.clone())
    full.start()
    while not ag.done and ag.actions < 30 * W * W:
        ag.step()
    while not full.done and full.actions < 30 * W * W:
        full.step()
    return dict(world=world, meta=meta, ag=ag, first_route=first_route, first_order=first_order,
                replan_actions=full.actions, replan_exp=full.stats.expansions - full.exp_initial)


def pick_snapshot(r):
    """The first repair triggered by the violated rule that changes the visiting order or route."""
    k = r["meta"]["type"]
    for s in r["ag"].snaps:
        if any(e[1] == k and e[0] in ("up", "down") for e in s["events"]) and s["inv"] \
                and len(s["inv"]) < len(s["keys"]) and s["route_before"] != s["route_after"]:
            return s
    return None


def xy(W, c):
    return c % W, c // W


def draw_map(ax, world, title):
    W = world.W
    ax.add_patch(Rectangle((-0.5, -0.5), W, W, fc="white", ec=MUTED, lw=0.6, zorder=0))
    for c, t in enumerate(world.grid):
        if t == WALL or t >= 0:
            x, y = xy(W, c)
            col = WALLC if t == WALL else TYPE_COLORS[t]
            ax.add_patch(Rectangle((x - 0.46, y - 0.46), 0.92, 0.92, fc=col, ec="none",
                                   alpha=1.0 if t == WALL else 0.85, zorder=1))
    for s in world.shrines:
        ax.plot(*xy(W, s), marker="o", ms=5.5, mfc="white", mec=INK, mew=1.1, zorder=6)
    ax.plot(*xy(W, world.tower), marker="*", ms=10, mfc="white", mec=INK, mew=1.0, zorder=6)
    ax.plot(*xy(W, world.start), marker="s", ms=5.5, mfc=INK, mec=INK, zorder=6)
    ax.set_xlim(-0.6, W - 0.4)
    ax.set_ylim(W - 0.4, -0.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=7.0 if len(title) < 30 else 7.6, color=INK, pad=3, loc="left")


def line(ax, W, cells, **kw):
    if len(cells) > 1:
        xs, ys = zip(*(xy(W, c) for c in cells))
        ax.plot(xs, ys, solid_capstyle="round", solid_joinstyle="round", **kw)


def figure(r, snap, out, shot=None, names=None, extent=None):
    world, ag, W = r["world"], r["ag"], r["world"].W
    k = r["meta"]["type"]
    L = "bcd" if shot else "abc"
    if shot:
        fig, axes = plt.subplots(1, 4, figsize=(7.0, 2.05), gridspec_kw=dict(width_ratios=[1.52, 1, 1, 1]))
        plt.subplots_adjust(left=0.004, right=0.996, top=0.90, bottom=0.235, wspace=0.05)
        img = plt.imread(shot)
        axes[0].imshow(img)
        axes[0].axis("off")
        axes[0].set_anchor("N")
        axes[0].set_title("(a) The game", fontsize=7.0, color=INK, pad=3, loc="left")
        axes = axes[1:]
    else:
        fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.72))
        plt.subplots_adjust(left=0.005, right=0.995, top=0.92, bottom=0.185, wspace=0.04)

    draw_map(axes[0], world, f"({L[0]}) Plan under assumed rules" if shot else f"({L[0]}) Plan under the assumed rules")
    line(axes[0], W, [world.start] + r["first_route"], color=INK, lw=1.6, zorder=4)

    walked = ag.trace[:snap["step"] + 1]
    n_inv, n_all = len(snap["inv"]), len(snap["keys"])
    draw_map(axes[1], world, f"({L[1]}) {n_inv} of {n_all} legs recomputed" if shot else f"({L[1]}) Rule revised: {n_inv} of {n_all} legs redone")
    for key in snap["keys"]:
        hit = key in snap["inv"]
        line(axes[1], W, snap["legs"][key], color=REDONE if hit else KEPT, lw=1.5 if hit else 1.0,
             ls=(0, (2.2, 1.6)) if hit else "-", alpha=0.95 if hit else 0.75, zorder=4 if hit else 3)
    line(axes[1], W, walked, color=INK, lw=1.6, zorder=5)
    axes[1].plot(*xy(W, snap["pos"]), marker="D", ms=5, mfc=INK, mec="white", mew=0.8, zorder=7)
    if snap["fail"] is not None:
        axes[1].plot(*xy(W, snap["fail"]), marker="x", ms=7, mec=REDONE, mew=2.0, zorder=8)

    draw_map(axes[2], world, f"({L[2]}) Route taken" if shot else f"({L[2]}) Route taken after repairs")
    line(axes[2], W, ag.trace, color=INK, lw=1.6, zorder=5)

    handles = [Patch(fc=TYPE_COLORS[t], alpha=0.85,
                     label=f"{names[t] if names else 'type %d' % (t + 1)}: assumed {VALUE_NAME[NOMINAL[t]]}"
                           + (f", really {VALUE_NAME[world.p_true[t]]}" if t == k else ""))
               for t in range(K) if world.type_cells[t]]
    handles += [Patch(fc=WALLC, label="wall"),
                Line2D([], [], marker="s", ls="", ms=5, mfc=INK, mec=INK, label="start"),
                Line2D([], [], marker="D", ls="", ms=4.5, mfc=INK, mec=INK, label="agent at the revision"),
                Line2D([], [], marker="o", ls="", ms=5, mfc="white", mec=INK, label="waypoint"),
                Line2D([], [], marker="*", ls="", ms=8, mfc="white", mec=INK, label="goal"),
                Line2D([], [], color=INK, lw=1.6, label="planned / walked"),
                Line2D([], [], color=KEPT, lw=1.0, label="cached leg kept"),
                Line2D([], [], color=REDONE, lw=1.4, ls=(0, (2.2, 1.6)), label="cached leg recomputed"),
                Line2D([], [], marker="x", ls="", ms=6, mec=REDONE, mew=1.8, label="failed entry")]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=6.0, frameon=False,
               handlelength=1.5, columnspacing=1.0, handletextpad=0.5, borderaxespad=0.1)
    for ext in ("pdf", "png"):
        fig.savefig(f"{out}.{ext}", dpi=300)
    plt.close(fig)


def describe(r, snap):
    ag = r["ag"]
    return dict(seed=r["world"].seed, W=r["world"].W, type=r["meta"]["type"] + 1, events=snap["events"],
                step=snap["step"], inv=len(snap["inv"]), legs=len(snap["keys"]),
                order_changed=snap["order_before"] != snap["order_after"],
                cost_before=round(snap["cost_before"], 2), cost_after=round(snap["cost_after"], 2),
                repairs=ag.repairs, actions=ag.actions, replan_actions=r["replan_actions"],
                post_exp=ag.stats.expansions - ag.exp_initial, replan_post_exp=r["replan_exp"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--W", type=int, default=15)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--condition", default="block")
    ap.add_argument("--scan", type=int, nargs=2)
    ap.add_argument("--out", default="paper/fig_walkthrough")
    ap.add_argument("--level", help="a Dice Adventure layout from scripts/game_levels.py, e.g. 11x11")
    ap.add_argument("--start", default="C2")
    ap.add_argument("--shot", help="game screenshot to show as the first panel")
    a = ap.parse_args()
    if a.level:
        import game_levels as g
        world = g.build(a.level, a.start, a.seed or 0)
        assert g.inject(world, a.condition) and g.solvable(world)
        r = run(world.W, world.seed, a.condition, world)
        s = pick_snapshot(r)
        figure(r, s, a.out, a.shot, ("stone", "trap", "monster 1", "monster 2", "monster 3"))
        print(describe(r, s))
        sys.exit()
    if a.scan:
        for seed in range(*a.scan):
            r = run(a.W, seed, a.condition)
            s = r and pick_snapshot(r)
            if s:
                print(describe(r, s))
    else:
        r = run(a.W, a.seed, a.condition)
        s = pick_snapshot(r)
        figure(r, s, a.out)
        print(describe(r, s))
