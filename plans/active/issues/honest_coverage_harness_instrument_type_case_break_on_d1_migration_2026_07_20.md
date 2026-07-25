---
doc_type: issue
title: Honest-coverage v2 harness reads instrument_type lowercase — the D1 UPPERCASE migration will zero-match it
summary:
  The v2 honest-coverage harness reads the manifest `instrument_type` column at its current LOWERCASE writer grain
  (`spot`, `perpetuals`, `pool`, `lending`, …), documented as SSOT in honest-coverage-model.md. The 2026-07-20 D1 ruling
  makes the canonical manifest `instrument_type` COLUMN UPPERCASE. When the D1 migration flips the writers to the
  UPPERCASE enum, the harness's lowercase reads/matches will silently zero-match every migrated shard unless it
  normalises case. This is a latent correctness hazard gated on the D1 migration — not a live break today.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags: [honest-coverage, instrument-type, case, d1-ruling, migration-pending, coverage-harness, ssot-contradiction]
related:
  [
    ../data_pipeline_reconciliation_skill_2026_07_20.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/canonical-cutover-register.md,
    /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
  ]
created: 2026-07-20
last_updated: 2026-07-25
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: instruments-service@867b68f6
depends_on:
source:
  found by the /data-pipeline-reconciliation post-phase consistency audit (todo 19), 2026-07-20 — reported as the one
  substantive contradiction it refused to blind-fix
---

# Honest-coverage v2 harness reads `instrument_type` lowercase — D1 UPPERCASE migration will zero-match it

> **⚠️ BIG FINDING (SSOT contradiction + latent data-correctness).** Operator-notified 2026-07-20. Not a live break
> today; it arms when the D1 `instrument_type`-column UPPERCASE migration runs.

## The contradiction

- `/codex/02-data/honest-coverage-model.md:154-157` states, as CK3-certified SSOT for the v2 coverage harness's read
  grain: _"`instrument_type` is a **real lowercase writer-grain column** (`spot`, `perpetuals`, `options_chain`,
  `futures_chain`, `pool`, `lending`, `prediction_market`, …) — **NOT the UPPERCASE catalogue enum**. The v2 harness
  MUST read `instrument_type`…"_
- The 2026-07-20 **D1** ruling (`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md` § D1 +
  `/codex/02-data/cross-asset-canonical-target-ssot.md` §7/§11) makes the canonical manifest `instrument_type` **COLUMN
  UPPERCASE** (catalogue enum wins).

These describe the **same column** in opposite cases. Both are internally right for their moment: honest-coverage
describes **current reality** (writers emit lowercase today), D1 describes the **target**. The gap between them is the
`migration_pending` window.

## Why it is a hazard, not just drift

The harness matches manifest rows by `instrument_type` value. It reads lowercase. When the D1 migration flips the
writers (and rewrites the historical column) to the UPPERCASE enum, every migrated shard's `instrument_type` stops
matching the harness's lowercase expectation → the shard is counted as **not covered** → coverage silently craters for
migrated asset_groups while the data is fully present. Same fail-closed / silent-zero class as the other case-sensitive
matchers found in this campaign (the sports MDPS `data_type={data_type}/` substring match; the MTDS `--leagues` filter).

## Correct resolution (do NOT blind-flip the doc)

Flipping honest-coverage-model.md to UPPERCASE now would break the harness against **today's** lowercase data (the exact
OOM/zero-match risk the consistency audit flagged). The resolution is case-robustness across the migration, not a doc
flip:

1. Make the v2 harness's `instrument_type` read/compare **case-insensitive** (normalise both sides to a single case at
   read time) so it is correct in BOTH the pre- and post-D1-migration states.
2. Add a `migration_pending`-window note to `honest-coverage-model.md:154-157`: the column is lowercase **today** (what
   the harness reads); the D1 **target** is UPPERCASE; the harness normalises case so the D1 migration does not zero it.
3. Sequence: this normalisation must land **before** the D1 `instrument_type`-column migration flips any writer/history
   — otherwise coverage craters on the first migrated asset_group.

## Todos

