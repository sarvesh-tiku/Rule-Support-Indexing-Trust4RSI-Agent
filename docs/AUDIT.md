# Strengthening report: rule-support indexing paper (Trust4RSI-Agent, AAAI-27)

Written 2026-11-20. Everything numerical below was produced tonight by code in this folder
or read from `results/`. Nothing is estimated. All new runs are post hoc (not in `PREREG.md`).
Source hash of `cpr/` is unchanged: `0560a1c8…`.

## The five changes with the highest expected impact

1. **Stop calling it rollback.** The system does dependency-directed invalidation and exact
   repair. It has no version log and never restores a belief. Change the title and framing (D1, D5).
2. **Add the direct-support-only baseline.** It is the baseline a planning reviewer will ask for,
   and it shows the optimality support (`blk`) is what makes repair exact (D4, result R1).
3. **Report the abandonment failure with its root cause and the safeguard.** This is the result
   most relevant to the workshop, and it is now explained and tested both ways (R2).
4. **State the proposition's real assumptions** and what it does not cover (D3). One clause was
   wrong as written; it is fixed in `paper/main.tex`.
5. **Position against incremental search (LPA*, D* Lite) honestly.** Not compared; say so and say
   why the two are complementary (D2).

---

## D1. Critical audit

### Ten most serious weaknesses

| # | Weakness | Status |
|---|---|---|
| 1 | Title and intro say "rolling back"; the code invalidates caches. No version history, no restore of a prior model, no undo of a belief update. | Open. Retitle. |
| 2 | Proposition 1 assumed "every cell costs at least 1". That is not enough: the bound needs obstacle cells to cost at least 1+ε under every committed model. | Fixed in the statement. Counterexample in tests. |
| 3 | No baseline between "replan everything" and "full index". | Closed by R1. |
| 4 | No incremental-search baseline (LPA*, D* Lite). | Open. Disclose. |
| 5 | The 19 abandoned goals were reported without a cause. | Closed by R2. |
| 6 | Pooled intervals resample episodes, but one map gives up to three episodes. | Checked (R3): intervals widen slightly, no conclusion changes. Disclose or swap. |
| 7 | Only node expansions reported; no time. | Partly closed (R3): whole-episode wall time recorded in the run. |
| 8 | The proposition guarantees equal plan *cost* under the committed model. "Identical actions" is an empirical observation, not a consequence. The paper should keep these apart. | Open (wording). |
| 9 | Per-cell exceptions and their retraction sit outside the proposition. | Open (one sentence). |
| 10 | Two-level routing on a grid; no HTN benchmark, no SHOPFixer or IPyHOPPER run. | Open. Already in Limitations. |

### Five strongest existing contributions

1. The two-sided support (`val` and `blk`) with a proof, checked in 17,170 in-agent repairs and now
   in 1,500 arbitrary revisions at the planner level.
2. A pre-registered, held-out evaluation with paired outcomes and a disclosed baseline bug.
3. Negative results reported as findings: probing loses once computation is priced, probing hurts
   outside the hypothesis space, not revising wins when nothing is wrong.
4. The game-level check, which broke a generator assumption and exposed the abandonment failure.
5. Index precision measured against ground truth (15–34% flagged, 10–19% really changed).

### Claim-to-evidence matrix

| Claim in the paper | Evidence | Verdict |
|---|---|---|
| Repaired plan cost equals from-scratch cost | Proposition 1; `results/final_diag.json` (17,170 repairs, 0 mismatches, 0 missed); `tests/test_index_properties.py` (0 stale legs in 31,500 checks) | Supported, under the stated cost floor |
| Repair does 0.56 / 0.66 / 0.67 of the replanning work | `results/final_summary.json` | Supported (node expansions). Wall time ratio is 0.75–0.77, see R3 |
| Identical actions to replanning in every episode | `final.jsonl`, 2,081 violation episodes; 1,800 game episodes | Supported empirically; not implied by the proposition |
| Probing saves 2–3% of actions | Table 1 | Supported at prior 0.7; shrinks at 0.9 (already disclosed) |
| Probing costs 24–34× the planning work | `final_summary.json` | Supported |
| "Rolling back" | none | **Not supported. Remove or narrow.** |
| "We did not find a system that links plan structure to revisable rule hypotheses" | two literature passes | Keep the hedge. Add LPA*/D* Lite as the closest computational relatives |
| 19 of 1,800 game episodes abandoned a reachable goal | `results/game_levels.json`, reproduced in `results/abandonment.json` | Supported; cause now known |

### Possible correctness bugs looked for

- ε lower bound: sound in the implementation (minimum obstacle cost is 1/0.9). Unsound if a rule could cost less than 1+ε; counterexample pinned in a test.
- Mid-leg reuse of the current path after a "cheaper" event: checked by hand. The `blk` test on the
  original endpoints implies the test for the suffix, because the walked prefix costs at least its Manhattan length.
- Reversal of an earlier commit: handled as an ordinary commit; 372 reversals tested, 0 stale legs.
- The `IndexError` when a waypoint is unreachable from the start: `Agent.step` reads `path[0]` on an
  empty path. It cannot occur on generated maps (open connectivity is guaranteed) and the game runs
  exclude unsolvable configurations, but it is a real crash path. Not fixed, because `cpr/` is hash-frozen.

---

## D2. Novelty matrix

Citations marked ✔ were opened earlier today or verified tonight; "listing" means confirmed only
from an index page (see `paper/refs.bib`).

