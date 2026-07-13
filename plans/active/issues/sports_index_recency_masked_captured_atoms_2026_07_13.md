---
doc_type: issue
title:
  Sports index — 189 atoms where a later empty_confirmed row recency-masks a still-present captured row (residue of the
  2026-07-13 captured->empty_confirmed oscillation; NOT blind-repaired, needs per-subclass adjudication)
summary: |
  While repairing the 2026-07-13 oscillation (21 captured atoms erased by the MTDS-twin cleanup after the v2 sports
  enumerator stamped EXPECTED_PRE/POST_SEASON empty_confirmed over them — enumerator guard shipped + 21 atoms
  re-stamped captured via VM_NAME=osc-repair-20260713), a single-index scan found 189 FURTHER atoms
  (data_type, league_id, date) that carry BOTH a captured row and an empty_confirmed row in the CURRENT raw index,
  where the empty row wins recency-only reader dedup (UTL manifest_writer._read_index._merge_shard_frames has NO
  captured-outranks tie-break, unlike the consolidator since 2026-07-12). The rows coexist because their dedup keys
  differ (service_name / venue / instrument dims), so consolidator dedup can never collapse them; atom-grain consumers
  (data-status, coverage) see whichever wins their own collapse rule. Subclasses: (a) 143 PLAYER_STATS atoms —
  captured rows written 2026-05-06 by service_name=fill-missing-player-stats (row_count NaN) vs EXPECTED_NO_FIXTURE
  empty rows whose written_at was refreshed to 2026-07-13T16:24:30.871968 by the MTDS-cleanup first-attempt re-stamp
  shard; needs on-disk object probes before any flip. (b) 46 FIXTURES atoms — empty rows are DELIBERATE
  truthset-evidenced flips (reason 'flipped_residual_attempted_failed_20260629...__truthset_20260628_confirms_no_fixtures')
  contradicting captured rows (venue=API_FOOTBALL, row_count 1-11): a truthset-vs-capture contradiction to adjudicate,
  NOT a blind re-stamp. Blind-stamping either subclass could undo operator-evidenced decisions, hence parked here.
  Atom lists: regenerate with the single-index scan in this doc (or from the 2026-07-13 session CSVs). Also carries
  the two hardening follow-ups: reader-side captured-outranks tie-break in _merge_shard_frames, and redeploying the
  expected-universe-v2-sports Cloud Run image so the shipped enumerator oscillation guard takes effect at 01:30Z.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer]
tags: [manifest, honest-coverage, oscillation, dedup, sports]
related:
  - plans/active/issues/manifest_consolidator_prune_race_overlapping_executions_2026_07_13.md
  - codex/02-data/availability-manifest-and-data-status.md
created: 2026-07-13
parent_epic: sports_master
priority: P1
source: oscillation investigation 2026-07-13 (operator task "lets fix it")
assigned_vm: ""
resolved_by: ""
locked_by: ""
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Sports index — 189 recency-masked captured atoms (2026-07-13 oscillation residue)

## Context (fixed part, same day)

- Root cause of the oscillation class: `instruments-service/scripts/enumerate_expected_universe.py`
  `_enumerate_v2_sports` emitted `empty_confirmed` (per-day source-rule gate `is_expected_for_source` →
  `EXPECTED_PRE_SEASON`/`EXPECTED_POST_SEASON`, lifecycle rows, `EXPECTED_NO_PROVIDER_COVERAGE`, matchday
  `EXPECTED_NO_FIXTURE`) WITHOUT consulting capture evidence. Fixed by the `enumerate_v2` oscillation guard
  (`captured_set` — a seeder never emits `empty_confirmed` over a captured atom) + unit tests.
- The 21 fully-erased atoms (captured row deleted by `dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py`
  because the only same-identity twin was the enumerator's dishonest empty seed) were content-verified on disk and
  re-stamped captured via per-VM shard `VM_NAME=osc-repair-20260713`
  (`scripts/osc_repair_captured_over_empty_2026_07_13.py`).

## Open work

- [ ] [DATA] P1. Subclass (a) — 143 PLAYER_STATS atoms: probe on-disk objects (UAC `candidate_parquet_paths`,
      PLAYER_STATS layout) for each (league, date); where an object with >=1 row exists, re-stamp captured at the
      canonical league-grain identity (same shard mechanism as osc-repair); where absent, DELETE-or-retype the stale
      `fill-missing-player-stats` captured row instead (it is the dishonest side then). Never blind-flip.
- [ ] [DATA] P1. Subclass (b) — 46 FIXTURES atoms: adjudicate truthset-flip vs captured row (row_count 1-11,
      venue=API_FOOTBALL). The 2026-06-28 truthset says no fixtures; the captured parquet says rows exist. Decide per
      atom by content (open the parquet; a header-only/placeholder parquet → keep the flip; real fixture rows → truthset
      was incomplete for that league-day → re-stamp captured + note truthset gap). Operator-evidenced flips must not be
      silently undone.
- [ ] [CODE] P2. Reader-side hardening: mirror the consolidator's 2026-07-12 captured-outranks-recency tie-break in
      `unified_trading_library/unified_trading_library/manifest_writer/_read_index.py::_merge_shard_frames` (and any
      atom-grain collapse consumers) so a later bare `empty_confirmed` can never mask a captured row at read time.
- [ ] [INFRA] P1. Redeploy the `expected-universe-v2-sports` Cloud Run job image with the shipped enumerator guard —
      until then the 01:30Z nightly keeps emitting season-gate empty rows over captured atoms (the consolidator's
      captured-outranks guard now protects same-identity groups, but the emission churn + cross-identity masking
      persists).
- [ ] [DATA] P3. Sweep other asset groups for the same seeder-over-captured pattern (the enumerate_v2 guard is active
      for every asset_group now via main(); verify the nightly jobs' images pick it up fleet-wide).

## Regeneration recipe (single index read, no corpus walk)

Group the raw index by `(data_type, league_id, date)`; keep groups containing BOTH `captured` and `empty_confirmed`
rows; within each, sort by `(attempted_at, written_at)` and flag groups whose last row is not `captured`. 2026-07-13
measurement: 33,172 contested atoms total; 32,982 resolve captured on recency; 189 resolve empty_confirmed; 1 resolves
attempted_failed.
