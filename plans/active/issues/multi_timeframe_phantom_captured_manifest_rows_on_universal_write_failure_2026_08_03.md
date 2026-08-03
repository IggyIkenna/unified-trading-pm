---
doc_type: issue
title:
  "multi_timeframe writes manifest capture_status=captured with a fabricated row_count even when EVERY per-instrument
  parquet write failed — a genuine phantom-captured / honest-absence violation"
summary: >-
  Re-verifying features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md's P2 todo, CEFI:multi_timeframe's
  force leg (VM `features-e2e-cefi-20260803-161807-38e1b8`, run against `features-service@52a7de5c` — AFTER both of this
  session's real fixes: the feature_group_version blob-path bug and the join-collision bug) completed with
  `exit_code=0`, but direct GCS listing confirms **ZERO parquet objects were ever written** under
  `multi_timeframe/by_date/day=2026-07-04/` or `.../day=2026-07-05/` — every one of the 173 HYPERLIQUID instruments hit
  either a "Missing required columns" calculator failure or a "Cannot serialize DataFrame to parquet" sink-write failure
  for every enabled feature group. Despite this, the run's manifest shard
  (`_index/per_vm/features-e2e-cefi-20260803-161807-38e1b8.parquet`) records **36 rows, ALL `capture_status=captured`,
  `row_count=173`** for feature groups (`tf_momentum_alignment`, `tf_structure_context`, `tf_vol_compression`, etc.)
  that produced not one single successful write. This is a textbook phantom-captured manifest row — a downstream
  consumer trusting the manifest (skip-if-fresh checks, honest-coverage reporting, this very e2e-check's own skip leg)
  would believe real feature data exists when none does.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags:
  [
    infra,
    features-service,
    pipeline-e2e-check,
    data-correctness,
    multi-timeframe,
    honest-absence,
    phantom-captured,
    manifest,
    big-finding,
  ]
related:
  [
    /plans/active/issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-08-03
priority: P1
parent_epic: infrastructure_master
source:
  "slot-6, data_engineering, discovered while re-running
  features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md's P2 re-verify todo for CEFI:multi_timeframe
  (after shipping features-service@87942ac0 and @52a7de5c, both of which fixed genuine upstream bugs but reached far
  enough into real execution to expose this third, deeper bug), 2026-08-03"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    features-service/features_service/multi_timeframe/engine/orchestrator.py,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md,
  ]
resolved_by:
---

# multi_timeframe writes phantom `captured` manifest rows on universal write failure

## What I found

`orchestrator.py::run_batch` tracks failure ONLY via whether `process_instrument()` raises an exception:

```python
failed: list[str] = []
for instrument_id in instruments:
    try:
        self.process_instrument(instrument_id, date_str)
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        logger.error("MTF failed for %s on %s: %s", instrument_id, date_str, exc)
        failed.append(instrument_id)
```

But `process_instrument()` → `_compute_and_write()` catches EVERY per-calculator failure internally and never re-raises:

```python
for group_name in self.config.enabled_feature_groups:
    ...
    try:
        result = calculator.calculate(df, symbol=instrument_id)
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        logger.error("Calculator %s failed for %s/%s: %s", group_name, instrument_id, date_str, exc)
        continue
    self._write_feature_group(result, group_name, instrument_id, date_str)
```

`_write_feature_group`'s own sink-write failures (`"Cannot serialize DataFrame to parquet"`) are ALSO caught and logged,
not propagated (confirmed via the real run's log — every write for `wedge_confluence`/`tf_risk_reward`/
`tf_confluence_signals` failed this way for all 173 instruments). So `process_instrument()` always returns successfully
regardless of whether ANY calculator's write actually landed — `failed_count` in `run_batch` stays 0 no matter how
completely the run failed underneath.

`_write_batch_manifest` then computes `success_count = instrument_count - failed_count` (173 - 0 = 173) and writes this
SAME blanket count as `row_count` for EVERY `group_name` in `enabled_feature_groups`, with `capture_status=captured` —
with no per-group tracking of whether THAT group's writes actually succeeded:

```python
success_count = instrument_count - failed_count
...
else:  # success_count != 0
    for group_name in self.config.enabled_feature_groups:
        for tf in source_timeframes:
            writer.add(processing_date=date_partition, row_count=success_count,
                       feature_group=group_name, feature_family="multi_timeframe", timeframe=tf)
```

**Directly verified on real GCS**: zero objects at `multi_timeframe/by_date/day=2026-07-04/` or `.../day=2026-07-05/` in
`features-cefi-test-central-element-323112` (both `gcloud storage ls` calls returned "matched no objects"), while the
manifest shard for the exact same run holds 36 `captured` rows at `row_count=173` across multiple feature groups
(`tf_momentum_alignment`, `tf_structure_context`, `tf_vol_compression`, and others — read directly via `pl.read_parquet`
on `_index/per_vm/features-e2e-cefi-20260803-161807-38e1b8.parquet`).

**Two compounding causes, both need fixing**:

1. **Wrong failure signal**: `run_batch`'s `failed` list only catches exceptions that escape `process_instrument()`, but
   `_compute_and_write` and `_write_feature_group` both deliberately swallow their own failures (reasonable in isolation
   — one bad calculator shouldn't kill the whole instrument), so NOTHING ever propagates up to mark an instrument as
   failed even when literally 0 of its feature groups wrote successfully.
2. **No per-group accounting**: even if (1) were fixed, `_write_batch_manifest` still writes the SAME `success_count`
   for every `group_name` — it has no way to know that `wedge_confluence` failed for all 173 instruments while (if any
   group genuinely DID write) that group succeeded. The manifest granularity needs to match the actual per-(instrument,
   feature_group) write outcome, not one blanket per-run number applied to every declared group.

## Why it matters

- This is exactly the honest-absence violation the workspace's data-pipeline-correctness HARD RULE exists to prevent:
  "never stamp a failure as zero" / no silent placeholders. Here it's arguably worse than a stamped zero — it's a
  stamped 173, actively asserting real data exists where there is none.
- **Downstream consequence, concretely demonstrated**: this same e2e-check's own `--legs force,skip` flow would have the
  skip leg read this phantom-captured manifest and either falsely report a skip-proof "pass" (if it only checks the
  manifest) or fail confusingly (if it also tries to read the non-existent parquet) — either way the check cannot
  produce a trustworthy verdict while this bug stands.
- Any REAL production consumer (skip-if-fresh backfill logic, honest-coverage / data-status reporting, a downstream
  service reading `multi_timeframe`'s manifest to decide whether to compute its own dependent features) would be
  silently misled into believing CEFI multi_timeframe data exists for `day=2026-07-04`/`2026-07-05` when it does not — a
  correctness gap with real operational consequences, not just a check-script cosmetic issue.
- This is now the THIRD distinct, previously-undiscovered `multi_timeframe` bug found in one session (after the
  `feature_group_version` blob-path omission and the join-column-collision crash, both already fixed and shipped) —
  strong evidence `multi_timeframe` has never had a genuine, fully-successful real-data batch run end-to-end. Worth
  treating the WHOLE family as unverified/untrusted until this is resolved, not just this one manifest-accounting bug.

## Todos

- [ ] [SCRIPT] P1. **Track per-(instrument, feature_group) write outcome, not just whether `process_instrument()`
      raised.** `_compute_and_write` (or `_write_feature_group`) should return/accumulate which `group_name`s actually
      wrote successfully for each instrument, threaded back up through `process_instrument` to `run_batch`. Repo:
      features-service (`features_service/multi_timeframe/engine/orchestrator.py`).
- [ ] [SCRIPT] P1. **Make `_write_batch_manifest` per-group-accurate**: replace the single blanket `success_count`
      applied to every `group_name` with the REAL per-group success count from the todo above — a group with 0
      successful writes across all instruments must get `record_empty(...)` (or an equivalent "attempted, 0 succeeded"
      state), never a `captured` row with a nonzero `row_count`. Repo: features-service (same file). **Done when** (for
      both todos together): a from-scratch CEFI:multi_timeframe force-leg run against real data, where every calculator
      genuinely fails (the exact scenario reproduced here — until the upstream missing-groups gap referenced below is
      separately fixed), writes ZERO `captured` manifest rows and the parquet-vs-manifest state agrees; a regression
      test proves a synthetic "every write fails" run does not produce a phantom `captured` row for any group.
- [ ] [DIAG] P2. **Root-cause WHY every calculator failed this run** —
      `Missing required columns: {'close','low','high'}` / `{'close','volume'}` /
      `{'market_structure_bias_4h','market_structure_bias_1d'}` / `{'vol_regime'}` suggest the calculators expect either
      (a) raw OHLCV passthrough columns no current `SourceSpec` in `DEFAULT_SOURCE_FEATURE_GROUP_TIMEFRAMES` marks as
      `~passthrough`, or (b) upstream delta-one feature groups (`level_confluence`, `fibonacci`, `supply_demand_zones`,
      `polynomial_trendlines`) that this session's real delta_one run never actually wrote for CEFI (confirmed via
      direct GCS check: only 12 of 33 registered delta-one feature groups had real output at `day=2026-07-05`) —
      separately confirmed the `polynomial_trendline` (singular) SourceSpec string in `config.py`'s
      `DEFAULT_SOURCE_FEATURE_GROUP_TIMEFRAMES` doesn't match the registry's real group name `polynomial_trendlines`
      (plural), so that spec silently never loads regardless of what delta_one wrote. Needs deciding: should delta_one's
      default feature-group set be expanded to cover everything `multi_timeframe` depends on, or should
      `multi_timeframe`'s calculator set / SourceSpec list be trimmed to only what delta_one actually produces? Not
      resolved here — a design decision, not a mechanical fix. Repo: features-service.

## Progress Log

- 2026-08-03 (slot-6, data_engineering): filed after re-verifying
  `features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`'s P2 todo — CEFI:multi_timeframe's force leg
  completed `exit_code=0` with a fully populated-looking manifest (36 `captured` rows, `row_count=173`) but zero actual
  parquet output, directly contradicting the manifest. Two other real bugs found+fixed in the SAME session
  (`features-service@87942ac0` feature_group_version fix, `features-service@52a7de5c` join-collision fix) are what let
  execution reach far enough to expose this third bug — not fixed here (a real per-group success-tracking +
  manifest-granularity change, out of scope for the verification-only parent todo).
