"""Agents for RuleGrid. One class, configured by kind:

  oracle        knows the true rules (reference for regret; not deployable)
  reactive      no rule revision; walls off a single cell after repeated failures
  replan        revises rule beliefs; recomputes the whole plan on every model change
  psrl          posterior sampling: plans against a sampled rule set
  ig_replan     probes to reduce rule uncertainty in general, then behaves like replan
  repair        revises beliefs; recomputes only legs whose rule support changed
  repair_probe  repair + plan-relevant probing, counterfactuals evaluated through the index
  replan_probe  the same probing rule, evaluated by full replanning over all rules
"""
import math
import random

from .planner import INF, Leg, Stats, astar, best_order, cost_array
from .world import K, NOMINAL, VALUES

DEFAULTS = dict(strength=0.7, block_mult=0.8, kappa=0.95, delta=0.10, n_patch=8,
                resolved=0.95, ig_resolved=0.90, probe_cap=20, margin=0.25)

KINDS = ("oracle", "reactive", "replan", "psrl", "ig_replan", "repair", "repair_probe", "replan_probe")


class Belief:
    def __init__(self, P, W):
        s = P["strength"]
        self.b = [[s if v == NOMINAL[k] else (1 - s) / 2 for v in VALUES] for k in range(K)]
        self.block_cost, self.kappa = P["block_mult"] * W, P["kappa"]

    def posterior(self, k, ok):
        post = [p * (v if ok else 1 - v) for p, v in zip(self.b[k], VALUES)]
        z = sum(post)
        return [p / z for p in post] if z > 0 else list(self.b[k])

    def update(self, k, ok):
        self.b[k] = self.posterior(k, ok)

    def cost_of(self, dist):
        if dist[2] >= self.kappa:
            return INF
        return dist[0] / VALUES[0] + dist[1] / VALUES[1] + dist[2] * self.block_cost

    def cost(self, k):
        return self.cost_of(self.b[k])

    def p_succ(self, k):
        return sum(p * v for p, v in zip(self.b[k], VALUES))


def entropy(dist):
    return -sum(p * math.log(p) for p in dist if p > 0)