| Method | Uncertainty | Model can change | Tracks rule dependencies | Tracks unused alternatives | Selective recomputation | Undo of a wrong update | Guarantee | Distinction from this paper |
|---|---|---|---|---|---|---|---|---|
| Doyle 1979, TMS (listing) | beliefs | yes | justifications | no | yes | yes (retraction) | consistency | General mechanism; no optimality notion |
| Nebel & Koehler 1995 ✔ | none | no | – | – | – | – | reuse is not easier than planning | Bounds what any repair can promise |
| Fritz & McIlraith 2007 (listing) | state | no | conditions for continued optimality | **yes** | monitors, then replans | no | optimality conditions | Closest idea to `blk`; over state under a fixed model |
| RepairSHOP / Warfield et al. 2007 ✔ | state | no | task-node dependencies | no | yes | no | – | Dependencies on state conditions |
| HOTRiDE 2007 ✔ | action failure | no | task dependencies | no | yes | no | – | Same |
| SHOPFixer 2020 ✔ | state | no | causal links | no | minimal subtree | no | stability | Same; fixed domain model |
| Zaidins et al. 2025 ✔ | state | no | – | – | compares methods | no | formal comparison | Assumes model fixed |
| LPA* (Koenig, Likhachev, Furcy 2004) ✔ | edge costs | yes (edge costs) | per-vertex consistency | **yes, implicitly** (inconsistent vertices) | yes, within one search | n/a | optimal path | **Strongest threat.** Reuses within a single shortest-path search for any edge change |
| D* Lite (Koenig & Likhachev 2002) ✔ | edge costs | yes | same | yes | yes | n/a | optimal path | Same, for a moving agent |
| Ramalingam & Reps 1996 ✔ | edge changes | yes | affected vertices | yes | yes | n/a | optimal distances | Dynamic shortest paths in general |
| Dearden et al. 1999 ✔ | model | learned | no | no | no | no | – | Source of the probing rule |
| Weber & Bryce 2011 (listing) | incomplete actions | learned | no | no | replans | no | – | Replans after learning |
| HYDRA / Mohan et al. 2024 ✔ | novelty | repaired | no | no | replans | no | – | Replans after repair |
| Karia et al. 2024 ✔ | non-stationary | relearned | no | no | replans | no | – | Replans |
| WorldCoder 2024 ✔ | program model | rewritten | no | no | replans | no | – | Replans |
| ALAS 2025 ✔ | disruptions | no | dependency graph | no | local compensation | compensation | – | LLM agents; no optimality statement |
| ChronoMem 2026 ✔ | memory | versioned | no | no | no | **yes (snapshots)** | – | Real rollback, in time, not along dependencies |
| EvoCF 2026 ✔ | failures | constraints | no | no | no | no | – | Counterfactual plan generation |
| **This paper** | rule values | yes, committed | **yes, per cached leg** | **yes (`blk`)** | yes, across legs | reversal of a commit is repaired exactly; beliefs are not restored | equal plan cost under the committed model | – |

**Three strongest threats to the novelty claim**

1. **LPA* / D* Lite.** They already repair a shortest path after arbitrary edge-cost changes, including
   decreases. They would handle every revision here. What the index adds is a different layer: it
   decides *which cached legs need any search at all* from a rule-level summary, without touching the
   graph, and it answers "would the plan change if rule k were otherwise" for many k cheaply. The two
   compose (run LPA* inside an invalidated leg). The paper has not measured this and must say so.
2. **Fritz & McIlraith 2007.** Monitoring conditions under which a plan stays optimal is the same idea
   as `blk`. The difference is the object (rule hypotheses of a revisable model, not state) and the
   cheap geometric certificate. This is a specialization, and should be described as one.
3. **Truth maintenance.** `val` is a justification set. Only `blk` goes beyond textbook TMS, and only
   because the property being maintained is optimality, not validity.

**Honest statement of novelty:** an optimality-preserving support set at the level of revisable rule
hypotheses, with a proof and a measurement of how loose it is. Not a new repair paradigm.

Answers to the Part III questions: (1) `blk` is a specialization of optimality monitoring, not new in
kind. (2) Yes, it differs from causal-link repair, which preserves validity, not optimality. (3) and (4)
It generalizes to any graph where an admissible lower bound through a rule's cells is available:
replace Manhattan distance by any admissible heuristic h(a,x)+h(x,b). This is argued, not proved or
tested. (5) Per leg: cost, used rules, and for each unused rule the minimum of the bound over its cells.
(6) Index cost is one pass over obstacle cells per leg; in wall time repair still wins (R3). (7) It loses
its advantage when most legs list the revised rule: 15% of legs flagged at 15×15, 34% at 51×51.
(8) See D3.

---

## D3. Formal correctness report

**Corrected statement (now in `main.tex`).** Assume that under every committed model an open cell
costs 1 to enter and an obstacle cell at least 1+ε, and that the table holds optimal legs under the
committed model. After a commit that changes one rule's cost, recomputing only the invalidated legs
and re-solving the ordering gives a plan whose cost equals that of a plan computed from scratch.

**Proof audit.**
- Costlier, k ∉ val: stored path cost unchanged, no path got cheaper. Sound.
- Cheaper: an improving path enters a cell x of type k, has at least d(a,x)+d(x,b) cells of cost ≥ 1,
  and x costs ≥ 1+ε, so its cost is ≥ d(a,x)+d(x,b)+ε. For it to beat C it must satisfy the `blk` test.
  Sound **only with the cost floor on obstacle cells**. In the code the floor holds because the cheapest
  rule value is success 0.9, cost 1/0.9.
- Current leg mid-execution: the suffix of an optimal path is optimal, and the `blk` test on (a,b,C)
  implies the test on (pos,b,C′). Sound.
