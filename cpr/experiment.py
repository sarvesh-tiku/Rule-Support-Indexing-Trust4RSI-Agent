"""Builds episodes with injected rule violations and runs every agent on each.

Usage:  python3 -m cpr.experiment --sizes 15 31 --seeds 1000 1200 --out results/final.jsonl
"""
import argparse
import hashlib
import json
import os
import sys
import time
from multiprocessing import Pool

from .agents import DEFAULTS, KINDS, nominal_plan_legs, run_episode
from .world import K, NOMINAL, gen_map

CONDITIONS = ("none", "block", "slow", "unlock", "irrelevant", "ool")


def make_episode(W, seed, condition, P=None):
    """Returns (world, meta) or None when the map offers no rule that fits the condition.
    Conditions are defined against the plan a belief-revising agent starts with."""
    world = gen_map(W, seed)
    legs = nominal_plan_legs(world, P)
    first_val, first_any = {}, {}
    for i, leg in enumerate(legs):
        for k in leg.val:
            first_val.setdefault(k, i)
            first_any.setdefault(k, i)
        for k in leg.blk:
            first_any.setdefault(k, i)
    meta = dict(type=None, first_leg=None, n_legs=len(legs))
    if condition == "none":
        return world, meta
    if condition in ("block", "slow", "ool"):
        cands = sorted((i, k) for k, i in first_val.items() if NOMINAL[k] == 0.9)
        if not cands:
            return None
        i, k = cands[0]
        if condition == "block":
            world.p_true[k] = 0.0
        elif condition == "slow":
            world.p_true[k] = 0.3
        else:
            world.ool = (k, W // 2)
    elif condition == "unlock":
        cands = sorted((i, k) for k, i in first_any.items() if NOMINAL[k] == 0.0)
        if not cands:
            return None
        i, k = cands[0]
        world.p_true[k] = 0.9
    elif condition == "irrelevant":
        cands = [k for k in range(K) if k not in first_any and world.type_cells[k]]
        if not cands:
            return None
        i, k = None, cands[0]
        world.p_true[k] = 0.9 if NOMINAL[k] == 0.0 else 0.0
    else:
        raise ValueError(condition)
    meta.update(type=k, first_leg=i)
    return world, meta


def run_task(task):
    W, seed, condition, kinds, P = task
    ep = make_episode(W, seed, condition, P)
    if ep is None:
        return [dict(W=W, seed=seed, condition=condition, skipped=True)]
    world, meta = ep
    rows = []
    for kind in kinds:
        t0 = time.perf_counter()
        row = run_episode(kind, world.clone(), P)
        row.update(W=W, seed=seed, condition=condition, wall=round(time.perf_counter() - t0, 4), **meta)
        rows.append(row)
    return rows


def source_hash():
    h = hashlib.sha256()
    here = os.path.dirname(os.path.abspath(__file__))
    for name in sorted(os.listdir(here)):
        if name.endswith(".py"):
            with open(os.path.join(here, name), "rb") as f:
                h.update(name.encode() + b"\0" + f.read())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[15, 31])
    ap.add_argument("--seeds", type=int, nargs=2, default=[0, 30], help="first and one-past-last map seed")
    ap.add_argument("--conditions", nargs="+", default=list(CONDITIONS))
    ap.add_argument("--agents", nargs="+", default=list(KINDS))
    ap.add_argument("--param", nargs="*", default=[], help="overrides such as strength=0.9")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    P = dict(DEFAULTS)
    for item in args.param:
        key, value = item.split("=")
        P[key] = type(DEFAULTS[key])(value)
    tasks = [(W, s, c, args.agents, P) for W in args.sizes for s in range(*args.seeds) for c in args.conditions]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    header = dict(header=True, params=P, sizes=args.sizes, seeds=args.seeds, conditions=args.conditions,
                  agents=args.agents, source_sha256=source_hash(), python=sys.version.split()[0])
    t0, n = time.time(), 0
    with open(args.out, "w") as f, Pool(args.workers) as pool:
        f.write(json.dumps(header) + "\n")
        for rows in pool.imap_unordered(run_task, tasks, chunksize=2):
            for row in rows:
                f.write(json.dumps(row) + "\n")
            n += 1
            if n % 200 == 0:
                print(f"{n}/{len(tasks)} tasks, {time.time() - t0:.0f}s", flush=True)
    print(f"done: {len(tasks)} tasks in {time.time() - t0:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
