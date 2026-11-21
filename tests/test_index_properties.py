"""Property tests for the rule-support index, at the planner level (no agent, no beliefs).

Run:  python3 tests/test_index_properties.py

They check Proposition 1 against arbitrary rule costs and arbitrary sequences of revisions,
including reversals, and they pin down the two things the proposition depends on:
  * the optimality support (blk) is needed: tracking only the rules a leg uses misses changes;
  * every obstacle cell must cost at least 1 + epsilon under every committed model.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cpr.planner import INF, MIN_OBSTACLE_EXTRA, Leg, Stats, astar, cost_array
from cpr.world import K, OPEN, WALL, World, gen_map

EPS = MIN_OBSTACLE_EXTRA


def build_table(world, costs, points):
    arr = cost_array(world, costs, ())
    table = {}
    for i, a in enumerate(points):
        for b in points[i + 1:]:
            c, path = astar(world.W, arr, a, b, Stats())
            table[(a, b)] = Leg(world, a, b, c, path or [], set())
    return table


def random_cost(rng, low=1 + EPS):
    r = rng.random()
    if r < 0.15:
        return INF
    if r < 0.45:
        return low
    return low + rng.random() * rng.choice((0.5, 3.0, 12.0))


def revise(world, table, costs, k, new, use_blk=True):
    """Commit rule k := new, invalidate by the index, recompute. Returns (#recomputed, #stale)."""
    old = costs[k]
    costs[k] = new
    if new == old:
        return 0, 0
    kind = "up" if new > old else "down"
    arr = cost_array(world, costs, ())
    redone = 0
    for key, leg in list(table.items()):
        hit = leg.affected([(kind, k)]) if use_blk else k in leg.val
        if hit:
            c, path = astar(world.W, arr, key[0], key[1], Stats())
            table[key] = Leg(world, key[0], key[1], c, path or [], set())
            redone += 1
    stale = 0
    for key, leg in table.items():
        fresh = astar(world.W, arr, key[0], key[1], Stats())[0]
        if not (fresh == leg.cost or abs(fresh - leg.cost) <= 1e-9):
            stale += 1
    return redone, stale


def run_sequences(use_blk, n_worlds=60, n_steps=25):
    total = dict(revisions=0, reversals=0, redone=0, legs=0, stale=0, stale_revisions=0)
    for seed in range(n_worlds):
        rng = random.Random(seed)
        world = gen_map(rng.choice((7, 9, 11, 13)), 5000 + seed)
        points = [world.start] + world.shrines + [world.tower]
        costs = [random_cost(rng) for _ in range(K)]
        table = build_table(world, costs, points)
        history = {k: [costs[k]] for k in range(K)}
        for _ in range(n_steps):
            k = rng.randrange(K)
            if rng.random() < 0.35 and len(history[k]) > 1:
                new = rng.choice(history[k][:-1])          # reverse an earlier commit of this rule
                total["reversals"] += new != costs[k]
            else:
                new = random_cost(rng)
            history[k].append(new)
            redone, stale = revise(world, table, costs, k, new, use_blk)
            total["revisions"] += 1
            total["redone"] += redone
            total["legs"] += len(table)
            total["stale"] += stale
            total["stale_revisions"] += stale > 0
            if stale and not use_blk:
                # bring the table back to a correct state so later errors are counted separately
                table = build_table(world, costs, points)
    return total


def test_index_is_exact_over_random_revision_sequences_with_reversals():
    t = run_sequences(use_blk=True)
    assert t["revisions"] == 1500 and t["reversals"] > 100
    assert t["stale"] == 0, t
    assert t["redone"] < t["legs"], "the index should not invalidate everything"
    return t


def test_direct_support_alone_leaves_stale_legs():
    t = run_sequences(use_blk=False)
    assert t["stale"] > 0, "tracking only used rules should miss cheaper alternatives"
    return t


def two_route_world():
    # 2x2: from (0,0) to (1,1) either through (1,0) [type 0] or through (0,1) [type 1].
    return World(2, [OPEN, 0, 1, OPEN], 0, [], 3, seed=0)


def test_tie_is_not_indexed_and_need_not_be():
    """With every obstacle cell at >= 1 + eps, an unindexed alternative can at best tie."""
    w = two_route_world()
    costs = [1 + EPS, 5.0, 9, 9, 9]
    table = build_table(w, costs, [0, 3])
    leg = table[(0, 3)]
    assert leg.val == frozenset({0}) and 1 not in leg.blk
    redone, stale = revise(w, table, costs, 1, 1 + EPS)      # the other route now costs the same
    assert redone == 0 and stale == 0


def test_bound_fails_if_an_obstacle_cell_may_cost_less_than_one_plus_eps():
    """Counterexample showing the assumption is needed, not just convenient."""
    w = two_route_world()
    costs = [1 + EPS, 5.0, 9, 9, 9]
    table = build_table(w, costs, [0, 3])
    redone, stale = revise(w, table, costs, 1, 1.0)          # violates the cost floor
    assert redone == 0 and stale == 1


def oracle_cost(world, arr, a, b):
    """Bellman-Ford on the grid. Shares no code with astar: an independent check of leg costs."""
    W = world.W
    dist = {a: 0.0}
    frontier = [a]
    while frontier:
        nxt = []
        for u in frontier:
            x, y = u % W, u // W
            for vx, vy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= vx < W and 0 <= vy < W:
                    v = vy * W + vx
                    if arr[v] < INF and dist[u] + arr[v] < dist.get(v, INF) - 1e-12:
                        dist[v] = dist[u] + arr[v]
                        nxt.append(v)
        frontier = nxt
    return dist.get(b, INF)


def test_simultaneous_revisions_and_cell_exceptions_against_independent_oracle():
    """One commit may raise some rules, lower others and add cell exceptions at once. Maps are
    generated WITHOUT the open-connectivity guarantee, so legs can be unreachable (infinite)."""
    import random as _r
    total = dict(commits=0, mixed=0, with_exception=0, legs=0, redone=0, stale=0, unreachable_legs=0)
    for seed in range(80):
        rng = _r.Random(900 + seed)
        W = rng.choice((6, 8, 10))
        grid = [OPEN] * (W * W)
        for c in range(W * W):
            r = rng.random()
            grid[c] = WALL if r < 0.12 else (rng.randrange(K) if r < 0.50 else OPEN)
        opens = [c for c in range(W * W) if grid[c] == OPEN]
        points = rng.sample(opens, 5)
        world = World(W, grid, points[0], points[1:4], points[4], seed)
        costs = [random_cost(rng) for _ in range(K)]
        patched = set()
        arr = cost_array(world, costs, patched)
        table = {}
        for i, a in enumerate(points):
            for b in points[i + 1:]:
                c, path = astar(W, arr, a, b, Stats())
                table[(a, b)] = Leg(world, a, b, c, path or [], set(patched))
        for _ in range(12):
            events, kinds = [], set()
            for k in rng.sample(range(K), rng.choice((1, 2, 2, 3, 4))):
                new = random_cost(rng)
                if new != costs[k]:
                    kind = "up" if new > costs[k] else "down"
                    events.append((kind, k))
                    kinds.add(kind)
                    costs[k] = new
            if rng.random() < 0.3:
                cand = [c for c in range(W * W) if grid[c] >= 0 and c not in patched]
                if cand:
                    x = rng.choice(cand)
                    patched.add(x)
                    events.append(("patch", x))
                    total["with_exception"] += 1
            if not events:
                continue
            total["commits"] += 1
            total["mixed"] += len(kinds) == 2
            arr = cost_array(world, costs, patched)
            for key, leg in list(table.items()):
                if leg.affected(events):
                    c, path = astar(W, arr, key[0], key[1], Stats())
                    table[key] = Leg(world, key[0], key[1], c, path or [], set(patched))
                    total["redone"] += 1
            for key, leg in table.items():
                truth = oracle_cost(world, arr, key[0], key[1])
                total["legs"] += 1
                total["unreachable_legs"] += truth == INF
                if not (truth == leg.cost or abs(truth - leg.cost) <= 1e-9):
                    total["stale"] += 1
    assert total["mixed"] > 100 and total["with_exception"] > 100 and total["unreachable_legs"] > 0, total
    assert total["stale"] == 0, total
    assert total["redone"] < total["legs"]
    return total


def detour_world():
    # 5x5: a wall column at x=2 with a single type-0 cell at (2,2); the only other way is row 4.
    W = 5
    grid = [OPEN] * 25
    for y in range(4):
        grid[y * W + 2] = WALL
    grid[2 * W + 2] = 0
    return World(W, grid, 0, [], 4, seed=1)


def test_unused_rule_gets_cheaper_old_plan_feasible_but_suboptimal():
    """The case alternative support exists for. Rule 0 is expensive, so the leg from (0,0) to (4,0)
    walks around it and does not use it. Rule 0 is then revised to its cheapest value. The old path is
    untouched and still walkable, so direct-support tracking keeps it; it is now 3.9 more expensive
    than the best path. The index lists rule 0 in the leg's alternative support and recomputes."""
    w = detour_world()
    before, after = [50.0, 9, 9, 9, 9], [1 + EPS, 9, 9, 9, 9]
    table = build_table(w, before, [0, 4])
    leg = table[(0, 4)]
    assert leg.cost == 12.0 and leg.val == frozenset() and 0 in leg.blk
    arr = cost_array(w, after, ())
    old_path_cost_now = sum(arr[v] for v in leg.path)
    fresh = astar(w.W, arr, 0, 4, Stats())[0]
    assert old_path_cost_now == 12.0                      # still feasible, cost unchanged
    assert abs(fresh - (7 + 1 + EPS)) < 1e-9              # 8 cells, one of them the type-0 cell
    kept = dict(table)
    costs = list(before)
    redone_val, stale_val = revise(w, kept, costs, 0, after[0], use_blk=False)
    assert redone_val == 0 and stale_val == 1             # direct support only: keeps the stale leg
    costs = list(before)
    redone, stale = revise(w, table, costs, 0, after[0], use_blk=True)
    assert redone == 1 and stale == 0 and abs(table[(0, 4)].cost - fresh) < 1e-9
    return dict(old_plan_cost=old_path_cost_now, optimal_cost=round(fresh, 3), excess=round(old_path_cost_now - fresh, 3))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            out = fn()
            print("ok", name, out if out else "")
