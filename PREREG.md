# Analysis plan, fixed before the final run

Written 2026-11-20 after a pilot on development map seeds 0–29 and before any run on the final seeds.
Source hash of `cpr/*.py` at freeze: `223588d373e068739028d0776c81af7e7150b10b0b46aaa7db0f795b0ce233ba`

## What was decided using the pilot
The pilot was used to find and fix bugs (a crash when a plan was unreachable; cell exceptions that could
seal the agent in a pocket, now retractable) and to check runtime. No parameter was tuned on outcomes.
Parameters are the defaults in `cpr/agents.py`: prior strength 0.7, block cost 0.8·W, confirmation
threshold 0.95, trigger threshold 10%, cell exception after 8 consecutive failures, probe margin 0.25 actions.

## Final run
Map seeds 1000–1299 (300 maps), board sizes 15, 31, 51, six conditions, eight agents, paired within
(size, seed, condition). An episode is skipped when no rule on the map fits the condition; skips are reported.

## Primary comparisons
Pooled over the three relevant, representable violations (block, slow, unlock), per board size, exactly
as listed in `PRIMARY` in `cpr/analyze.py`. Mean paired difference with a 10,000-resample percentile
bootstrap interval; Wilcoxon signed-rank p-values with Holm correction across all 21 tests.

## Criteria
- H1 (repair): supported if indexed repair uses fewer post-initial node expansions than replanning at
  every size (interval excluding 0) with no difference in actions.
- H2 (probing): supported only if plan-relevant probing has lower actions than BOTH no probing (P2) and
  posterior sampling (P3), interval excluding 0, at two or more sizes, and is not worse than no probing
  by more than 2% of the oracle's actions in the no-violation control.
- The out-of-language condition and the total-cost table (actions + λ·expansions, λ ∈ {0, 0.001, 0.01})
  are reported as they come out, whichever way they go.

## Predictions recorded in advance (from the pilot)
- H1 will hold, with post-initial expansions around 0.5–0.7 of full replanning.
- P4 (versus generic probing) will hold by a wide margin.
- P2 (versus no probing) is uncertain: the pilot showed gains of 1–5 actions, concentrated in the unlock
  condition, with intervals touching 0 at the largest size.
- Probing will be worse than no probing in the out-of-language condition on the larger boards.
- Probing will cost one to two orders of magnitude more planning computation, so it will lose on total
  cost at λ ≥ 0.001.
- The no-revision agent will have the lowest regret when nothing is violated.

## Secondary, labelled as such
Sensitivity to prior strength (0.9) on the same seeds; ground-truth precision and recall of the index
(`cpr/diagnose.py`).

## Addendum after the first final run (2026-11-20)
The first run on the final seeds (kept as `results/final_v1_psrl_bug.jsonl`) exposed a bug in the
posterior-sampling baseline: it only resampled when the committed planning cost changed, so once a rule
was confirmed blocked it could keep attempting the same blocked cell until the step cap (59 of 3,777
episodes). The bug made that baseline look far worse than it is, in favour of our method. Fix: the
baseline now resamples after every attempt. No other agent's code path changed; the rerun confirms that
every other agent's results are identical row for row. Comparison P3 should be read knowing that this
baseline was repaired after the final seeds had been seen once. Nothing else in the plan changed.
Source hash after the fix: `0560a1c88e53f6af8029378067ea6ee3bd413d462900974308dec1157ec2f497`