- Several events in one step (a rule change plus a cell exception) are handled as a union. Sound,
  by applying the argument once per event; the statement says "one rule" and should say "one or more".

**Missing assumptions to state.** (i) the obstacle cost floor; (ii) four-connected grid and Manhattan d;
(iii) commits are atomic: a plan is never used between a commit and its repair (true in the code, where
repair runs inside the same step); (iv) the ordering is solved exactly; (v) rule costs are the only thing
that changes besides cell exceptions.

**What the proposition does not say.**
- *Ties.* An unindexed alternative can become equally cheap. Cost is preserved; the path need not be.
  Identical actions in the experiments are an observation.
- *Stochastic rules.* The guarantee is optimality under the committed expected-cost surrogate. It says
  nothing about expected actions in the real environment or about success probability.
- *Per-cell exceptions.* An exception invalidates legs that pass through the cell, which is sound
  (it only raises costs). Retraction triggers a full replan, so it is outside the proposition.
- *Generality.* Proved: 4-connected grids, per-type entry costs. Conjectured: weighted graphs with an
  admissible heuristic. Not addressed: task DAGs, multi-level HTNs, resources, irreversible actions.

**Counterexample (assumption is necessary).** 2×2 grid, from (0,0) to (1,1), one route through a
type-0 cell and one through a type-1 cell. With costs 1+ε and 5 the leg uses type 0 and type 1 is not in
`blk`, correctly: at cost ≥ 1+ε it can only tie. Drop type 1 to cost 1.0 and the other route is strictly
better, and the index misses it.

**Tests** (`tests/test_index_properties.py`, all pass):

| Test | Result |
|---|---|
| 60 random maps, 1,500 random revisions incl. 372 reversals, full index | 0 stale legs in 31,500 leg checks; 6,197 legs recomputed (20%) |
| Same sequences, direct support only | 1,245 stale legs; 361 of 1,500 revisions (24%) left a stale leg |
| Tie case | not invalidated, and correct |
| Cost floor violated | 1 stale leg (the counterexample) |

---

## D4. Experiments run tonight, and what remains

### R1. Direct-support-only repair (`scripts/valonly_baseline.py`, `results/valonly.json`)

Same held-out maps and outcome draws as the main run, all conditions. The baseline invalidates a leg
only when a rule it uses changes.

| Board | Episodes | Repairs | Repairs leaving a non-optimal plan | Episodes with one | Episodes whose actions differ | Mean extra actions | Max | Work vs. full index |
|---|---|---|---|---|---|---|---|---|
| 15×15 | 1,227 | 4,052 | 101 (2.5%) | 71 (5.8%) | 71 | 0.04 | 9 | 0.84 |
| 31×31 | 1,306 | 6,190 | 710 (11.5%) | 282 (21.6%) | 233 | 0.22 | 49 | 0.74 |
| 51×51 | 1,244 | 6,476 | 1,305 (20.2%) | 395 (31.8%) | 328 | 0.95 | 51 | 0.71 |

Reading: tracking only used rules is cheaper and is wrong often, increasingly with board size. The
average cost of being wrong is small (under one action); the worst case is not (49–51 actions). So `blk`
buys exactness, and a modest amount of behaviour. Do not claim it buys a large action saving.

### R2. Abandoned reachable goals (`scripts/abandonment.py`, `results/abandonment.json`)

**Root cause, all 19 episodes** (traces in `results/abandonment_traces.json`). An obstacle whose true
success rate is 0.3 guarded the only way to a waypoint and never once let the agent through. In 10
episodes it was a kind the agent assumed slow, and 13 failures with no success were needed (0.7^13 =
0.97% each time such a crossing is forced). In 9 it was a kind assumed free that the injected violation
had made slow, and 9 failures sufficed (0.7^9 = 4.0%). The failures need not be consecutive in time:
the agent tried other routes in between. (An earlier version of this paragraph said 13 in all 19; that
was wrong.) The
posterior on "blocked" passed 0.95, the rule was committed at infinite cost, the plan cost became
infinite, and the agent stopped. In 18 of 19 the exception-retraction step had already fired once; it
cannot help, because the infinite cost is on the rule, not on a cell. The truth was inside the hypothesis
space. This is not a bug and not misspecification: it is a 95% belief being acted on as a certainty
when the action is to give up. Indexed repair and full replanning fail identically.

**Safeguard tested: staged commit.** A commit that would make the goal unreachable is not applied. The
rule keeps a finite cost from the same posterior and is marked contested; the agent gives up only when
every rule in the way passes a stricter threshold (0.999).

| Setting | Agent | Finished | Abandoned | Mean actions |
|---|---|---|---|---|
| Goal reachable (1,800 episodes) | indexed repair | 1,781 | 19 | 45.10 |
| | with staged commit | 1,800 | 0 | 45.52 |
| Goal truly unreachable (450 episodes) | indexed repair | 0 | 450 | 20.6 |
| | with staged commit | 0 | 450 | 37.0 |

- In the 1,781 episodes where no commit was staged, actions are identical to the unguarded agent.
- Staged repair and staged replanning take identical actions in all 2,250 episodes.
- On generated maps the safeguard cannot fire: every agent completed all 3,777 episodes, so the plan
  cost is never infinite there.
- **Cost:** when the goal really is unreachable the guarded agent wastes 16 more actions (79% more)
  before giving up. The safeguard does not make anything reachable; it moves the threshold for the one
  decision that cannot be undone.
- Not measured: the residual rate of wrongful abandonment at 0.999 (expected to be far below 1 in
  1,800; zero observed).

