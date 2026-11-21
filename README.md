# Rule-support indexing for exact plan repair under model revision

Code, tests, raw results and paper source for *Recomputing Only What Depended on It:
Rule-Support Indexing for Exact Plan Repair Under Model Revision*.

An agent plans a route through waypoints under uncertain rules about which obstacles can be
crossed. When it revises a rule, it normally has to rebuild its whole plan. This repository
studies what the planner must record so that it can recompute only the cached pieces that
depended on the revised rule and still get a plan of exactly the same cost.

Each cached leg (a shortest path between two waypoints) stores two sets of rules:

- **direct support**: the rules its path uses;
- **alternative support**: rules it avoids that could make a different path cheaper if they improved.

A leg is recomputed only if a revised rule is in one of its sets.

## Results at a glance

All numbers are produced by the commands below and stored in `results/`.

| Question | Result | File |
|---|---|---|
| Is indexed repair exact? | 0 mismatches against from-scratch plans in 17,170 repairs; 0 counterexamples in 15.7 million exhaustive small-board revisions | `final_diag.json`, `counterexample_search.json` |
| How much search does it save over full replanning? | 0.56 / 0.66 / 0.67 of the node expansions at 15×15 / 31×31 / 51×51 | `final_summary.json` |
| And time? | 0.65 / 0.70 / 0.69 of a replanner that builds no index | `timing.json` |
| Is tracking direct support alone enough? | No: a non-optimal plan after 2.5% / 11.5% / 20.2% of repairs | `valonly.json` |
| How does it compare with incremental search (LPA*)? | LPA* saves more search (0.15 / 0.27 / 0.30 of A* on every leg, against 0.31 / 0.47 / 0.48 for the index). The index removes a further 11–18% on top of LPA*. In this Python implementation LPA* is slower in wall-clock time | `incremental.json` |
| Can belief revision make the agent unreliable? | Yes: revising agents abandoned a reachable goal in 19 of 1,800 episodes on game-derived layouts and 42 of 5,275 on fresh maps, by treating a 95% belief as certain | `abandonment.json`, `safeguard_validation.json` |
| Does staging such commits help? | 0 abandonments in both sets; recognising a truly unreachable goal takes about twice as many actions (97 vs 46) | `safeguard_validation.json` |

The guarantee is equal plan cost under the agent's committed model. It is **not** rollback (no
earlier model is restored), not a claim about general hierarchical planning, and not a claim
that plans which are optimal under the model lead to reliable behaviour. See *Scope* below.

## Quick start

Python 3.10+ with numpy, scipy and matplotlib.

```
pip install -r requirements.txt
make test          # 15 tests, about a minute
make smoke         # a small end-to-end run of the main experiment and analysis
```

## Reproducing the paper

Everything is deterministic given the seeds, except wall-clock timings. Each results file
records a SHA-256 of `cpr/*.py`; the reported runs used `0560a1c8…`.

| Step | Command | Output |
|---|---|---|
| Main experiment (300 held-out maps × 3 sizes, about 9 min on 8 cores) | `python3 -m cpr.experiment --sizes 15 31 51 --seeds 1000 1300 --out results/final.jsonl` | `results/final.jsonl` |
| Pre-registered analysis | `python3 -m cpr.analyze results/final.jsonl --out results/final` | `final_summary.json`, `final_report.md` |
| Index against ground truth | `python3 -m cpr.diagnose --sizes 15 31 51 --seeds 1000 1300 --out results/final_diag.json` | `final_diag.json` |
| ε audit and exhaustive counterexample search | `python3 scripts/counterexample_search.py` | `counterexample_search.json` |
| Direct-support-only baseline | `python3 scripts/valonly_baseline.py` | `valonly.json` |
| Incremental search (LPA*), with and without the index | `python3 scripts/incremental_baseline.py` | `incremental.json` |
| Wall-clock time by phase | `python3 scripts/timing.py` | `timing.json` |
| Index size and peak memory | `python3 scripts/memory.py` | `memory.json` |
| Game-derived layouts | `python3 scripts/game_levels.py` | `game_levels.json` |
| Abandoned goals: traces and safeguard | `python3 scripts/abandonment_traces.py`; `python3 scripts/abandonment.py` | `abandonment_traces.json`, `abandonment.json` |
| Safeguard on fresh maps | `python3 scripts/safeguard_validation.py` | `safeguard_validation.json` |
| Map-level bootstrap | `python3 scripts/audit_stats.py results/final.jsonl results/audit_stats.json` | `audit_stats.json` |
| Tables and Figure 1 | `make tables figure` | `paper/table_primary.tex`, `paper/fig_game_walkthrough.pdf` |
| Paper | `make paper` | `paper/main.pdf` |

`make all-posthoc` runs every post-hoc script in turn.

## What was planned in advance and what was not

`PREREG.md` was written after a pilot on development maps (seeds 0–29) and before any run on
the final maps (seeds 1000–1299). It fixes the comparisons, the statistics and our predictions.

- **Pre-registered:** the main experiment and its analysis.
- **Disclosed deviation:** the first final run exposed a bug in the posterior-sampling baseline.
  It was fixed and the run repeated; every other agent's rows are identical. The first run is
  kept as `results/final_v1_psrl_bug.jsonl.gz`.
- **Post hoc** (marked † in the paper): everything under `scripts/`.
- **Safeguard:** designed on the 19 failures in `abandonment.json`, then run unchanged on new
  maps in `safeguard_validation.json`. Only the second is independent evidence.

## Layout

```
cpr/        simulator, planner with the support index, agents, experiment runner, analysis
tests/      unit tests and planner-level property tests
scripts/    post-hoc experiments, tables and figure
results/    raw rows (.jsonl), summaries and reports
paper/      LaTeX source, bibliography, generated tables and figure
docs/       AUDIT.md: proof audit, novelty comparison, and the reasoning behind each post-hoc run
PREREG.md   analysis plan frozen before the final run
```

Start with `cpr/planner.py` (`Leg` holds the two support sets and `affected` is the
invalidation test) and `cpr/agents.py` (`scoped_repair`).

## Scope and known limits

- Two-level routing on four-connected grids. Nothing here is shown for deeper task hierarchies.
- The alternative support uses a Manhattan-distance bound, which over-approximates: 15–34% of
  legs are invalidated where 10–19% really change.
- The exactness result needs every obstacle cell to cost at least 1 + ε under every committed
  model (ε = 1/0.9 − 1 here). `tests/test_index_properties.py` contains the counterexample
  that arises without it.
- The LPA* comparison covers the leg table only and one unoptimised implementation.
- `Agent.step` assumes the next waypoint is reachable when the episode starts; maps that
  violate this are filtered out by the scripts that can generate them.

## Third-party material

`scripts/game_levels.py` contains four level layouts transcribed from the game Dice Adventure,
and `paper/game_shot.png` is a screenshot of that game. They are included to make one experiment
and one figure reproducible and are not covered by this repository's licence. Check that you are
entitled to redistribute them before making the repository public.

## Licence

MIT for the code in this repository; see `LICENSE`.
