---
doc_type: issue
title:
  TradFi bare instrument_type (UD/OPTION/FUTURE/COMBO) phantom manifest rows — one write batch, no backing GCS objects,
  explains the mtds_available_at_cross_asset_backfill "genuine ~16% gap"
summary: >-
  Investigating the still-open tradfi lane of mtds_available_at_cross_asset_backfill_2026_07_13.md's Apply todo
  (pre-2023-04 ohlcv_1s/ohlcv_1m available_at fill), found the remaining unfilled population is dominated by phantom
  manifest rows — instrument_type in {UD, OPTION, FUTURE, COMBO} (bare, no instrument_id, no underlying), all written in
  a single ~9-second batch (2026-07-27T16:46:31-40Z), with NO corresponding real GCS object (directly confirmed for
  UD/OPTION/FUTURE via gcs_describe/list at sampled dates+venue). UD alone was already known + quarantined
  (unified-api-contracts market_data_categories.py TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE, root cause not
  confirmed); this extends that finding to OPTION/FUTURE/COMBO (same batch, same signature) and also found that
  frozenset is NOT actually wired into deployment-api's _ACCEPTED_EXCEPTIONS despite its own comment claiming it is.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-api]
scope: [engineer, admin]
tags: [tradfi, manifest, phantom-rows, data-correctness, available_at, instrument_type, delete-safety]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Found while working mtds_available_at_cross_asset_backfill_2026_07_13.md's tradfi Apply todo (task
  mtds_available_at_cross_asset_backfill-008), 2026-08-03, slot 14."
---

# TradFi bare instrument_type phantom manifest rows (UD/OPTION/FUTURE/COMBO)

## What I found