### R3. Statistics and time (`scripts/audit_stats.py`, `results/audit_stats.json`)

- **Sampling unit.** Resampling maps instead of episodes widens every pooled interval a little and
  changes no sign. Examples at 31×31: probing − no probing −3.12, [−4.03, −2.22] by episode,
  [−4.13, −2.17] by map; repair − replan work −1,970, [−2,216, −1,740] vs [−2,287, −1,676].
  Maps contributing to the pooled rows: 276, 295, 300.
- **Wall time** (whole episode, includes simulation and the shared initial plan; recorded during a
  parallel run, so treat as indicative): repair ÷ replan = 0.75, 0.77, 0.75, against 0.56, 0.66, 0.67
  in node expansions. Index upkeep does not cancel the saving. Indexed ÷ unindexed probing = 0.53, 0.68, 0.71.
- **Verified from the repository:** development seeds 0–29 and final seeds 1000–1299 are disjoint;
  outcomes are paired by a hash of (map, cell, attempt); the PSRL fix changed no other agent's rows;
  Holm is applied over the 21 pre-specified tests; exclusions are per condition and counted in
  `n_skipped`.

### Not done, and why

| Item | Priority | Reason |
|---|---|---|
| LPA* / D* Lite baseline | P1, not feasible tonight | A fair version needs per-leg incremental search state for 15–21 legs and careful testing. Disclose as the main missing baseline. |
| Tighter `blk` bound (true distances instead of Manhattan) | P2 | Would cut the over-approximation; needs a new proof and rerun. |
| SHOPFixer / IPyHOPPER / REWRITE | P2 | Different problem: they repair against changed state under a fixed model. Compare in words only. |
| Peak memory, per-phase timing | P2 | Not instrumented. |
| Version log with belief restore | P2 | Would make "rollback" true. Not implemented. |

---

## D5. Trustworthiness: what is guaranteed, measured, unsupported

| Property | Status | Evidence | Minimum change to claim it |
|---|---|---|---|
| Provenance | **Partial.** Each leg stores the rules it depends on, not a model version id. | code | Stamp each leg with a commit counter. |
| Safe invalidation | **Proved and tested.** No retained leg is non-optimal after a commit. | Proposition 1; 17,170 + 31,500 checks | none |
| Reproducibility | **Holds.** Deterministic given seed and parameters; source hash in every result file. | README | none |
| Recoverability | **Narrow.** Reversing one rule's commit, with later commits to other rules kept, is repaired exactly (372 reversals). Beliefs are never restored and there is no version log. | property test | Version log plus belief snapshots. |
| Auditable change | **Computable, not built in.** Trigger, rule, invalidated and kept legs, and new plan are all available at repair time and are what Figure 1 draws. The agent does not log them. | `scripts/make_walkthrough.py` | Emit the record on every repair. |
| Conservative failure | **Violated by default** (19 of 1,800), **fixed by staged commit at a measured cost**. | R2 | Put the safeguard in the agent. |

Six operations, kept apart: belief revision (implemented); model-version commits (implemented, no
history); derived-plan invalidation (implemented, proved); incremental repair (implemented, proved);
rollback of an erroneous update (only as "a reversing commit is repaired exactly"; no detection, no
restore); compensation for physical actions (not addressed, and never claimed).

---

## D6. Section-by-section revision guidance

You write the text; these are the changes and the evidence each needs.

**Title.** Drop "Rolling Back". Options: *Invalidating Only What Depended on It: Rule-Support
Indexing for Exact Plan Repair Under Model Revision*, or simply *Rule-Support Indexing for Exact Plan
Repair When a Planner's Rules Are Revised*. Reason: Criticism 1 is correct.

**Abstract.** Replace "roll back only the parts" with "invalidate only the parts". Add one clause for
R1 (direct-support tracking leaves a non-optimal plan after 2.5–20% of repairs) and one for R2
(a 95% belief acted on as certainty made agents abandon reachable goals in 1.1% of game-level
episodes; staging the commit removed all 19 at 16 extra actions when the goal was truly unreachable).
Cut the PSRL-bug sentence from the abstract to make room; it stays in Limitations.

**Introduction.** Say the workshop asks for rollback and that this paper supplies a prerequisite,
dependency records that make selective invalidation exact, not rollback itself. In the related-systems
paragraph add LPA* and D* Lite as the closest computational relatives.

**Mechanism.** Name the two supports "direct" and "alternative" if you like the terms; say alternative
support exists because the maintained property is optimality. After the proposition add two sentences:
it guarantees cost under the committed surrogate model, not the path and not real-world expected cost;
ties and cell-exception retraction are outside it. The statement itself is already corrected.

**Results.** Add R1 next to "Scoped repair is exact and cheaper" (three numbers per size). Replace the
last sentence of the game paragraph with the root cause and the safeguard table or two sentences.
To make room: shorten "Doubt has a price" and "Against our predictions", or drop Figure 2 (its content
is in Table 1 and the text) and use the space for a small R1/R2 table.

**Table 1.** Add a row "Direct support only: repairs leaving a non-optimal plan" (2.5%, 11.5%, 20.2%)
in the ground-truth block. Either switch pooled intervals to map-resampled values from
`results/audit_stats.json` or state the sampling unit in the caption.

**Figure 1.** It shows invalidation but not the direct/alternative distinction. Cheap improvement:
none tonight; say in the caption that kept legs are those listing the rule in neither support.
The screenshot is not necessary for the argument; keep it only if you want the motivation visible.

