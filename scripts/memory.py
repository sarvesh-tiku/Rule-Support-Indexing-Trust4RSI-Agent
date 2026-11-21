"""Size of the rule-support index next to the cached legs it annotates, and peak memory of an episode.

Usage:  python3 scripts/memory.py --out results/memory.json
"""
import argparse
import json
import os
import sys
import tracemalloc

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from cpr.agents import Agent
from cpr.experiment import make_episode, source_hash

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[15, 31, 51])
    ap.add_argument("--seeds", type=int, nargs=2, default=[1000, 1100])
    ap.add_argument("--out", default="results/memory.json")
    a = ap.parse_args()
    out = dict(source_sha256=source_hash(), seeds=a.seeds, by_size={})
    for W in a.sizes:
        legs = support = cells = n = 0
        peaks = {"replan": [], "repair": []}
        for seed in range(*a.seeds):
            ep = make_episode(W, seed, "block")
            if ep is None:
                continue
            n += 1
            ag = Agent("repair", ep[0].clone())
            ag.start()
            for leg in ag.table.values():
                legs += 1
                support += len(leg.val) + len(leg.blk)
                cells += len(leg.path)
            for kind in peaks:
                tracemalloc.start()
                x = Agent(kind, ep[0].clone())
                x.start()
                while not x.done and x.actions < 30 * W * W:
                    x.step()
                peaks[kind].append(tracemalloc.get_traced_memory()[1])
                tracemalloc.stop()
        out["by_size"][W] = dict(maps=n, cached_legs_per_map=round(legs / n, 1),
                                 support_entries_per_leg=round(support / legs, 2),
                                 path_cells_per_leg=round(cells / legs, 1),
                                 support_share_of_stored_ids=round(support / (support + cells), 3),
                                 peak_kib_replan=round(sum(peaks["replan"]) / n / 1024, 1),
                                 peak_kib_repair=round(sum(peaks["repair"]) / n / 1024, 1))
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out["by_size"], indent=1))
