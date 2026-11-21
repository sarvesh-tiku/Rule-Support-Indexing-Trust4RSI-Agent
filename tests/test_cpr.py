import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cpr.agents import Agent, Belief, DEFAULTS, KINDS, run_episode
from cpr.experiment import CONDITIONS, make_episode
from cpr.planner import INF, Leg, Stats, astar, best_order, cost_array
from cpr.world import K, NOMINAL, OPEN, VALUES, World, gen_map, hash01


def tiny_world():
    # 5x5: a wall column at x=2 with one type-0 cell at (2,2) as the only gap besides row 4.
    W = 5
    grid = [OPEN] * 25
    for y in range(4):
        grid[y * W + 2] = -2
    grid[2 * W + 2] = 0
    return World(W, grid, 0, [4], 24, seed=1)


def test_astar_matches_brute_force_cost():
    w = gen_map(9, 3)
    arr = cost_array(w, [1 / 0.9, 1 / 0.9, 1 / 0.3, 9.0, 9.0], ())
    # Bellman-Ford style relaxation as an independent check.
    a, b = w.start, w.tower
    dist = {a: 0.0}
    for _ in range(81):
        for u in list(dist):
            x, y = u % 9, u // 9
            for vx, vy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= vx < 9 and 0 <= vy < 9 and arr[vy * 9 + vx] < INF:
                    v = vy * 9 + vx
                    if dist[u] + arr[v] < dist.get(v, INF) - 1e-12:
                        dist[v] = dist[u] + arr[v]
    cost, path = astar(9, arr, a, b, Stats())
    assert abs(cost - dist[b]) < 1e-9
    assert path[-1] == b and abs(sum(arr[v] for v in path) - cost) < 1e-9


def test_leg_supports():
    w = tiny_world()
    arr = cost_array(w, [1.1, 5, 5, 5, 5], ())
    cost, path = astar(5, arr, 0, 4, Stats())
    leg = Leg(w, 0, 4, cost, path, set())
    assert 12 in leg.cells and leg.val == frozenset({0})
    assert leg.affected([("up", 0)]) and leg.affected([("down", 0)]) and leg.affected([("patch", 12)])
    assert not leg.affected([("up", 1)])
    # Make type 0 expensive: the leg goes around through row 4 and type 0 becomes a blocking rule.
    arr = cost_array(w, [50.0, 5, 5, 5, 5], ())
    cost, path = astar(5, arr, 0, 4, Stats())
    leg = Leg(w, 0, 4, cost, path, set())
    assert leg.val == frozenset() and 0 in leg.blk
    assert leg.affected([("down", 0)]) and not leg.affected([("up", 0)])
    assert leg.oriented(4)[-1] == 0 and len(leg.oriented(4)) == len(path)


def test_belief_update_and_cost():
    b = Belief(DEFAULTS, 15)
    assert abs(sum(b.b[0]) - 1) < 1e-12 and b.b[0][0] == 0.7 and b.b[3][2] == 0.7
    b.update(0, True)
    assert b.b[0][2] == 0.0                      # one success rules out "blocked"
    c0 = b.cost(1)
    b.update(1, False)
    assert b.cost(1) > c0                        # a failure makes the rule look costlier
    for _ in range(12):
        b.update(1, False)
    assert b.cost(1) == INF                      # enough failures confirm "blocked"
    assert abs(sum(b.posterior(2, False)) - 1) < 1e-12


def test_best_order_is_exhaustive():
    first = {1: 5.0, 2: 1.0, 3: 4.0}
    fixed = {(1, 2): 1.0, (1, 3): 1.0, (2, 3): 6.0, (1, 9): 7.0, (2, 9): 2.0, (3, 9): 1.0}
    order, cost = best_order(first, fixed, {1, 2, 3}, 9)
    brute = min(first[p[0]] + fixed[tuple(sorted(p[:2]))] + fixed[tuple(sorted(p[1:]))] + fixed[(p[2], 9)]
                for p in itertools.permutations([1, 2, 3]))
    assert abs(cost - brute) < 1e-12 and order == [2, 1, 3]


def test_attempts_use_common_random_numbers():
    w = gen_map(15, 5)
    cell = w.type_cells[0][0]
    a, b = w.clone(), w.clone()
    assert [a.attempt(cell) for _ in range(20)] == [b.attempt(cell) for _ in range(20)]
    assert 0 <= hash01(1, 2, 3) < 1


def test_repair_matches_full_replanning_and_never_misses_a_changed_leg():
    total = dict(flagged=0, changed=0, hit=0, missed=0, legs=0, repairs=0, mismatch=0)
    for seed in range(40):
        for cond in ("block", "slow", "unlock", "ool", "none"):
            ep = make_episode(15, seed, cond)
            if ep is None:
                continue
            for kind in ("repair", "repair_probe"):
                diag = dict.fromkeys(total, 0)
                row = run_episode(kind, ep[0].clone(), diag=diag)
                assert row["completed"]
                for key in total:
                    total[key] += diag[key]
    assert total["repairs"] > 100
    assert total["mismatch"] == 0      # repaired plan costs exactly what a fresh plan costs
    assert total["missed"] == 0        # every leg whose cost changed was invalidated


def test_every_agent_completes_every_condition():
    for seed in range(6):
        for cond in CONDITIONS:
            ep = make_episode(15, seed, cond)
            if ep is None:
                continue
            for kind in KINDS:
                assert run_episode(kind, ep[0].clone())["completed"], (seed, cond, kind)


def test_irrelevant_violation_is_outside_the_plan_support():
    from cpr.agents import nominal_plan_legs
    seen = 0
    for seed in range(30):
        ep = make_episode(15, seed, "irrelevant")
        if ep is None:
            continue
        world, meta = ep
        seen += 1
        for leg in nominal_plan_legs(gen_map(15, seed)):
            assert meta["type"] not in leg.val and meta["type"] not in leg.blk
    assert seen > 0


def test_oracle_never_attempts_a_blocked_cell():
    ep = make_episode(15, 2, "block")
    world = ep[0].clone()
    ag = Agent("oracle", world)
    ag.start()
    while not ag.done:
        ag.step()
    assert all(world.true_p(c) > 0 for c in world.counts)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