**Related work.** Add one sentence each for LPA*/D* Lite and dynamic shortest paths (Ramalingam &
Reps 1996). Describe `blk` as a specialization of Fritz & McIlraith's optimality monitoring.

**Limitations.** Add: no incremental-search baseline; time is whole-episode and indicative; R1, R2 and
the game check are post hoc; the safeguard was designed after seeing the 19 failures and tested on
the same episodes, so its 19→0 is a demonstration, not a held-out estimate.

Bibliography entries to add (verified tonight):
- Koenig, Likhachev, Furcy. Lifelong Planning A*. *Artificial Intelligence* 155(1–2):93–146, 2004.
- Koenig, Likhachev. D* Lite. *AAAI-02*, 476–483, 2002.
- Ramalingam, Reps. An Incremental Algorithm for a Generalization of the Shortest-Path Problem. *Journal of Algorithms* 21(2):267–305, 1996.

---

## D7. Reviewer simulation (of the paper *with* the changes above)

These are my estimates, not predictions of the real outcome.

**Reviewer A, formal planning. 6/10, confidence 4.**
Strengths: correct, clearly scoped proposition with a necessity counterexample; the direct-support
baseline; honest measurement of over-approximation. Weaknesses: no LPA*/D* Lite comparison; two-level
routing only; Manhattan certificate is loose. Recommendation: weak accept for a workshop.
Would reject if: the paper still implies generality to HTN repair. Most important fix: an incremental-search baseline.

**Reviewer B, trustworthy agent systems. 6.5/10, confidence 3.**
Strengths: the abandonment analysis and the two-sided safeguard result; a stated invariant for derived
state; negative results. Weaknesses: no real rollback or version log; provenance and audit are
computable but not implemented; safeguard tested on the episodes that motivated it. Recommendation:
accept if retitled. Would reject if: "rollback" stays in the title. Most important fix: a version log
with restore, tested.

**Reviewer C, empirical methodology. 7/10, confidence 4.**
Strengths: pre-registration with hash, held-out maps, disclosed bug and rerun; post hoc analyses
labelled; sampling-unit check. Weaknesses: home-built environment; wall time measured loosely; several
post hoc additions on a short paper. Recommendation: accept. Would reject if: post hoc results are
blended with pre-registered ones. Most important fix: clustered intervals in the main table.

**Synthesis.** Without the changes (title claiming rollback, no intermediate baseline, unexplained
abandonment) I would put it near 5.5–6. With them, about 6.5: a narrow, correct result plus a failure
analysis that fits the workshop. Position **A + C**, with B only as "what this would need". Submit.

---

## D8. Submission checklist

- [ ] Retitle; remove "roll back" wording from abstract and intro.
- [ ] Add R1 and R2 numbers; mark them post hoc.
- [ ] Add the three bibliography entries; re-check the four "listing only" entries.
- [ ] Caption or table: state the bootstrap sampling unit.
- [ ] Rewrite the prose yourself. The draft was machine-written; AAAI-27 allows judicious AI assistance
      with authors fully responsible, and your own plan was to author the text.
- [ ] Body ≤ 4 pages excluding references (currently exactly 4; every addition needs a cut).
- [ ] Anonymity: PDF metadata has no author (checked). The paper names Dice Adventure and "our earlier
      agent"; decide whether that could identify you.
- [ ] Supplement: anonymise paths in the code archive.
- [ ] Confirm on OpenReview that the portal is open. Deadline Nov 20 AoE (about 7 a.m. Eastern Nov 21).
      Not re-checked tonight.

## Files added tonight

- `tests/test_index_properties.py`
- `scripts/valonly_baseline.py`, `results/valonly.json`
- `scripts/abandonment.py`, `results/abandonment.json`
- `scripts/audit_stats.py`, `results/audit_stats.json`
- `paper/main_before_audit.tex` (copy before the one-clause proposition fix)

---

## Addendum (second pass, same night)

Added after the first version of this report. Files: `scripts/counterexample_search.py`,
`scripts/timing.py`, `scripts/abandonment_traces.py`, one more test in `tests/test_index_properties.py`.

**Epsilon** (`results/counterexample_search.json`). ε = 1/0.9 − 1 = 0.1111. Every way the code produces
a committed rule cost has minimum exactly 1.1111 or higher: the belief cost formula over a grid of the
belief simplex at board sizes 2 to 51, sampled rule sets, nominal costs, and 2,097 commits observed in
real episodes (minimum 1.1286). Exhaustive search on 3×3 boards: 15,739,200 leg revisions with the cost
floor respected, 0 index misses (direct-support-only misses: 943,728); with a cost of 1.0 allowed,
74,084 index misses out of 28,330,560.

**Timing** (`results/timing.json`; single process, Python 3.12.3, arm64, fastest of 3 runs per episode,
2,081 violation episodes). This supersedes the whole-episode figure in R3, which included the shared
initial plan and the simulation.

| Board | Expansions ratio | Time after initial plan, repair ÷ replan | vs. a replanner that does not build the index | Index build + lookup as share of repair's planning time | ms per repair: replan / repair |
|---|---|---|---|---|---|
| 15×15 | 0.560 | 0.564 | 0.653 | 11.1% | 0.35 / 0.19 |
| 31×31 | 0.662 | 0.635 | 0.702 | 6.3% | 1.70 / 1.06 |
| 51×51 | 0.665 | 0.643 | 0.691 | 4.4% | 4.88 / 3.11 |

The replanning agent in this code base also builds the support sets and never reads them, so the fair
comparison is the fourth column: 0.65–0.70. Index lookup is under 0.01 ms per episode. Peak memory was
not measured.