- [x] 1. [DATA] P1. Confirm the exact harness read/compare site(s) for `instrument_type` (grep the v2 coverage harness +
      `read_availability_index` callers that filter/group by `instrument_type`); enumerate every case-sensitive match. —
      instruments-service@867b68f6 + evidence. Audited every read/compare/group site across
      `instruments-service/scripts/{measure_honest_coverage.py,check_enumeration_completeness.py}`: (a) **Layer-1**
      (`check_enumeration_completeness._canon_instrument_type`/`_canon_key`) already normalises case
      (`.strip().lower()`) on BOTH EXPECTED and ENUMERATED sides before intersecting — predates this issue
      (`honest_coverage_uac_writer_matrix_reconciliation`, 2026-06-29) and is already regression-tested
      (`test_case_fold_instrument_type`, `TestAlignmentNotArtifact.test_uppercase_manifest_matches_lowercase_expected`)
      — NO fix needed. (b) the cefi Layer-2 MVP read-time gate (`filter_manifest_to_expected`, the only non-Layer-1 site
      that FILTERS by instrument_type) delegates to the same `_canon_key` — already case-robust, NO fix needed. (c) the
      ONE genuinely case-sensitive site: `measure_honest_coverage._compute_coverage`'s direct pandas
      `groupby(["venue", "instrument_type"])` / `groupby(["venue", "instrument_type", "data_type"])` for the
      `by_venue_instrument_type` / `by_venue_instrument_type_data_type` Layer-2 drill-down projections — these read the
      manifest directly and never went through the Layer-1 normaliser, so a shard whose history spans the lowercase
      writer grain and the post-D1 UPPERCASE spelling would silently SPLIT into two cells. This is the one fixed in
      todo 2.
- [x] 2. [CODE] P1. Make those reads/compares case-insensitive (normalise at read); add a regression test that a shard
      whose column is UPPERCASE and a shard whose column is lowercase both count as covered. —
      instruments-service@867b68f6 + evidence. Added `_casefold_instrument_type_series` (case-folds `instrument_type`
      for GROUPING only, `.strip().casefold()`) + `_representative_instrument_type` (deterministic raw-casing display
      label — mirrors `_canonicalise_tuple_set`'s "first original tuple wins" precedent) in
      `instruments-service/scripts/measure_honest_coverage.py`; both `by_venue_instrument_type` and
      `by_venue_instrument_type_data_type` now group on the case-folded key so a shard's history is never split by
      casing alone, while still reporting the raw writer-grain spelling as the dict key (does not disturb
      deployment-api's distinct-values drift panel, which deliberately reads the raw casing to track the cefi/tradfi
      in-flight migration). Regression tests added to
      `instruments-service/tests/unit/test_measure_honest_coverage.py::TestInstrumentTypeCaseInsensitivity`:
      `test_lowercase_and_uppercase_rows_merge_into_one_shard` (a legacy-lowercase row + a new-uppercase row for the
      same shard merge into ONE cell, both counted captured) and
      `test_uppercase_only_shard_counts_as_covered_same_as_lowercase` (an UPPERCASE-only shard counts identically to a
      lowercase-only shard). Full suite green:
      `instruments-service/.venv/bin/python -m pytest     tests/unit/test_measure_honest_coverage.py tests/unit/scripts/test_check_enumeration_completeness.py -q`
      → 34 + 44 passed. `quality-gates.sh --no-fix` green (`.qg_last_passed_sha=de6591c8` → commit
      `867b68f6179747a51b25410d3771f1e02e571fc6`).
- [x] 3. [DATA] P1. Add the `migration_pending`-window note to `honest-coverage-model.md:154-157` (today lowercase /
      target UPPERCASE / harness normalises), with a dated annotation and a pointer to this issue. —
      unified-trading-pm@c1c317069 + evidence. Added the `migration_pending window (2026-07-25...)` blockquote to
      `/codex/02-data/honest-coverage-model.md` § Layer-2 read grain, documenting today's-lowercase / D1-target-
      UPPERCASE / the Layer-1 normaliser (pre-existing) / the Layer-2 drill-down fix (this issue) / the sequencing gate,
      with a pointer back to this issue doc; bumped `last_reviewed: 2026-07-25` and added this issue to `referenced_by`.
- [x] 4. [REVIEW] P1. Gate: this normalisation lands + is proven green BEFORE the D1 `instrument_type`-column migration
      flips any writer or rewrites history. Cross-link this issue from the D1 migration todo so the ordering is
      enforced. — unified-trading-pm@c1c317069 + evidence. Confirmed the D1 `instrument_type`-column UPPERCASE rewrite
      is performed by `instruments-service/scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py`'s `--apply`
      (its own docstring delta (iv): "instrument_type COLUMN drift — 3.19M BLANK + lowercase/aliased -> canonical"; it
      reassigns `out["instrument_type"] = new_itype` with the UPPERCASE-space canonicalised value) — this is EXACTLY
      todo 3 ("Execute the minutes-gap hybrid cutover (Track 1)") of
      `plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md`. Added a cross-link gate blockquote to
      that todo citing this issue + the shipped fix's commit sha (`instruments-service@867b68f6`), confirming the
      normalisation landed BEFORE that `--apply` runs (the plan is `status: draft`, not yet dispatched) and that the
      todo is now unblocked on this specific dependency. Ordering is enforced.
