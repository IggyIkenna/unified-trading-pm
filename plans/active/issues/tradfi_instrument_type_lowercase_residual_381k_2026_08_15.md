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

**CORRECTION 2026-08-15 (slot-14, data_engineering, via the written_at-distribution todo below) — `combo`'s
classification above is WRONG; it is not case-drift.**
`unified_trading_library/canonical/_manifest_instrument_type_canon.py` (the shared manifest-column canonicalizer every
tradfi/cefi write path routes through) was DELIBERATELY changed 2026-08-10 (`unified-trading-library@74fe04fd98`,
"fix(canonical): exclude combo and continuous_future as bundle-grain manifest types") to REMOVE
`combo`/`continuous_future` from the canonical mapping and add them to `_BUNDLE_GRAIN_EXCLUDED` — evidence-based (a live
473,374-row census found bundle-grain-signature rows, populated `underlying` + null `instrument_id`, incorrectly
classified as per-contract `FUTURE`). Per that commit's own docstring, bare lowercase `combo` is now, BY DESIGN, the
SAME kind of permanent id-less bundle-grain axis as `futures_chain`/`options_chain` — never canonicalized. This directly
means the `CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` registry this doc's own distinct-values discussion above
relies on (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`) is STALE: its own comment
(committed 2026-07-22, `unified-api-contracts@030d64d8`, THREE WEEKS before the UTL ruling) explicitly calls lowercase
`combo` "real case-drift" and deliberately excludes it from the accepted-exceptions set — a direct, git-dated SSOT
contradiction between the two repos' registries. See the "Open work" todos below for the split disposition this
correction implies.

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

- [x] ✅ [DATA] P1. Measure the `written_at` distribution of the 381,119 lowercase `instrument_type` rows (bucketed by
      week) — if any rows have `written_at` newer than the 2026-07-27 writer-bypass fix (`mtds@a1729bb4`), that proves a
      STILL-LIVE writer bypass (find + fix it, mirroring the two prior bypass fixes); if all rows predate it, this is a
      residual the 2026-07-25/07-27 CAS migrations' dry-run scoping simply never covered (identify why — different
      partition path? different capture_status filter?). (repo: market-tick-data-service)

      **DONE 2026-08-15 (slot-14, data_engineering).** Bounded read (`columns=[instrument_type, capture_status,
          written_at]`, no whole-corpus load, wrapped in `run-bounded-analysis.sh`) against the live
          `market-data-tick-tradfi-prd-central-element-323112` availability_index reconfirmed the exact 381,119-row
          population, then measured `written_at`: **100% (381,119/381,119) postdate the 2026-07-27 fix** — min
          `written_at`=2026-08-05T01:32:02Z, max=2026-08-15T06:29:38Z (today), weekly buckets 2026-W32=42,086 /
          2026-W33=339,033. This is unambiguously the STILL-LIVE-bypass branch, not the pre-existing-residual
          branch — but per-instrument_type breakdown splits it into TWO DIFFERENT root causes, not one:
          - **`combo` (339,035 rows, 89%) is NOT a bug.** Traced to `unified-trading-library@74fe04fd98`
          (2026-08-10, "fix(canonical): exclude combo and continuous_future as bundle-grain manifest types") —
          a DELIBERATE, evidence-based ruling (a live 473,374-row census found bundle-grain-signature rows
          mis-typed as `FUTURE`) that removed `combo` from the canonicalizer's mapping and made it a PERMANENT
          bundle-grain exclusion, same treatment as `futures_chain`/`options_chain`. Every write since that
          commit landed is correctly leaving `combo` lowercase, by design — this doc's own earlier "confirmed
          genuine case-drift" conclusion for `combo` was WRONG (see the CORRECTION note added above in "What I
          found"); it only ruled out one alternative hypothesis (QUARANTINE_COMBO) without checking the
          canonicalizer's actual current exclusion set. **Real, separate defect found**: UAC's
          `CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` (`market_data_categories.py`, committed
          2026-07-22 — 3 weeks BEFORE the UTL ruling) still only lists `options_chain`/`futures_chain`, not
          `combo`/`continuous_future` — a stale cross-repo registry, tracked as a new todo below.
          - **`equity`/`etf`/`future`/`index`/`spot_pair` (42,084 rows, 11%, written since 2026-08-05) ARE a
          genuine still-live writer bypass.** Unlike `combo`, all 5 of these tokens ARE present in
          `_MANIFEST_ITYPE_CANONICAL["tradfi"]` (equity/etf/index/future/spot_pair all map to their real
          `InstrumentType`) — so a write path is stamping them WITHOUT calling
          `canonicalize_manifest_instrument_type` at all. Checked `venue_fetch.py::_record_venue_shard_counts`
          (the main tradfi/cefi manifest-key seam) and confirmed it DOES canonicalize on both branches
          (`tradfi_shard[0]` / `fallback_itype` via `_tms._tradfi_manifest_itype`) — so the live bypass is
          elsewhere, not yet pinpointed; tracked as a new todo below rather than absorbed into this
          measurement-scoped todo. `unified-trading-pm@<pending>`.

- [ ] [DATA] P1. **NARROWED 2026-08-15** (was: re-stamp all 381,119 rows) — re-run the existing in-place CAS re-stamp
      mechanism (`scripts/migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py` or its 2026-07-27 successor) on
      ONLY the genuine residual: the 42,084 `equity`/`etf`/`future`/`index`/`spot_pair` rows — NOT the 339,035 `combo`
      rows, which the above measurement confirmed are correctly-classified permanent bundle-grain data, not drift. Must
      be preceded by the still-live-bypass todo below (fix the writer FIRST, else the re-stamp just gets re-drifted by
      the next write). Use the same fresh-retention-check + snapshot-first + CAS-apply + post-apply
      independent-re-verification procedure as both prior runs. Done when a fresh live read shows 0 non-UPPERCASE
      `instrument_type` rows for tradfi excluding the permanent bundle-grain axis (now `combo`/`continuous_future`/
      `futures_chain`/`options_chain` — see the registry-sync todo below), confirmed by an INDEPENDENT second read.
      (repos: market-tick-data-service, unified-trading-library)
- [x] ✅ [DATA] P1. **NEW 2026-08-15.** Find + fix the still-live writer bypass producing lowercase
      `equity`/`etf`/`future`/`index`/`spot_pair` tradfi manifest rows (42,084 rows since 2026-08-05, growing —
      confirmed still writing as of 2026-08-15T06:29Z). `venue_fetch.py::_record_venue_shard_counts` (the main seam)
      already canonicalizes correctly on both its branches — the bypass is a DIFFERENT write path not yet identified;
      the file's own module docstring (`_manifest_instrument_type_canon.py`) names 3 historically-implicated writers
      ("mtds, instruments-service's universe enumerator, market-data-processing-service's continuous-future builder") as
      a starting point. Mirrors the exact defect class `mtds@a1729bb4` (2026-07-27) already fixed twice — find the
      THIRD/Nth bypass. Done when a fresh live read shows 0 rows written after the fix's landing SHA for these 5 tokens,
      confirmed by an independent second read. (repo: market-tick-data-service, and/or instruments-service /
      market-data-processing-service if the trace leads there)

      **DONE 2026-08-15 (slot-14, data_engineering).** Root cause: `ManifestWriter.add()` (the legacy ingest seam,
          `unified_trading_library/manifest_writer/_writer_ingest.py`) never received the BLK-f3950c25 (2026-07-27)
          treatment the `record_captured`/`record_empty`/`record_failed` methods got — it built `AvailabilityRecord(...,
          instrument_type=instrument_type, ...)` with the raw token, no call to `canonicalize_manifest_instrument_type`.
          The live caller: market-tick-data-service's `engine/orchestrator/manifest_finalize.py::_write_shard_counts_to_manifest`
          (the per-shard-count tradfi/cefi capture seam, DISTINCT from `venue_fetch.py::_record_venue_shard_counts` which
          this doc's earlier investigation already ruled out) calls `venue_writer.add(..., instrument_type=itype_key, ...)`
          with the raw hive-partition token for every non-bundle shard. Fixed AT THE SHARED SEAM (not the call site) so
          every current + future `.add()` caller inherits it for free, mirroring the original BLK-f3950c25 fix's own
          rationale: `.add()` now canonicalizes via the same `canonicalize_manifest_instrument_type(resolved_asset_group,
          instrument_type)` call, `resolved_asset_group` already computed in-function (provided kwarg or venue self-heal —
          the real call site never passes `asset_group=` explicitly, relying on self-heal from the tradfi venue, same as
          `record_captured`/etc. already do). Also fixed a second-order regression this exposed: `rebuild_manifest_from_
          canonical_paths`'s drift comparison (`_candle_shard_key_of` / `_walk_canonical_candle_shards` in
          `_maintenance.py`) compared the now-canonicalized manifest column against the permanently-lowercase raw GCS path
          token verbatim (previously coincidentally agreeing only because `.add()` never canonicalized) — both sides now
          re-canonicalize via a new shared `_canonical_itype_for_shard_key` helper (asset_group self-heals from venue) so a
          rebuild no longer resurrects the exact lowercase-residual defect class this fix just closed, and no longer
          spuriously drifts against its own already-canonical manifest rows. Split 3 shard-key helper functions into a new
          `_maintenance_shard_key.py` module to stay under the 900-line file-size ratchet after the fix's line growth.
          4 new/extended unit tests added to `test_manifest_instrument_type_casing_canon.py` (`.add()` uppercases tradfi,
          `.add()` self-heals asset_group from venue, `.add()` leaves bundle-grain lowercase, `.add()` no-ops for non-
          tradfi/cefi). Full `quality-gates.sh` green (7078 passed). Evidence: `unified-trading-library@b0e1d06b3e`.
          **Note for the sibling NARROWED re-stamp todo above**: this fix stops NEW lowercase rows from this bypass, but
          the 42,084 rows already written 2026-08-05..2026-08-15 by this SAME bypass are still lowercase on disk — the
          re-stamp todo (which explicitly gates on this one landing first) still needs to run against them.

- [x] ✅ [DATA] P1. **NEW 2026-08-15, DONE 2026-08-15 (slot-3, data_engineering).** Sync UAC's
      `CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`
      (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`) to add `combo` and
      `continuous_future` alongside the existing `options_chain`/`futures_chain` — syncing this stale (2026-07-22)
      registry to the evidence-based UTL ruling (`unified-trading-library@74fe04fd98`, 2026-08-10) that made both
      permanent bundle-grain exclusions. Update the registry's own comment (currently claims lowercase `combo` is "real
      case-drift... SEPARATE, already-classified finding" — now stale/wrong per this doc's correction above).
      Cross-check whether `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` or a sibling set is the more correct home
      instead (the exact registry-scope judgment the 2026-08-15 CME/mbp_10 verify todo in
      `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md` flagged as its own precedent class) — this is a genuine
      cross-repo SSOT-contradiction fix, not a mechanical rename; verify against `_distinct_values.py`'s actual
      `_ACCEPTED_EXCEPTIONS` consumption before shipping. (repo: unified-api-contracts) —
      `unified-api-contracts@1a27415e50`, `deployment-api@c76302bdb4` (both verified on origin/live-defi-rollout). See
      Progress Log for the cross-check result and an adjacent unrelated QG-blocking finding fixed in the same pass.