**Stale-plan demonstration** (`test_unused_rule_gets_cheaper_old_plan_feasible_but_suboptimal`). 5×5
board, wall with one type-0 gap. Rule 0 costs 50, the leg walks around (cost 12, does not use rule 0).
Rule 0 is revised to 1.111. The old path is still walkable at cost 12; the best path costs 8.111.
Direct-support tracking keeps the old leg; the index lists rule 0 in the alternative support and recomputes.

**Manuscript revision applied** (`paper/main.tex`; previous version kept as `paper/main_before_revision.tex`).
New title; abstract and introduction no longer claim rollback; direct and alternative support named;
proposition scope stated; direct-support-only baseline, timing and the abandonment analysis added to
Results and Table 1 (rows marked as post hoc); incremental search added to Related Work with three new
references; Figure 2 (regret chart) removed and the probing material condensed to make room. Body is
four pages.

---

## Third pass (same night): what was added and what it showed

| Item | Test | Result | File |
|---|---|---|---|
| Simultaneous revisions | 939 random commits (438 mixing increases and decreases, 289 with a cell exception), maps without the connectivity guarantee, checked by a Bellman-Ford oracle that shares no code with A* | 0 stale legs in 9,390 checks; 643 of those legs unreachable | `tests/test_index_properties.py` |
| Incremental search | Replay of the real revision sequences on the leg table: A* on all legs, index + A*, LPA* on all legs, LPA* on indexed legs; all four must agree on every leg cost | Expansions as a fraction of A* on all legs: index 0.31 / 0.47 / 0.48; LPA* 0.15 / 0.27 / 0.30; both 0.14 / 0.23 / 0.24. Index on top of LPA*: 11–18% fewer expansions, 22–27% less time. LPA* wall-clock 1.2–1.9× A* on all legs and about 5× slower to initialise (Python). 63,397 leg-cost checks agree | `results/incremental.json` |
| Safeguard on unseen maps | 1,750 new maps (seeds 20000–20599, sizes 11, 15, 21) that require obstacle crossings; safeguard unchanged | Reachable goal, 5,275 episodes: original abandons 42 (0.80%), safeguard 0, mean actions 64.8 → 65.4. Unreachable goal, 1,310 episodes: stops after 45.9 vs 96.5 actions. Never giving up: hits the action cap in all 1,310 | `results/safeguard_validation.json` |
| Memory | Index entries and tracemalloc peak | 2.2 / 3.5 / 4.0 support entries per leg against 12 / 30 / 55 path cells; peak memory equal for both agents (both build the same objects) | `results/memory.json` |
| Listing-only references | Four searches | Doyle 1979 (12(3):231–272), Fritz & McIlraith 2007 (pp. 144–151), Weber & Bryce 2011 (DOI 10.1609/icaps.v21i1.13463), Russell & Wefald 1991 (49:361–395) all confirmed | `paper/refs.bib` |

**Proof for simultaneous revisions.** Let a commit change a set S of rules, some up and some down, and
let ℓ be a leg with no rule of S in val(ℓ) and no cheapened rule of S in blk(ℓ). Its stored path uses no
rule of S, so its cost C is unchanged. Take any other path P. If P enters no cell of a cheapened rule,
every cell of P costs at least what it did, so cost(P) ≥ its old cost ≥ C. If P enters a cell x of a
cheapened rule k, then P has at least d(a,x)+d(x,b) cells of cost ≥ 1 and x costs ≥ 1+ε, so
cost(P) ≥ d(a,x)+d(x,b)+ε ≥ C because k ∉ blk(ℓ). Either way the stored path is still optimal. A cell
exception only raises a cost and invalidates the legs through that cell, so it is covered by the first case.

**What this changes in the paper's claims.** The index is not a substitute for incremental search:
LPA* alone does less search. The defensible claim is that a rule-level summary decides which cached
searches need to run at all, and that this composes with incremental search. The safeguard result is
now supported on independent maps, with a doubled cost of recognising real impossibility.

**Still unverified or not done.** A cost-sensitive abandonment rule; an optimised LPA* (the time
ranking could change); sensitivity to the commit threshold, waypoint count and obstacle density;
anything beyond two-level grid routing. The workshop page and portal were not re-checked in this pass.

---

# Fourth pass (2026-11-20): audit against the "Master Research Prompt"

No manuscript text was changed in this pass. New code is in `scripts/`; `cpr/` is unchanged (same hash).

## What was run

| Item | Command | Result | File |
|---|---|---|---|
| Proposition 1 on 4x4 and 5x5 grids, every pair of open cells, mixed commits and cell exceptions, Bellman-Ford oracle | `python3 scripts/small_grid_bruteforce.py --layouts 20000` | 0 stale legs in 10,034,509 checks (2,853,703 at 4x4; 7,180,806 at 5x5) over 236,770 commits, 116,999 of them mixing increases and decreases, 72,187 with a cell exception, 163,749 rule changes to or from infinite cost, 82,231 to exactly 1+eps. Direct support alone: 905,151 stale. | `results/small_grid_bruteforce.json` |
| Optimised LPA* (flat lists, shared neighbour table, inlined update), same expansions as the dictionary version by assertion | `python3 scripts/incremental_audit.py` | 2.8x faster than the first implementation at every size (time ratio 0.35-0.36). | `results/incremental_audit.json` |
| LPA* profile | `python3 scripts/incremental_audit.py --profile 31 --seeds 1000 1030` | Dictionary version: 6.6 s, 33.8M calls, dominated by the per-vertex update (generator + `min` + `dict.get`). Optimised: 1.1 s, 3.9M calls. | `results/lpa_profile.txt` |
| Safeguard intervals and threshold sweep on a third map set (seeds 30000-30599) | `python3 scripts/safeguard_audit.py` | see below | `results/safeguard_audit.json` |
| Tests | `python3 -m pytest -q tests` | 15 passed | |

