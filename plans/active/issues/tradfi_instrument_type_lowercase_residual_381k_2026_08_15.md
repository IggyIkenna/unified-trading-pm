---
doc_type: issue
title: tradfi manifest instrument_type still carries 381,119 lowercase-case rows despite two prior "0 residual" closures
summary: >-
  Running the (already-shipped) distinct-values + axis-value-census enumerators for tradfi
  (`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s "Run distinct-values/axis-value census" todo) found the
  `GET /distinct-values/tradfi` panel reports `non_canonical_count.instrument_types == 0` (true, but only because the
  panel's accepted-exceptions mechanism excludes bundle-grain `options_chain`/`futures_chain` from the headline — it
  does NOT badge lowercase spellings as accepted). A direct live read of the tradfi availability_index (13,748,571 rows,
  `capture_status != attempted_failed`, 2026-08-15) shows 381,119 rows still stamped lowercase
  (`combo`/`equity`/`etf`/`future`/`index`/`spot_pair`) — none of which are in
  `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` (that set only contains `"UD"`). This directly contradicts
  `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s two independent "0 non-UPPERCASE instrument_type rows"
  self-verifications (2026-07-25 post-CAS, and again 2026-07-27 after "2 writer bypasses fixed",
  `/plans/archive/2026_08/tradfi_casing_100pct_redrift_2026_07_27.md`) — a third re-drift, or a residual population
  those two migrations' `--apply` never actually reached.
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [tradfi, casing, instrument_type, manifest, re-drift, distinct-values-census]
related:
  [
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/archive/2026_08/tradfi_casing_100pct_redrift_2026_07_27.md,
    /plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
created: 2026-08-15
author: slot-6 (backend_engineer)
source:
  [
    "tradfi_satellite_ao_dispatch_batch13-f6e63667d3c4, Run distinct-values/axis-value census for tradfi and confirm 0
    non-canonical values",
  ]
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: backend_engineer
drift_direction: unknown
depends_on: []
last_updated: 2026-08-15
parent_epic: tradfi_master
priority: P1
---

# tradfi manifest instrument_type: 381,119-row lowercase residual, despite two prior "0 residual" closures

## What I found

Ran both shipped census endpoints for `asset_group=tradfi` directly (no live server needed — called
`deployment_api.routes.data_status._distinct_values.get_distinct_values` and `..._axis_census.get_axis_value_census`
in-process), per `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s "Run distinct-values/axis-value census for
tradfi and confirm 0 non-canonical values" todo.

**`/distinct-values/tradfi` (honest-coverage rollup, `source_date=2026-08-15`)**: `non_canonical_count` =
`{venues: 0, instrument_types: 0, data_types: 0, chains: 0}` — genuinely 0 across every axis, but ONLY because
`_ACCEPTED_EXCEPTIONS` excludes `options_chain`/`futures_chain` (bundle-grain) and `UD` (unresolved residue) from the
`instrument_types` headline count. Lowercase spellings are NOT in `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE`
(verified live: that frozenset contains exactly `{"UD"}`) — if they existed in the rollup's `by_venue_instrument_type`
keys they WOULD count. They don't show up there, meaning the nightly honest-coverage rollup's own enumeration
under-counts relative to the live manifest (a separate, smaller finding — not investigated further here, out of this
todo's scope).

**`/axis-value-census?service=market-tick-data-service&asset_group=tradfi`** (direct live read of the consolidated
`availability_index`, `capture_status != attempted_failed`, 13,748,571 rows, 2026-08-15) — the RAW, uncanonicalised
`instrument_type` distinct values + counts:

```
EQUITY        8,176,563   (canonical)
COMBO         2,421,453   (canonical)
FUTURE        1,384,961   (canonical)
ETF             574,954   (canonical)
futures_chain   389,838   (accepted exception — bundle-grain, CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES)
combo           339,035   (NOT canonical, NOT accepted)
options_chain   205,963   (accepted exception — bundle-grain)
SPOT_PAIR        53,349   (canonical)
INDEX            34,762   (canonical)
equity           30,561   (NOT canonical, NOT accepted)
BOND             14,399   (canonical)
etf               5,678   (NOT canonical, NOT accepted)
future            4,676   (NOT canonical, NOT accepted)
index               835   (NOT canonical, NOT accepted)
spot_pair           334   (NOT canonical, NOT accepted)
```

Sum of the 6 unexplained lowercase values: **381,119 rows** (`combo` dominates at 339,035, i.e. 89% of the residual).
Confirmed this is genuine case-drift, not the `QUARANTINE_COMBO` relabel mechanism in disguise — that mechanism's own
docstring states "a QUARANTINE_COMBO result's derived_instrument_type is always `'COMBO'`" (uppercase), so a lowercase
`combo` row was never produced by that path.

**`venue`/`data_type`/`chain`/`source`/`pipeline_mode` axes all check out clean** against
`VENUES_BY_ASSET_GROUP['tradfi']` / `DATA_TYPES_BY_ASSET_GROUP['tradfi']` / the accepted-exception sets (`BARCHART`
9,119 rows all `empty_confirmed`, already operator-ruled quarantine-with-tracking; `chain` is empty for every tradfi
row, correct). Only `instrument_type` has an unexplained non-canonical population.

**Why this contradicts prior closures**: `tradfi_manifest_content_recovery_completion_2026_07_24.md` records TWO
independent self-verifications of 0 lowercase residual — one immediately after the 2026-07-25 in-place CAS
(`mtds@4e631a3df071c0d253bd4e5e3c7f053a890fa1be`, "0 non-UPPERCASE `instrument_type` rows... excluding the permanent
`futures_chain`/`options_chain` bundle-grain axis"), a second independent re-read the same day
("`SELF-VERIFY: 4,988,822/4,988,822 UPPERCASE`"), and a THIRD fix after a found re-drift 2026-07-27 ("2 writer bypasses
fixed", `mtds@a1729bb4`, archived as `tradfi_casing_100pct_redrift_2026_07_27.md`). This session's fresh measurement
(2026-08-15, ~3 weeks later) shows 381,119 lowercase rows live — either a fourth re-drift (a still-uncaught writer
bypass keeps forward-writing lowercase) or the 2026-07-25/07-27 `--apply` runs never actually reached this specific
381K-row population (e.g. a different partition/shard-atom path than what those migrations' dry-run scoped). Not
determined which — that's the open work below.

## Why it matters

This is the exact "instrument_type case+plural dupes" defect class the original 2026-07-18 audit found (18 distinct
spellings) and that two dedicated migration passes were supposed to have fully closed. A 381K-row live residual means
either (a) downstream consumers keying/joining on `instrument_type` are silently missing ~2.7% of tradfi rows whose case
doesn't match their filter, or (b) forward writes are STILL emitting lowercase today, in which case the residual will
keep growing rather than being a fixed, shrinking backlog. `combo` alone (339,035 rows, 89% of the residual) deserves
first-priority investigation given its size.

## Recommended decision

Not fixed here (this REVIEW/verify todo's own scope is running the census, not re-diagnosing a writer). Bounded,
AO-eligible follow-up:

## Open work (tracked todos)

- [ ] [DATA] P1. Measure the `written_at` distribution of the 381,119 lowercase `instrument_type` rows (bucketed by
      week) — if any rows have `written_at` newer than the 2026-07-27 writer-bypass fix (`mtds@a1729bb4`), that proves a
      STILL-LIVE writer bypass (find + fix it, mirroring the two prior bypass fixes); if all rows predate it, this is a
      residual the 2026-07-25/07-27 CAS migrations' dry-run scoping simply never covered (identify why — different
      partition path? different capture_status filter?). (repo: market-tick-data-service)
- [ ] [DATA] P1. Once root cause is determined, re-run the existing in-place CAS re-stamp mechanism (the same one used
      2026-07-25, `scripts/migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py`, or its 2026-07-27 successor) on
      the residual 381,119 rows; use the same fresh-retention-check + snapshot-first + CAS-apply + post-apply
      independent-re-verification procedure as both prior runs. Done when a fresh live read shows 0 non-UPPERCASE
      `instrument_type` rows for tradfi (excluding the permanent `futures_chain`/`options_chain` bundle-grain axis),
      confirmed by an INDEPENDENT second read (matches the prior closures' own evidence bar). (repos:
      market-tick-data-service, unified-trading-library)
- [ ] [DATA] P3. Separately investigate why the honest-coverage nightly rollup's `by_venue_instrument_type` enumeration
      (consumed by `/distinct-values/tradfi`) does NOT surface these lowercase spellings at all, even though they are
      present in the live availability_index the rollup is supposed to summarize — a detector gap that let this 381K-row
      residual go unnoticed by the panel this whole time. (repo: instruments-service, or wherever
      `measure_honest_coverage.py` derives `by_venue_instrument_type`)
