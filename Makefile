PY ?= python3

.PHONY: test smoke tables figure paper all-posthoc

test:
	$(PY) tests/test_cpr.py
	$(PY) tests/test_index_properties.py

smoke:
	$(PY) -m cpr.experiment --sizes 15 --seeds 0 6 --out results/smoke.jsonl
	$(PY) -m cpr.analyze results/smoke.jsonl --out results/smoke

tables:
	$(PY) scripts/make_tables.py results/final_summary.json results/final_diag.json paper results/valonly.json results/timing.json results/incremental.json

figure:
	$(PY) scripts/make_walkthrough.py --level 11x11 --start C2 --condition block --seed 0 --shot paper/game_shot.png --out paper/fig_game_walkthrough

paper: tables
	cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main

all-posthoc:
	$(PY) scripts/counterexample_search.py
	$(PY) scripts/valonly_baseline.py
	$(PY) scripts/incremental_baseline.py
	$(PY) scripts/timing.py
	$(PY) scripts/memory.py
	$(PY) scripts/game_levels.py
	$(PY) scripts/abandonment.py
	$(PY) scripts/abandonment_traces.py
	$(PY) scripts/safeguard_validation.py
	$(PY) scripts/audit_stats.py results/final.jsonl results/audit_stats.json