class Agent:
    def __init__(self, kind, world, P=None, diag=None):
        self.kind, self.w = kind, world
        self.P = dict(DEFAULTS, **(P or {}))
        self.W, self.tower = world.W, world.tower
        self.stats = Stats()
        self.revises = kind not in ("oracle", "reactive")
        self.family = "repair" if kind in ("repair", "repair_probe") else "replan"
        self.belief = Belief(self.P, self.W)
        if self.revises:
            self.c = [self.belief.cost(k) for k in range(K)]
        else:
            self.c = [1 / v if v > 0 else INF for v in NOMINAL]
        self.rng = random.Random(world.seed * 31 + 7)
        self.patched, self.fail = set(), {}
        self.table = {}
        self.pos, self.remaining = world.start, set(world.shrines)
        self.order, self.target, self.path, self.cur_leg = [], None, [], None
        self.mode, self.probe_cell = "plan", None
        self.done = self.failed = False
        self.diag = diag
        self.actions = self.probes = self.triggers = self.patches = 0
        self.full_replans = self.repairs = self.noops = 0
        self.legs_recomputed = self.legs_reused = 0
        self.sample = None
        self.retractions = 0

    # ---------------------------------------------------------------- planning
    def build_arr(self):
        if self.kind == "oracle":
            w = self.w
            arr = cost_array(w, [1.0] * K, ())
            for cells in w.type_cells:
                for x in cells:
                    p = w.true_p(x)
                    arr[x] = 1 / p if p > 0 else INF
            return arr
        return cost_array(self.w, self.sample if self.sample is not None else self.c, self.patched)

    def _search(self, a, b, arr=None, stats=None):
        cost, path = astar(self.W, self.arr if arr is None else arr, a, b, stats or self.stats)
        return Leg(self.w, a, b, cost, path or [], self.patched)

    def _keys(self):
        rem = sorted(self.remaining)
        keys = [(rem[i], rem[j]) for i in range(len(rem)) for j in range(i + 1, len(rem))]
        return keys + [(min(s, self.tower), max(s, self.tower)) for s in rem]

    def _anchor(self, reuse_current):
        """Legs from the current position, then the best ordering."""
        targets = sorted(self.remaining) or [self.tower]
        first, legs = {}, {}
        for s in targets:
            if reuse_current and s == self.target and self.mode == "plan" and self.path:
                first[s], legs[s] = sum(self.arr[v] for v in self.path), None
            else:
                legs[s] = self._search(self.pos, s)
                first[s] = legs[s].cost
        fixed = {key: self.table[key].cost for key in self._keys()}
        order, total = best_order(first, fixed, self.remaining, self.tower)
        if total == INF:
            self.plan_cost = INF
            return
        self.order, self.plan_cost = order, total
        self.target = order[0] if order else self.tower
        if legs[self.target] is not None:
            self.cur_leg = legs[self.target]
            self.path = list(self.cur_leg.path)
        self.mode = "plan"

    def full_replan(self):
        self.arr = self.build_arr()
        for key in self._keys():
            self.table[key] = self._search(key[0], key[1])
            self.legs_recomputed += 1
        self.mode = "plan"
        self._anchor(False)
        self.full_replans += 1

    def scoped_repair(self, events, force):
        self.arr = self.build_arr()
        keys = self._keys()
        inv = [key for key in keys if self.table[key].affected(events)]
        cur_aff = self.mode != "plan" or self.cur_leg is None or self.cur_leg.affected(events)
        only_up = all(kind != "down" for kind, _ in events)
        if self.diag is not None:
            self._diag_before(keys, inv)
        if only_up and not inv and not cur_aff and not force:
            self.noops += 1
            self.legs_reused += len(keys)
        else:
            for key in inv:
                self.table[key] = self._search(key[0], key[1])
            self.legs_recomputed += len(inv)
            self.legs_reused += len(keys) - len(inv)
            self._anchor(not cur_aff)
            self.repairs += 1
        if self.diag is not None:
            self._diag_after(keys)

    def current_plan_cost(self):
        seq = (self.order or []) + [self.tower] if self.order else [self.tower]
        cost = sum(self.arr[v] for v in self.path)
        for a, b in zip(seq, seq[1:]):
            cost += self.table[(min(a, b), max(a, b))].cost
        return cost

    # ------------------------------------------------- diagnostics (evaluation only)
    def _diag_before(self, keys, inv):
        shadow = Stats()
        fresh = {key: astar(self.W, self.arr, key[0], key[1], shadow)[0] for key in keys}
        changed = {key for key in keys if abs(fresh[key] - self.table[key].cost) > 1e-9}
        flagged = set(inv)
        d = self.diag
        d["flagged"] += len(flagged)
        d["changed"] += len(changed)
        d["hit"] += len(flagged & changed)
        d["missed"] += len(changed - flagged)
        d["legs"] += len(keys)
        self._fresh = fresh

    def _diag_after(self, keys):
        shadow = Stats()
        targets = sorted(self.remaining) or [self.tower]
        first = {s: astar(self.W, self.arr, self.pos, s, shadow)[0] for s in targets}
        _, total = best_order(first, self._fresh, self.remaining, self.tower)
        d = self.diag
        d["repairs"] += 1
        if abs(total - self.current_plan_cost()) > 1e-6:
            d["mismatch"] += 1

    # ---------------------------------------------------------------- execution
    def start(self):
        if self.kind == "psrl":
            self.psrl_plan()
            self.exp_initial = self.stats.expansions
        else:
            self.full_replan()
            self.full_replans = 0
            self.exp_initial = self.stats.expansions
            self.decision_point()

    def observe(self, v, k, ok):
        events = []
        if self.revises:
            self.belief.update(k, ok)
            new, old = self.belief.cost(k), self.c[k]
            if (new == INF) != (old == INF) or (old < INF and abs(new - old) > self.P["delta"] * old):
                events.append(("up" if new > old else "down", k))
                self.c[k] = new
                self.triggers += 1
        if self.kind == "oracle":
            return events
        if ok:
            self.fail[v] = 0
        else:
            self.fail[v] = self.fail.get(v, 0) + 1
            if self.fail[v] >= self.P["n_patch"] and v not in self.patched and self.c[k] < INF:
                self.patched.add(v)
                self.patches += 1
                events.append(("patch", v))
        return events

    def retract_patches(self):
        """Cell exceptions are soft: drop them if they have made the goal unreachable."""
        self.retractions += 1
        self.patched.clear()
        self.fail.clear()

    def advance(self):
        prev = self.target
        self.order = [s for s in self.order if s != prev]
        nxt = self.order[0] if self.order else self.tower
        rec = self.table[(min(prev, nxt), max(prev, nxt))]
        self.cur_leg, self.path, self.target = rec, rec.oriented(prev), nxt

    def step(self):
        v = self.path[0]
        k = self.w.grid[v]
        events, attempted = [], False
        if k >= 0:
            ok, attempted = self.w.attempt(v), True
            if ok:
                self.pos = v
                self.path.pop(0)
            events = self.observe(v, k, ok)
        else:
            self.pos = v
            self.path.pop(0)
        self.actions += 1
        arrived = incidental = False
        if self.pos in self.remaining:
            self.remaining.discard(self.pos)
            if self.mode == "plan" and self.pos == self.target:
                arrived = True
            else:
                incidental = True
                self.order = [s for s in self.order if s != self.pos]
        if not self.remaining and self.pos == self.tower:
            self.done = True
            return
        probe_done = self.mode == "probe" and (not self.path or (attempted and v == self.probe_cell))
        if self.kind == "psrl":
            # Resample after every observation: a posterior sample is only valid until new evidence arrives.
            if attempted or arrived or incidental or not self.path:
                self.psrl_plan()
            return
        decide = True
        if arrived:
            self.advance()
        if events:
            if self.family == "repair":
                self.scoped_repair(events, force=incidental or probe_done)
            else:
                self.full_replan()
        elif probe_done or (incidental and self.mode == "plan"):
            self.arr = self.build_arr()
            self._anchor(False)
        elif not arrived:
            decide = False
        if self.plan_cost == INF and self.patched:
            self.retract_patches()
            self.full_replan()
        if self.plan_cost == INF:
            self.failed = self.done = True
            return
        if decide:
            self.decision_point()

    # ---------------------------------------------------------------- deciding
    def decision_point(self):
        if self.kind == "ig_replan":
            self.choose_ig_probe()
        elif self.kind == "repair_probe":
            self.choose_voi_probe(indexed=True)
        elif self.kind == "replan_probe":
            self.choose_voi_probe(indexed=False)

    def psrl_plan(self):
        for _ in range(10):
            self.sample = []
            for k in range(K):
                v = self.rng.choices(VALUES, weights=self.belief.b[k])[0]
                self.sample.append(1 / v if v > 0 else INF)
            self.full_replan()
            if self.plan_cost < INF:
                return
        self.retract_patches()
        self.sample = [c if c < INF else self.belief.block_cost for c in self.c]
        self.full_replan()
        if self.plan_cost == INF:
            self.failed = self.done = True

    def _nearest(self, k):
        px, py, W = self.pos % self.W, self.pos // self.W, self.W
        best = None
        for x in self.w.type_cells[k]:
            if x in self.patched or x == self.pos:
                continue
            d = abs(x % W - px) + abs(x // W - py)
            if best is None or (d, x) < best:
                best = (d, x)
        return best

    def _start_probe(self, x, path):
        self.mode, self.path, self.probe_cell, self.cur_leg = "probe", list(path), x, None
        self.probes += 1

    def choose_ig_probe(self):
        if self.probes >= self.P["probe_cap"]:
            return
        best = None
        for k in range(K):
            b = self.belief.b[k]
            if self.c[k] == INF or max(b) >= self.P["ig_resolved"]:
                continue
            near = self._nearest(k)
            if near is None:
                continue
            ps = self.belief.p_succ(k)
            gain = entropy(b) - ps * entropy(self.belief.posterior(k, True)) \
                - (1 - ps) * entropy(self.belief.posterior(k, False))
            score = gain / (near[0] + 1)
            if best is None or score > best[0]:
                best = (score, near[1])
        if best is None:
            return
        cost, path = astar(self.W, self.arr, self.pos, best[1], self.stats)
        if cost < INF:
            self._start_probe(best[1], path)

    def cf_value(self, k, ck, pos2, indexed, memo):
        """Cost of the best plan from pos2 if rule k had planning cost ck (a counterfactual)."""
        if (k, ck) not in memo:
            tc = list(self.c)
            tc[k] = ck
            arr2 = cost_array(self.w, tc, self.patched)
            events = [] if ck == self.c[k] else [("up" if ck > self.c[k] else "down", k)]
            fixed = {}
            for key in self._keys():
                rec = self.table[key]
                if indexed and not rec.affected(events):
                    fixed[key] = rec.cost
                else:
                    fixed[key] = astar(self.W, arr2, key[0], key[1], self.stats)[0]
            memo[(k, ck)] = (arr2, fixed)
        arr2, fixed = memo[(k, ck)]
        targets = sorted(self.remaining) or [self.tower]
        first = {s: astar(self.W, arr2, pos2, s, self.stats)[0] for s in targets}
        return best_order(first, fixed, self.remaining, self.tower)[1]

    def choose_voi_probe(self, indexed):
        if self.probes >= self.P["probe_cap"] or self.mode != "plan":
            return
        cands = [k for k in range(K) if self.c[k] < INF and max(self.belief.b[k]) < self.P["resolved"]]
        if indexed:
            seq = self.order + [self.tower] if self.order else [self.tower]
            legs = [self.cur_leg] + [self.table[(min(a, b), max(a, b))] for a, b in zip(seq, seq[1:])]
            relevant = set()
            for leg in legs:
                if leg is not None:
                    relevant |= leg.val | leg.blk
            cands = [k for k in cands if k in relevant]
        q_exec, best, memo = self.current_plan_cost(), None, {}
        for k in cands:
            near = self._nearest(k)
            if near is None:
                continue
            x = near[1]
            cost, path = astar(self.W, self.arr, self.pos, x, self.stats)
            if cost == INF:
                continue
            prev = path[-2] if len(path) > 1 else self.pos
            ps = self.belief.p_succ(k)
            q = cost - self.arr[x] + 1.0
            for ok, pr, pos2 in ((True, ps, x), (False, 1 - ps, prev)):
                if pr > 1e-12:
                    ck = self.belief.cost_of(self.belief.posterior(k, ok))
                    q += pr * self.cf_value(k, ck, pos2, indexed, memo)
            if best is None or q < best[0]:
                best = (q, x, path)
        if best is not None and best[0] < q_exec - self.P["margin"]:
            self._start_probe(best[1], best[2])


def run_episode(kind, world, P=None, diag=None):
    ag = Agent(kind, world, P, diag)
    ag.start()
    cap = 30 * world.W * world.W
    while not ag.done and ag.actions < cap:
        ag.step()
    return dict(agent=kind, completed=bool(ag.done and not ag.failed), actions=ag.actions,
                expansions=ag.stats.expansions, exp_initial=ag.exp_initial, searches=ag.stats.searches, probes=ag.probes,
                triggers=ag.triggers, patches=ag.patches, full_replans=ag.full_replans,
                repairs=ag.repairs, noops=ag.noops, retractions=ag.retractions, legs_recomputed=ag.legs_recomputed,
                legs_reused=ag.legs_reused)


def nominal_plan_legs(world, P=None):
    """Legs of the plan a belief-revising agent starts with, in execution order."""
    ag = Agent("replan", world.clone(), P)
    ag.full_replan()
    seq = ag.order + [ag.tower]
    return [ag.cur_leg] + [ag.table[(min(a, b), max(a, b))] for a, b in zip(seq, seq[1:])]