## Leg-table maintenance, ratio to A* on every leg [95% interval, bootstrap over maps]

| | 15x15 | 31x31 | 51x51 |
|---|---|---|---|
| Expansions: index + A* | 0.31 [0.27, 0.34] | 0.47 [0.44, 0.50] | 0.48 [0.45, 0.53] |
| Expansions: LPA* | 0.15 [0.12, 0.18] | 0.27 [0.24, 0.29] | 0.30 [0.27, 0.33] |
| Expansions: index + LPA* | 0.14 [0.11, 0.17] | 0.23 [0.20, 0.25] | 0.24 [0.21, 0.28] |
| Time: index + A* | 0.32 [0.28, 0.35] | 0.49 [0.46, 0.52] | 0.50 [0.46, 0.54] |
| Time: LPA*, first implementation | 1.18 [1.04, 1.33] | 1.73 [1.59, 1.87] | 1.85 [1.69, 2.02] |
| Time: LPA*, optimised | 0.41 [0.36, 0.47] | 0.61 [0.56, 0.67] | 0.67 [0.60, 0.74] |
| Time: index + optimised LPA* | 0.34 [0.28, 0.40] | 0.51 [0.47, 0.56] | 0.53 [0.47, 0.61] |
| Index on top of optimised LPA*: expansions | 0.89 [0.85, 0.93] | 0.85 [0.82, 0.87] | 0.82 [0.78, 0.85] |
| Index on top of optimised LPA*: time | 0.82 [0.77, 0.87] | 0.84 [0.81, 0.87] | 0.80 [0.75, 0.84] |
| Time: index + optimised LPA* / index + A* | 1.06 [0.91, 1.20] | 1.05 [0.98, 1.13] | 1.08 [1.00, 1.17] |
| State kept between commits (pickled KiB): index + A* | 1.7 | 3.5 | 5.7 |
| State kept: optimised LPA* | 89 | 369 | 968 |
| State kept: dictionary LPA* | 32 | 129 | 306 |
| Initial table build, optimised LPA* / A* | 2.6 | 2.2 | 2.2 |

600 / 753 / 727 episodes on 276 / 295 / 300 maps; 63,397 leg-cost checks, all six methods agree. Timings: 4 worker processes, each
method timed back to back inside one process on identical inputs; a second run under machine load gave ratios within 0.03.

**What this changes.** The paper's sentence "LPA* was 1.2-1.9 times slower in wall-clock time than A* on every leg ... which we
attribute to the implementation" is true of the first implementation and the attribution was right, but it understates LPA*: once
optimised, LPA* on every leg takes 0.41-0.67 of the A* time. The defensible statements are (i) LPA* saves more search than the index,
(ii) the index removes a further 11-18% of expansions and 16-20% of time on top of optimised LPA*, (iii) index + A* and index + LPA*
take the same time within noise, and (iv) the index keeps 50-170x less state between commits than LPA* and needs no persistent
search structures. The 22-27% time figure was measured on the first implementation and should be replaced by 16-20%.

## Safeguard, with intervals (bootstrap over maps)

Validation set (seeds 20000-20599, threshold fixed beforehand at 0.999): reachable goals, 5,275 episodes on 1,750 maps.

| | commit at 0.95 | staged, 0.999 |
|---|---|---|
| Reachable goal abandoned | 42 (0.80% [0.51, 1.12]) | 0; one-sided 95% upper bound 0.17% by maps, 0.06% by episodes |
| Mean actions, reachable | 64.8 | +0.59 [0.34, 0.88] |
| Unreachable goal not abandoned (of 1,310) | 0 | 0 |
| Mean actions before stopping, unreachable | 45.9 [43.6, 48.1] | 96.5 [92.5, 100.6]; +50.7 [48.3, 53.1] |

Threshold sweep on a third set (5,197 reachable episodes on 1,731 maps; 1,379 unreachable):

| second threshold | reachable abandoned | extra actions, reachable | actions before stopping, unreachable |
|---|---|---|---|
| none (commit at 0.95) | 32 (0.62% [0.40, 0.86]) | - | 45.2 |
| 0.99 | 9 (0.17% [0.08, 0.30]) | +0.32 | 67.7 |
| 0.999 | 0 (upper bound 0.17% by maps) | +0.49 | 94.5 |
| 0.9999 | 0 | +0.51 | 117.2 |
| 0.99999 | 0 | +0.53 | 129.4 |

The trade-off is monotone: each tighter threshold costs about 12-27 more actions on a goal that really is unreachable. 0.999 was the
first value tried and was not chosen from this sweep. Zero observed is not zero: the data rule out a rate above about 0.17%. The
safeguard is a threshold on one failure mechanism, not a safety guarantee.

## Reference audit

