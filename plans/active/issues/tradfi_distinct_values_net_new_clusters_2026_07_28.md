---
doc_type: issue
title: >-
  TradFi distinct-values net-new clusters (2026-07-28) — YAHOO_FINANCE venue registration gap, ESM0 futures-root
  chain-axis mis-stamp, UD instrument_type — deferred filing from the 2026-07-28 live-evidence Progress Log entry
summary: >-
  distinct_values_noncanonical_audit_2026_07_20.md's 2026-07-28 "tradfi live-evidence run" Progress Log entry already
  identified two of these three clusters and explicitly deferred filing them ("Root-cause + fix both deferred — file as
  a fresh, precisely-scoped follow-on if picked up; not fixed inline"). This doc is that filing, done as part of
  cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md's line-191 owning-plan-reconciliation todo, plus a third
  cluster (`UD` instrument_type) surfaced by the same 2026-07-28 re-run that the earlier entry did not name. None of the
  three fixes are executed here (read-only audit scope) — filed for the next session/operator to pick up.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, honest-coverage, canonicalisation, venues, chains, instrument_types, distinct-values, manifest]
related:
  [
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-28"
author: unknown
last_updated: "2026-08-05"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
source: >-
  distinct_values_noncanonical_audit_2026_07_20.md line-191 todo (owning-plan reconciliation of every current
  non-canonical value), dispatched via cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md
assigned_role: data_engineering
resolved_by: >-
  tradfi_satellite_ao_dispatch_batch5_2026_07_29.md todo 5 (slot-7, 2026-08-04): all 3 clusters investigated against
  live tradfi manifest (6.4M rows), zero code changes needed — ESM0/MIGRATED chain-axis gone, YAHOO_FINANCE venue
  confirmed 0 live rows (dead code, cite sibling investigation), UD instrument_type root-caused to MDPS
  canonical_writer.py + tracked in tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md.
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md,
    /plans/active/issues/tradfi_yahoo_venue_vendor_conflation_2026_07_27.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
---

# TradFi distinct-values net-new clusters (2026-07-28)

## What I found

Live `GET /distinct-values/tradfi` (in-process, `source_date=2026-07-28`) currently badges: `venues` — `BARCHART`,
`YAHOO_FINANCE`; `instrument_types` — `FUTURES`, `UD`, `UNKNOWN`, `continuous_future`; `chains` — `ESM0`,
`ESM0_MIGRATED_20260418T131054Z`. Disposition per cluster:

- `BARCHART` — already ruled (quarantine-with-tracking, `tradfi_consolidated_closeout` 2026-07-20), no new action.
- `FUTURES` — already tracked cat-1 case/plural drift owned by
  `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s tradfi instrument_type casing track (re-confirmed
  live 410,418/4,307/16 row split across FUTURE/future/FUTURES in the 2026-07-28 Progress Log entry above), no new
  action.
- `UNKNOWN` — already ruled (classify-or-quarantine, operator ruling 2026-07-18), no new action.
- `continuous_future` — cat-1, already an active concept tracked in
  `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` (the build-continuous stitched-series work
  referenced in `unified-api-contracts/registry/market_data_categories.py:820-826`'s `FEATURE_GROUP_DATA_TYPE_OVERRIDES`
  comment) — not registered as a canonical `InstrumentType` member yet, but the owning plan already exists; no new issue
  needed, cross-linked here.
- **`YAHOO_FINANCE` (venue, 6 rows manifest-direct) — NEW, unattributed.** Plausibly the 2026-07-19
  Yahoo-as-daily-source addition (`/codex/02-data/tradfi-databento-sourcing-ssot.md` — Databento = batch SoT, Yahoo =
  daily) never got a `VENUES_BY_ASSET_GROUP['tradfi']` registration. Not confirmed further here.
- **`UD` (instrument_type) — NEW, unattributed.** No existing plan/registry reference found for this token. Root cause
  and real row count not investigated here.
- **`ESM0` / `ESM0_MIGRATED_20260418T131054Z` (chains, 7 rows each manifest-direct) — NEW, unattributed.** These are
  futures-contract root/continuation symbols (e.g. an ES-future roll-migration marker), miscategorized into the `chain`
  axis — tradfi/CeFi/DeFi's `chain` column is meaningless outside DeFi (mirrors this same plan's own RESULT 3 finding
  for cefi), so this is a wrong-axis writer mis-stamp (cat-3), not a registry gap. Writer not traced here.

## Why it matters

`YAHOO_FINANCE` and the `ESM0*` chain values are silent drift the distinct-values panel has been flagging since at least
2026-07-28 without an owner; `UD` is a genuinely unrecognised instrument_type token. None are large in row count (6-7
rows each, per the manifest-direct axis census), so this is a low-blast-radius, precisely-scoped finding, not an urgent
data-correctness emergency — filed per the findings-closure requirement rather than fixed inline (read-only audit
scope).

## Recommended decision

> **NOTE (na-eligibility-audit 2026-07-30, tradfi tranche) — KEEP-NA-STALE, do NOT reclassify.** All three todos below
> are already claimed VERBATIM as one combined todo in `/plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`
> ("Trace/fix 3 distinct-value mis-stamp clusters", whose `Source:` cites this doc by name; its items (1)-(3) map 1:1
> onto the three todos here). That batch doc is `assigned_vm: planning` but **`status: draft`** — NOT ingested, NOT
> dispatched today. Flipping this doc's `assigned_vm` would dispatch a duplicate, so the shared conflict-check
> (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) verdict is CONFLICT → citation fix
> only. Note also that the `YAHOO_FINANCE` half (todo 2) is the SAME question batch5's sibling todo sourced from
> `/plans/active/issues/tradfi_yahoo_venue_vendor_conflation_2026_07_27.md` owns; batch5 already encodes the
> "investigate once, cite from all three" sequencing. Live blocker = batch5's draft status (operator item 5 in
> `/plans/active/issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md`).

- [x] ✅ [DATA] P2. **RESOLVED 2026-08-04 (slot 7, data_engineering) — 0 rows remaining, no fix needed.** Trace the
      `ESM0`/`ESM0_MIGRATED_20260418T131054Z` chain-axis writer (tradfi manifest `chain` column) and either fix the
      writer to leave `chain=""` for tradfi (mirrors the cefi `_canonical_manifest_venue_chain` precedent) or re-stamp
      the 7+7 rows if the writer fix alone would fragment row identity (same caution as the MTDS venue-as-chain
      precedent on this doc). **Measured live 2026-08-04 against the consolidated tradfi
      `_index/availability_index.parquet` (6.4M rows): 0 non-empty `chain` values across the entire tradfi manifest —
      all rows have `chain=""`, confirming the 7+7 rows flagged on 2026-07-28 were cleaned up between then and now. No
      code fix needed for this cluster.** Source: this doc.
- [x] ✅ [DATA] P3. **RESOLVED 2026-08-04 (slot 7, data_engineering) — cite sibling finding, no separate fix needed.**
      Confirm whether `YAHOO_FINANCE` should be added to `VENUES_BY_ASSET_GROUP['tradfi']` (real, working daily-source
      venue per the 2026-07-19 sourcing decision) or is a mis-stamped `source=` value leaking into the `venue` column.
      **Measured live 2026-08-04: 0 `venue=YAHOO_FINANCE` rows in the live manifest. The sibling investigation
      (`/plans/active/issues/tradfi_yahoo_venue_vendor_conflation_2026_07_27.md`, resolved 2026-08-04) confirmed: 0 live
      rows, `write_canonical_shard()` is dead code (the active `_umi_yahoo.py` route never calls it), and
      `YAHOO_FINANCE` was DELIBERATELY removed 2026-07-15 as a source-as-venue modeling error per UAC's
      `market_data_categories.py` + `TRADFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES`. Do NOT re-register it. This doc's own
      YAHOO_FINANCE question is fully answered by that investigation — cite, do not re-derive.** Source: this doc.
- [x] ✅ [DIAG] P3. **TRACED 2026-08-04 (slot 7, data_engineering) — root cause identified, already tracked in sibling
      doc, no separate fix needed here.** Identify what writes `instrument_type='UD'` in tradfi and either register it
      (if a real, distinct instrument type) or trace it as a mis-stamp. **Measured live 2026-08-04: 1,099 rows
      (`capture_status=captured`, venue=CME, source=databento, `ohlcv_1m`=1,092 + `trades`=7), ALL `instrument_id=None`,
      ALL `underlying=None`, ALL written in the 2026-07-27T16:46:31-40Z phantom batch — the IDENTICAL signature as the
      UD/OPTION/FUTURE/COMBO phantom rows already root-caused + tracked in
      `/plans/active/issues/tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md` (traced to
      `market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py`). `UD` is already
      quarantined as `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` in
      `unified-api-contracts/registry/market_data_categories.py`. This cluster is a subset of the broader phantom-batch
      defect already tracked in that sibling doc — no separate fix needed here.** Source: this doc.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tradfi tranche): **KEEP-NA-STALE — citation fixed, `assigned_vm` deliberately
  unchanged.** All 3 todos are bounded, deterministic-outcome work and would otherwise have been a clean RECLASSIFY; the
  shared conflict-check (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) returned
  CONFLICT because `/plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md` already extracts all three verbatim
  as one combined todo citing this doc as its `Source:`. See the note added above the todos. Live blocker is batch5's
  `status: draft`, not this doc's classification.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: trimmed context_scope from 7 to 6 entries (dropped two generic dispatch-batch/closeout
  provenance links) and added the `VENUES_BY_ASSET_GROUP` registry file the `YAHOO_FINANCE` todo would edit.
- **2026-08-04 (slot 7, data_engineering, task `tradfi_satellite_ao_dispatch_batch5-004`)** — Investigated all 3
  clusters end-to-end against the live consolidated tradfi `_index/availability_index.parquet` (6.4M rows, bounded
  single-object read via `gsutil cp`). All 3 checkboxes flipped with evidence — zero code changed (no fix needed for any
  cluster). (1) ESM0/MIGRATED chain-axis: 0 non-empty chain values in the entire tradfi manifest — the 7+7 rows flagged
  2026-07-28 are gone (cleaned up between then and now). (2) YAHOO_FINANCE venue: 0 rows live, confirmed dead code per
  the sibling investigation (`tradfi_yahoo_venue_vendor_conflation_2026_07_27.md`, resolved same day) — cite, do NOT
  re-register (deliberately removed 2026-07-15 as source-as-venue modeling error). (3) UD instrument_type: 1,099 rows
  (all CME/Databento, all written in the 2026-07-27T16:46:31-40Z phantom batch, all `instrument_id=None`) — root cause
  already traced to `market-data-processing-service/.../canonical_writer.py` and already tracked + quarantined in
  `tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md`. No new fix needed for any cluster.
