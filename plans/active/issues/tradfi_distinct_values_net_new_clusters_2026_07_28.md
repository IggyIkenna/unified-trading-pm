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
status: open
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
last_updated: "2026-07-28"
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
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
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

- [ ] [DATA] P2. Trace the `ESM0`/`ESM0_MIGRATED_20260418T131054Z` chain-axis writer (tradfi manifest `chain` column)
      and either fix the writer to leave `chain=""` for tradfi (mirrors the cefi `_canonical_manifest_venue_chain`
      precedent) or re-stamp the 7+7 rows if the writer fix alone would fragment row identity (same caution as the MTDS
      venue-as-chain precedent on this doc). Source: this doc.
- [x] ✅ [DATA] P3. **CLOSED 2026-07-29 (na-eligibility-audit) — resolved, not a venue.** Confirm whether `YAHOO_FINANCE`
      should be added to `VENUES_BY_ASSET_GROUP['tradfi']` (real, working
      daily-source venue per the 2026-07-19 sourcing decision) or is a mis-stamped `source=` value leaking into the
      `venue` column. Source: this doc.
      `unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py:130` — "YAHOO_FINANCE removed
      2026-07-15 — it was a source-as-venue modeling error, not a real venue (no adapter, no fetch code stamps
      venue=YAHOO_FINANCE). Yahoo is a SOURCE; its rows land under real venues with source=yahoo." Confirmed: the
      mis-stamp answer, not the register-as-venue answer.
- [ ] [DIAG] P3. Identify what writes `instrument_type='UD'` in tradfi and either register it (if a real, distinct
      instrument type) or trace it as a mis-stamp. Source: this doc.

## Progress Log

- **na-eligibility-audit 2026-07-29**: KEEP_NA_STALE_ITEMS. Closed the YAHOO_FINANCE venue-registration item with a
  direct codex/registry citation (already resolved 2026-07-15 — Yahoo is a source, not a venue). The ESM0 chain-axis
  item and the `instrument_type='UD'` item remain genuine open investigation work — not reclassified, correctly stay
  NA.