All 25 entries exist. One error: `mohan2024` is missing an author (Yoni Sher, seventh of eight, per the journal's Crossref record).
`tang2024` also appeared at NeurIPS 2024. Several entries lack pages or DOIs. EvoCF is `chi2026` (ICML 2026, PMLR 306). SHOPFixer is
Goldman, Kuter and Freedman 2020, not "Zhaowei et al." as the prompt had it. Fritz and McIlraith state "The action theory D remains
unchanged": their discrepancies are in the state, not the model.

## Numbers in the paper checked against result files

17,170 repairs (4,102 + 6,338 + 6,730, `final_diag.json`); 2,081 episodes (600 + 753 + 728); 15.7 million (15,739,200,
`counterexample_search.json`); 939 commits (test output); 63,397 (reproduced in the rerun); direct-support rows (`valonly.json`);
time 0.65/0.70/0.69 (`timing.json`); 1,800 game episodes and 0.78 (`game_levels.json`); 19 -> 0 (`abandonment.json`); 42 -> 0 on
1,750 maps, 46 vs 97 actions (`safeguard_validation.json`). All match. Not re-derived in this pass: Table 1 bootstrap intervals and
the probing rows (taken from `final_summary.json` by `make_tables.py`).

## Applied to the manuscript (2026-11-20)

The fourth-pass corrections are now in `paper/main.tex` (backup: `paper/main_before_fourth_pass.tex`): optimised LPA* timings, the 16-20% time saving and state sizes replace the "1.2-1.9 times slower" sentence; the 4x4/5x5 check replaces the 939-commit figure; the safeguard paragraph carries the 0.17% upper bound and the 0.99 sweep result; Yoni Sher added to `mohan2024`. Cut to stay at four pages: the sentence on cell-exception retraction, the never-give-up agent, the index entries per leg, the description of the posterior-sampling bug, and Figure 1 is 0.75 of the text width.

---

# Fifth pass (2026-11-20): four-way totals, coverage sweep, adversarial case

No manuscript text changed in this pass. New script: `scripts/coverage_sweep.py` -> `results/coverage_sweep.json`.

## Four-way comparison including the initial table build (time, ratio to A* on every leg; 95% interval over maps)

| | 15x15 | 31x31 | 51x51 |
|---|---|---|---|
| Index + A* | 0.69 [0.66, 0.73] | 0.71 [0.69, 0.74] | 0.69 [0.66, 0.72] |
| Optimised LPA* | 1.35 [1.25, 1.45] | 1.21 [1.15, 1.27] | 1.17 [1.11, 1.24] |
| Index + optimised LPA* | 1.42 [1.31, 1.54] | 1.22 [1.15, 1.29] | 1.12 [1.05, 1.20] |
| Expansions: index + A* / LPA* / both | 0.60 / 0.63 / 0.63 | 0.67 / 0.60 / 0.57 | 0.66 / 0.57 / 0.54 |

LPA* wins after the initial build (0.41-0.67 of the A* time) but its initial build costs 2.2-2.6 times an A* build, and episodes
here have only 4-5 commits, so over a whole episode index + A* is the fastest of the four. One Python implementation; a longer
episode would favour LPA*.

## Cost of one commit against the share of cached legs whose cost really changed (all sizes pooled; ratio to A* on every leg)

| legs changed | commits | index + A*, time | direct only, time | LPA*, time | index + LPA* / LPA*, time | commits leaving a stale leg, direct only |
|---|---|---|---|---|---|---|
| 0% | 5,416 | 0.14 [0.12, 0.16] | 0.01 | 0.32 [0.28, 0.37] | 0.24 [0.19, 0.30] | 427 |
| 0-25% | 1,096 | 0.46 [0.41, 0.51] | 0.19 | 0.63 [0.57, 0.69] | 0.75 [0.70, 0.81] | 360 |
| 25-50% | 1,422 | 0.79 [0.76, 0.83] | 0.36 | 0.95 [0.88, 1.03] | 0.96 [0.93, 0.98] | 806 |
| 50-75% | 588 | 0.99 [0.97, 1.01] | 0.51 | 1.19 [1.08, 1.31] | 1.06 [1.02, 1.11] | 319 |
| 75-100% | 291 | 1.04 [1.01, 1.11] | 0.60 | 1.33 [1.18, 1.54] | 1.11 [1.03, 1.22] | 100 |

The affected share is observed, not controlled: these are the 8,813 commits of the held-out episodes, binned. Reading: the index
pays when under about half the table changes, breaks even at 50-75%, and costs about 4% when nearly everything changes; on top of
LPA* it costs 6-11% above half. 61% of commits change no cached leg at all, which is where the saving comes from. Direct support is
always cheaper and leaves a stale table after 2,012 of 8,813 commits (staleness persists across later commits).

## Adversarial case for direct support (`tests/test_index_properties.py::test_unused_rule_gets_cheaper_old_plan_feasible_but_suboptimal`)

5x5 grid, wall at x=2 for rows 0-3 except one type-0 obstacle cell at (2,2); row 4 open. Leg from (0,0) to (4,0). With rule 0 at
cost 50 the optimal leg goes round by row 4: cost 12, direct support empty, alternative support {0}. Rule 0 is then committed at
1.111. The old path is still walkable at cost 12; the optimum is now 8.111 through (2,2). Direct support: 0 legs recomputed, 1 stale
(excess 3.889). Index: 1 leg recomputed, 0 stale. In real held-out episodes the direct-support agent took more actions than the
indexed agent in the worst case by 51 (51x51, seed 1071, block: 420 against 369). It took more actions in 486 of 3,777 episodes and, by chance, fewer in 146.

## Applied to the manuscript (fifth pass)

Added to the incremental-search paragraph: totals including the initial build (index + A* 0.69-0.71; LPA* 1.17-1.35) and the coverage regime (pays under about half the legs changing, about 4% cost when nearly all do, 61% of commits change none). Cut for space: the mention of the first, slower LPA*; "and nothing recorded that the plan had avoided it"; "the excess grows with board size"; "2-3% of the episode". Backup: `paper/main_before_fifth_pass.tex`.
