---
doc_type: issue
title:
  "market-data-processing-service empty-string-fallback baseline (66) is stale vs actual tree (81) -- blocks ANY commit
  to the repo, not caused by any specific recent change"
summary: >-
  Discovered while shipping an unrelated new script (candle_orphan_sweep.py, todo 1 of
  mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md) via quickmerge --agent. STEP 5.101
  (check_no_empty_string_fallback.py) hard-fails market-data-processing-service: 81 `.get("key", "")`-style
  empty-string-fallback sites found vs a recorded baseline of 66 (no_empty_string_fallback_baseline.yaml). All 15
  over-baseline sites are in 3 PRE-EXISTING files this session never touched (migrate_candle_canonical_2026_07.py,
  reconcile_1440_nan_placeholders.py, seed_mock_data.py) -- the new script itself introduces zero new violations. This
  blocks EVERY future commit to the repo (a repo-wide hard gate, not scoped to changed files) until resolved -- not a
  one-off, not caused by this session.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [market-data-processing-service, unified-trading-pm]
scope: [engineer]
tags: [quality-gates, baseline-ratchet, empty-string-fallback, mdps, blocking]
related:
  [
    /plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
source: "slot-13, 2026-07-27, discovered shipping candle_orphan_sweep.py via quickmerge"
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# market-data-processing-service empty-string-fallback baseline is stale — blocks all commits

## What I found

Shipping a new, unrelated file (`scripts/candle_orphan_sweep.py`) via
`quickmerge --agent --files scripts/candle_orphan_sweep.py` fails at STEP 5.101 with:

```
[FAIL] market-data-processing-service: 81 empty-string-fallback site(s) > baseline 66.
New/over-baseline site(s): scripts/migrate_candle_canonical_2026_07.py:1229;
scripts/migrate_candle_canonical_2026_07.py:1361; scripts/migrate_candle_canonical_2026_07.py:1365;
scripts/migrate_candle_canonical_2026_07.py:1366; scripts/reconcile_1440_nan_placeholders.py:209;
scripts/reconcile_1440_nan_placeholders.py:212; scripts/reconcile_1440_nan_placeholders.py:214;
scripts/reconcile_1440_nan_placeholders.py:215; scripts/reconcile_1440_nan_placeholders.py:216;
scripts/reconcile_1440_nan_placeholders.py:351; scripts/reconcile_1440_nan_placeholders.py:447;
scripts/seed_mock_data.py:289; scripts/seed_mock_data.py:290; scripts/seed_mock_data.py:291;
scripts/seed_mock_data.py:315
```

`unified-trading-pm/scripts/quality_gates/no_empty_string_fallback_baseline.yaml:51-52` records
`market-data-processing-service: count: 66` — with no `commit:` reference (unlike the sibling `market-tick-data-service`
entry immediately below it, which DOES carry a `commit:` hash). All 15 flagged sites are in files this session never
edited. This is a genuine, pre-existing drift between the recorded baseline and the actual tree — the check is doing its
job correctly; the baseline entry is what's stale.

## Why I didn't fix it in this session

- **Not in scope**: my task was building `candle_orphan_sweep.py` (todo 1 of the orphan-sweep tooling-gap plan), a
  different concern entirely.
- **Not trivial**: per the check's own remediation guidance, each site needs a real judgment call — rewrite to fail-fast
  (`raise`/`return None`), or `# noqa: qg-empty-fallback` with a genuine one-line reason. A blanket noqa-everything pass
  risks papering over an actual correctness bug (per the workspace's data-pipeline-correctness HARD RULE) rather than
  fixing or justifying it properly. One spot-check (`seed_mock_data.py:289-291`, `_build_instrument_id()`) looks like a
  plausible genuine noqa candidate (mock-data ID construction, not a production data path) but I did not verify all 15
  with the same care, and the other two files (`migrate_candle_canonical_2026_07.py`,
  `reconcile_1440_nan_placeholders.py`) are migration/ reconciliation tools I have no context on.
- **Baseline can only go DOWN** (workspace HARD RULE) — bumping `count: 66` → `81` to unblock myself would be the wrong
  fix even if I wanted a fast unblock.

## Impact

This blocks EVERY future commit to `market-data-processing-service` via `quickmerge`, not just mine — any agent trying
to ship anything to this repo will hit the identical failure until resolved. My own `candle_orphan_sweep.py` sits
committed-locally-pending (staged, QG-clean on every OTHER check, ready to ship the moment this clears).

## Open work

- [x] 1. [SCRIPT] P1. **Triage all 15 over-baseline empty-string-fallback sites** in
      `scripts/migrate_candle_canonical_2026_07.py` (4 sites), `scripts/reconcile_1440_nan_placeholders.py` (7 sites),
      `scripts/seed_mock_data.py` (4 sites) — for each, decide fail-fast rewrite vs
      `# noqa: qg-empty-fallback <reason>`, per `check_no_empty_string_fallback.py`'s own guidance. Repo:
      market-data-processing-service. ✅ market-data-processing-service@01744b73a — 1 docstring false-positive reworded,
      2 dead-code `.get(k, "")` sites (`timeframe`, `blob_path`, both provably always-set by their producers) rewritten
      to direct dict indexing, 13 noqa'd as genuinely deliberate absent-means-N/A cases (canonical row_key hive
      segments, checkpoint metadata that fails safe via the enumeration_signature mismatch path, mock-seed rows). Live
      scan count now 51 (< baseline 66, see todo 2).
- [x] ✅ 2. [SCRIPT] P1. **DONE 2026-07-27 (slot-9).** Re-verified live rather than trusting todo 1's "51" snapshot —
      other commits landed on this hot branch in the interim, so the live count had drifted back to **66** (still `<= `
      the recorded baseline, not a regression). Ran
      `check_no_empty_string_fallback.py --scope     market-data-processing-service --update-baseline`: confirmed
      `01744b7` (todo 1's fix) is a real ancestor of current HEAD (`43d8f7d`), then stamped the baseline with a
      `commit:` reference (`43d8f7d7d30de3430202bf91568cdb61e3a652fc`) matching the `market-tick-data-service` entry's
      format — count stays `66` (accurate, not silently stale), so the next drift is now attributable to an actual
      commit.
- [x] 3. [SCRIPT] P2. Ship the already-written `scripts/candle_orphan_sweep.py` (staged locally in slot-13, zero new
      violations of its own) once todos 1-2 clear the gate. ✅ market-data-processing-service@01744b73a — shipped in the
      same commit as todo 1's fix (the gate cleared for both in one quickmerge).