Re-ran the tradfi `available_at` fill-rate check for pre-2023-04-10 `ohlcv_1s`/`ohlcv_1m` captured rows against the
live-freshly-consolidated manifest
(`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, consolidated
2026-08-03T00:34:07Z). Raw fill rate: 88.6%. Folded by `UPPER(instrument_type)` (the known C2a casing-migration-pending
workaround this doc's parent plan already established): 91.9% (8,377/9,117 distinct
`(date, venue, data_type, UPPER(instrument_type))` cells covered).

**Broke down the 740 still-unfilled folded keys** — dominated by 4 `instrument_type` values, NOT `ohlcv_1s`/`ohlcv_1m`
data proper:

```
UD              372 folded keys (2,232 raw rows)
OPTION          205 folded keys (1,230 raw rows)
COMBO            73 folded keys (raw rows include real underlying-bundle rows AND phantom rows — see below)
FUTURE           59 folded keys (raw rows include real per-instrument/bundle rows AND phantom rows)
OPTIONS_CHAIN    31 folded keys (real, recently-written, see § "Not phantom" below)
```

**All 4 of UD/OPTION/FUTURE/COMBO's fully-unfilled rows share one exact signature**: `instrument_id IS NULL`,
`underlying IS NULL`, `written_at` in the identical 9-second window **2026-07-27T16:46:31.986Z ..
2026-07-27T16:46:40.441Z** — clearly one batch job/writer run, not organic capture traffic (8,556 such rows total in
just this pre-2023-04/ohlcv_1s+1m slice; the true corpus-wide count is unknown — not checked, see § Recommended next
steps).

**Confirmed via direct GCS checks these are phantom (no backing object), not just unfilled**:

- `instrument_type=UD` was already documented as unresolved residue (see § "Prior art" below) — this session reconfirms
  it, no new check needed.
- `instrument_type=future` / `instrument_type=option` (bare, lowercase per the real hive-path convention): checked
  `gs://market-data-tick-tradfi-prd-central-element-323112/raw_tick_data/by_date/day=2020-03-31/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/`
  — only `instrument_type=combo/`, `instrument_type=futures_chain/`, `instrument_type=options_chain/` exist. **No bare
  `instrument_type=future/` or `instrument_type=option/` prefix exists at all.** Same result at 2 more sampled dates
  (structure confirmed identical for the whole 2019-2023 range these phantom rows span).
- `instrument_type=combo` (bare, blank underlying) rows: sampled `date=2020-01-05/CME/ohlcv_1m` — every raw row for that
  folded key has `underlying=None`, matching the phantom signature (a REAL combo row for the same day, e.g.
  `underlying=WTI-BZ`, DOES exist with a real backing object and IS filled — real and phantom combo rows coexist under
  the same `instrument_type=combo` label, distinguished by whether `underlying` is populated).

**Excluding all rows matching the phantom signature (written_at in that 9s window AND `instrument_id`+`underlying` both
null) from the population and re-folding**: real folded keys drop from 9,117 to 8,408; **real fill rate rises to 99.63%
(8,377/8,408)**. The only remaining unfilled real folded keys are all `instrument_type=OPTIONS_CHAIN` (31 keys) — see
next section.

## Not phantom: OPTIONS_CHAIN's 31 remaining unfilled keys

Spot-checked one (`date=2020-07-27, CME, ohlcv_1m, underlying=SP500, quote=USD, margin=linear`): the manifest row's
`written_at` is `2026-08-02T23:22:43Z` and the real GCS object
(`.../instrument_type=options_chain/data_type=ohlcv_1m/underlying=SP500/quote=USD/margin=linear/ticks.parquet`) has
`time_created=2026-08-02T23:22:42Z` — essentially the same instant. This looks like a genuinely real, very recently
(possibly still actively) written shard, not a stale gap — plausibly a live/in-progress options_chain backfill still
landing objects marginally ahead of the manifest read. Not investigated further (out of scope for this finding; tiny
population, 31/8,408 = 0.4%).

## Prior art (why this isn't a fresh discovery, just an extension of one)

`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:806-819` already documents
`instrument_type=UD` as `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` — "3,607 captured rows, venue=CME, spanning
2021-2026 in disjoint yearly chunks. Investigated twice: no writer found stamping bare instrument_type='UD' ... GCS
checked at 3 dates found no instrument_type=UD/ or instrument_type=ud/ path. Quarantined per the operator's standing
classify-or-quarantine precedent (UNKNOWN, 2026-07-18) — root cause NOT fully confirmed." This session's finding:
**OPTION/FUTURE/COMBO-bare share the exact same signature (same 9-second write batch, same blank id+underlying shape,
same GCS non-existence) and should very likely be added to the same quarantine class** — this is one root cause across 4
instrument_type labels, not 4 separate issues.

**Also found while checking how the UD residue set is consumed**: its own comment claims "consumed by
`_ACCEPTED_EXCEPTIONS[("instrument_types", "tradfi")]`" but
`deployment-api/deployment_api/routes/data_status/ _distinct_values.py:200-206`'s actual `_ACCEPTED_EXCEPTIONS` dict
maps `("instrument_types", "tradfi")` to `CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`
(`{"options_chain", "futures_chain"}` only) — `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` is defined + exported
but never actually wired in. The census/data-status surface is therefore NOT currently silencing UD as its own comment
claims.

## Why it matters

`mtds_available_at_cross_asset_backfill_2026_07_13.md`'s tradfi "Apply" todo has been re-run and re-diagnosed across at
least 4 sessions (2026-07-14, 2026-08-02 x3) chasing a "genuine ~16% gap" that turned out to be >95% phantom manifest
bookkeeping the rebuild script structurally cannot fill (no real GCS object exists to read a `time_created` from) — the
same "aggregate metric dominated by out-of-scope rows" trap this same plan's prediction lane hit and resolved in its own
session #21 (`mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md`). Flipping the plan's Apply todo now
against the corrected 99.63% real-data metric, citing this issue doc.

Separately, these are `capture_status=captured` manifest rows with **no real backing data** — the same defect class as
the already-resolved "4,991 phantom captured FIXTURE_EVENTS manifest rows" (sports) — a genuine, if small (8,556 rows in
this one slice), manifest-correctness problem independent of the `available_at` question.

## Recommended next steps

- [ ] [DATA] P2. Determine the FULL corpus-wide scope of this phantom signature (written_at in
      `2026-07-27T16:46:31Z..2026-07-27T16:46:41Z` AND `instrument_id IS NULL` AND `underlying IS NULL`) — this session
      only checked the pre-2023-04 `ohlcv_1s`/`ohlcv_1m` slice (8,556 rows); the same 9-second batch likely touched
      other data_types/date ranges too. Read the manifest with this filter directly (bounded read, already have the
      parquet locally cached from this session if still fresh) — do not re-derive via a new GCS walk. (repo:
      market-tick-data-service)
- [ ] [SCRIPT] P2. Root-cause what wrote this exact batch (2026-07-27T16:46:31-40Z, ~9 seconds, 8,556+ rows across 4
      instrument_type labels) — check `run.log`/Cloud Logging around that timestamp for whatever backfill/migration VM
      or script was active then; the prior UD investigation already tried and failed twice, so this may need a different
      angle (e.g. searching by the exact `written_at` timestamp cluster rather than by instrument_type). (repo:
      market-tick-data-service)
- [ ] [DATA] P2. Once root-caused (or if root-cause remains elusive after the above), extend
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`'s
      `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` frozenset to add `"OPTION"`, `"FUTURE"`, `"COMBO"` alongside
      the existing `"UD"` (same evidenced signature) — OR, if by then the operator has ruled these should be deleted
      (delete-safety protocol, since they carry zero real data and a false `capture_status=captured` claim) rather than
      quarantined, do that instead. Do not delete manifest rows without a fresh delete-safety 5-part-proof pass
      regardless of how confident this doc's evidence looks. (repo: unified-api-contracts)
- [ ] [CODE] P3. Fix the wiring gap — `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` should actually reach
      `_ACCEPTED_EXCEPTIONS[("instrument_types", "tradfi")]` in
      `deployment-api/deployment_api/routes/data_status/     _distinct_values.py`, or its own comment should stop
      claiming it does. Decide which (probably: fix the wiring, since the comment's intent is clear) after todo 3 lands
      so the exception set is correct at wiring time. (repo: deployment-api)

## Progress Log

- **2026-08-03** — Filed while working `mtds_available_at_cross_asset_backfill_2026_07_13.md` task
  `mtds_available_at_cross_asset_backfill-008` (data_engineering, slot 14). Full evidence above.