- [ ] [DATA] P3. Separately investigate why the honest-coverage nightly rollup's `by_venue_instrument_type` enumeration
      (consumed by `/distinct-values/tradfi`) does NOT surface these lowercase spellings at all, even though they are
      present in the live availability_index the rollup is supposed to summarize — a detector gap that let this 381K-row
      residual go unnoticed by the panel this whole time. (repo: instruments-service, or wherever
      `measure_honest_coverage.py` derives `by_venue_instrument_type`)

## Progress Log

- **2026-08-15 (slot-3, data_engineering, "Sync UAC's CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES" todo,
  DONE)**: `unified-api-contracts@1a27415e50` + `deployment-api@c76302bdb4` (both verified on origin/live-defi-rollout).
  **Cross-check result** (todo's own instruction): read UTL's
  `_manifest_instrument_type_canon.py::_BUNDLE_GRAIN_EXCLUDED` directly rather than trusting this doc's 2-item
  description — it actually declares FIVE permanent bundle-grain tokens (`combo`, `combo_chain`, `continuous_future`,
  `futures_chain`, `options_chain`), not the two named in the todo prose. Synced the full set (added
  `combo`/`combo_chain`/`continuous_future`) rather than partially syncing to the two named values, since `combo_chain`
  is part of the same authoritative permanent-exclusion ruling and leaving it out would recreate the exact
  stale-registry gap this todo exists to close. Confirmed `CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_ INSTRUMENT_TYPES` (not
  `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE`) is the correct home — the RESIDUE set is for
  genuinely-unresolved/quarantined values (root cause unconfirmed, e.g. `UD`), which does not describe
  combo/combo_chain/continuous_future (their root cause is confirmed: deliberate bundle-grain architecture). Rewrote the
  stale comment in both `market_data_categories.py` AND a second, previously-unnoticed duplicate of the same wrong claim
  in `deployment-api/.../_distinct_values.py`'s own module docstring — updated both plus the 3 UAC unit tests + 1
  deployment-api integration test that hard-asserted the old (`combo` excluded) behavior. **Adjacent finding fixed in
  the same pass** (blocking, not part of this todo's scope): `unified-api-contracts`'s QG failed on an UNRELATED
  pre-existing test, `test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_ regressions` —
  `tests/data/execution_service_venue_reachability_baseline.json` (a DIFFERENT ratchet ledger, generated earlier the
  same day per `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`'s P0 dispatcher-wiring todo) still
  listed `uniswap`/`uniswap_v2`/`uniswap_v3`/`uniswap_v4` as unreachable, but the test's own live measurement showed all
  four now have a reachable execution-service connector — someone wired the dispatcher without shrinking the baseline in
  the same change. Shrunk the baseline to `["morpho"]` (the only venue the live check still confirms unreachable) — did
  not myself wire anything, just re-measured and synced the ledger per its own stated convention; left the `morpho` P0
  todo in the sibling plan untouched (no collision). QG green on both repos (deployment-service host under heavy
  multi-slot contention throughout this session — one of the two unified-api-contracts QG passes was needed because a
  ruff-format pre-commit hook reformatted a file after the first green run, moving HEAD past the sentinel).

- **2026-08-15 (slot-14, data_engineering, "Measure the written_at distribution..." todo, DONE)**: bounded live read
  (columns-projected, `run-bounded-analysis.sh`-wrapped) confirmed the exact 381,119-row population and found 100% of it
  postdates the 2026-07-27 fix (written 2026-08-05..2026-08-15, i.e. an active still-live bypass, not a stale
  pre-migration residual). Splitting the population by root cause reversed this doc's own earlier premise for the
  dominant `combo` share: it is CORRECTLY, DELIBERATELY lowercase per a same-family, evidence-based UTL ruling
  (`unified-trading-library@74fe04fd98`, 2026-08-10) that this doc's original investigation never checked — the real
  defect there is a stale UAC registry (`CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`, dated 3 weeks earlier),
  not a writer bug. The remaining `equity`/`etf`/`future`/`index`/`spot_pair` share (42,084 rows) IS a genuine new
  still-live writer bypass, not yet pinpointed (ruled out the main `venue_fetch.py` seam, which already canonicalizes
  correctly). Narrowed the CAS re-stamp todo to exclude `combo`, and filed 2 new P1 todos (find the real bypass; sync
  the stale UAC registry) instead of absorbing either into this measurement-scoped todo. No code shipped this pass —
  this was pure measurement + root-cause classification, per the todo's own scope.
