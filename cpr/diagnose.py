"""Ground-truth check of the support index (evaluation only, never used by an agent).

For every repair it compares the legs the index invalidated with the legs whose optimal cost
really changed, and the repaired plan's cost with a plan built from scratch.

Usage:  python3 -m cpr.diagnose --sizes 15 31 51 --seeds 1000 1300 --out results/final_diag.json
"""
import argparse
import json
from multiprocessing import Pool

from .agents import run_episode
from .experiment import CONDITIONS, make_episode

KEYS = ("flagged", "changed", "hit", "missed", "legs", "repairs", "mismatch")


def one(task):
    W, seed, cond = task
    ep = make_episode(W, seed, cond)
    diag = dict.fromkeys(KEYS, 0)
    if ep is not None:
        run_episode("repair", ep[0].clone(), diag=diag)
    return W, diag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[15, 31, 51])
    ap.add_argument("--seeds", type=int, nargs=2, default=[0, 30])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    tasks = [(W, s, c) for W in args.sizes for s in range(*args.seeds) for c in CONDITIONS]
    total = {W: dict.fromkeys(KEYS, 0) for W in args.sizes}
    with Pool(8) as pool:
        for W, diag in pool.imap_unordered(one, tasks, chunksize=4):
            for k in KEYS:
                total[W][k] += diag[k]
    for W, d in total.items():
        d["recall"] = d["hit"] / d["changed"] if d["changed"] else None
        d["precision"] = d["hit"] / d["flagged"] if d["flagged"] else None
        d["flagged_fraction"] = d["flagged"] / d["legs"] if d["legs"] else None
        d["changed_fraction"] = d["changed"] / d["legs"] if d["legs"] else None
    with open(args.out, "w") as f:
        json.dump(total, f, indent=1)
    print(json.dumps(total, indent=1))


if __name__ == "__main__":
    main()
