---
doc_type: issue
title:
  TradFi FX KRW-USD daily bar physically triplicated across THREE venue partitions (FX/SPOT/YAHOO_FINANCE) — 7 manifest
  rows surfaced venue="SPOT" as a fresh non-canonical value on the live distinct-values panel
summary: >-
  Live-evidence finding (operator directly observed `venue="SPOT"` non-canonical in deployment-ui's tradfi
  distinct-values panel, 2026-08-04). Traced via a bounded, column-pruned, predicate-pushdown read of
  `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (single object, no new GCS
  walk): 7 manifest rows carry `venue="SPOT"`, all `instrument_type="SPOT_PAIR"`, `instrument_id=
  "YAHOO_FINANCE:SPOT_PAIR:KRW-USD"`, `data_type=ohlcv_24h`, `source=yahoo`, `service_name=market-tick-data-service`,
  `row_count=0`, dates 2025-01-02..2025-01-10, all `written_at` within the same ~1.2s window
  (2026-08-02T15:46:59.632Z..15:47:00.788Z). Content-verified (not manifest-inferred): for one sampled date (2025-01-02)
  there are THREE real, physically distinct GCS objects carrying the IDENTICAL KRW-USD daily bar
  (open/high/low/close/volume byte-identical) — one correctly under `venue=FX` (the canonical partition, `time_created
  2026-06-11`), and two duplicates under WRONG venue partitions `venue=SPOT` and `venue=YAHOO_FINANCE` (both
  `time_created 2026-07-20`, ~7 minutes apart). The manifest only registered the `venue=SPOT` copies on 2026-08-02 — ~2
  weeks after the GCS objects themselves were created — consistent with a manifest rebuild/consolidation pass
  discovering pre-existing stray objects, not a fresh writer bug on 2026-08-02. `venue=SPOT` is not a registered tradfi
  venue anywhere in `VENUES_BY_ASSET_GROUP['tradfi']`; `venue=YAHOO_FINANCE` is the ALREADY-tracked legacy
  vendor-as-venue artifact (removed from the registry 2026-07-15, see the related doc below) — this finding is new in
  that it shows BOTH wrong-venue partitions carry REAL duplicated GCS objects (not just manifest bookkeeping drift), and
  adds a third, previously-unseen wrong-venue value (`SPOT`) to that same defect family. Not fixed or deleted here —
  read-only investigation, filed per the findings-triage rule.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-api]
scope: [engineer, admin]
tags: [tradfi, fx, venue, data-correctness, manifest, duplicate-rows, canonicalisation, distinct-values, delete-safety]
related:
  [
    /plans/archive/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
    /plans/archive/issues/tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md,
    /plans/archive/issues/tradfi_yahoo_venue_vendor_conflation_2026_07_27.md,
    /plans/archive/issues/tradfi_distinct_values_net_new_clusters_2026_07_28.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-04"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: investigate
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Operator live observation of deployment-ui's tradfi distinct-values panel (venue axis), 2026-08-04 interactive
  session."
context_scope:
  [
    /plans/archive/issues/tradfi_yahoo_venue_vendor_conflation_2026_07_27.md,
    market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_canonical_2026_07.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# TradFi FX KRW-USD daily bar triplicated across FX/SPOT/YAHOO_FINANCE venue partitions

> **📦 ARCHIVED 2026-08-16 — complete.** Every todo (3 main + 1 follow-up) is done, `locked_by` was empty. The
> follow-up's structural fix (`_VENUE_REMAP`-equivalent normalization/rejection) had already landed via a
> different plan's todo (`market-tick-data-service@ff6c2f4a`, 2026-08-09,
> `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`) — this session confirmed it live and flipped this doc's
> own copy of the todo rather than duplicating the fix, then archived per the plan-completion HARD RULE.

## What I found

Operator reported `venue="SPOT"` showing non-canonical in deployment-ui's tradfi distinct-values panel (live,
2026-08-04). Confirmed via `_distinct_values.py`: that panel reads the nightly honest-coverage rollup's `by_venue` map,
which is built by `measure_honest_coverage.py` grouping RAW manifest rows on the `venue` column — so a `SPOT` entry
there means real manifest rows carry `venue="SPOT"`, not an aggregation-layer bug.

**Manifest-side (bounded, column-pruned, predicate-pushdown read of the single consolidated
`_index/availability_index.parquet` object — no new GCS walk):**

| venue | asset_group | instrument_type | data_type | capture_status | service_name             | source | instrument_id                   | row_count | dates                    | written_at (all 7)                                   |
| ----- | ----------- | --------------- | --------- | -------------- | ------------------------ | ------ | ------------------------------- | --------- | ------------------------ | ---------------------------------------------------- |
| SPOT  | tradfi      | SPOT_PAIR       | ohlcv_24h | captured       | market-tick-data-service | yahoo  | YAHOO_FINANCE:SPOT_PAIR:KRW-USD | 0         | 2025-01-02 .. 2025-01-10 | 2026-08-02T15:46:59.632Z .. 2026-08-02T15:47:00.788Z |

7 rows total, all one instrument (KRW-USD), all one ~1.2-second write batch. `SPOT` is not a member of
`VENUES_BY_ASSET_GROUP['tradfi']` (confirmed: only `NASDAQ, NYSE, CME, ICE, CBOE, KRX, FX, FRED`).

**GCS-side, content-verified for the first affected date (2025-01-02)** — listed every object under that date's prefix
and found THREE physically distinct objects carrying the SAME real KRW-USD daily bar
(`open=0.000679, high=0.000684, low=0.000677, close=0.000679, volume=0.0` — byte-identical OHLC across all three):

| Path (venue segment)                                | `pipeline_mode` | `time_created`       | Status                                                                |
| --------------------------------------------------- | --------------- | -------------------- | --------------------------------------------------------------------- |
| `venue=FX/instrument_type=spot_pair/...`            | `batch_yahoo`   | 2026-06-11T10:13:28Z | **Correct** — the canonical partition                                 |
| `venue=SPOT/instrument_type=spot_pair/...`          | `batch_yahoo`   | 2026-07-20T04:35:37Z | **Wrong venue** — duplicate real object, this doc's new finding       |
| `venue=YAHOO_FINANCE/instrument_type=spot_pair/...` | `batch_yahoo`   | 2026-07-20T04:28:59Z | **Wrong venue** — the already-tracked legacy vendor-as-venue artifact |

The `SPOT` and `YAHOO_FINANCE` copies were both created ~7 minutes apart on 2026-07-20 — plausibly the same write pass.
The manifest only registered the 7 `venue=SPOT` rows on 2026-08-02, ~2 weeks after the GCS objects themselves were
created, consistent with a manifest rebuild/consolidation run discovering pre-existing stray objects rather than a fresh
writer bug that day. `row_count=0` in the manifest is itself wrong — the real object has 1 real data row.

## Why it matters

This is a genuinely new cluster, not covered by any existing tracked finding:

- **Not the same as `tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md`'s 1,812 phantom rows** — that
  population is scoped to `venue=FX` with NO backing GCS object at all, written in 3 distinct 2026-07-16/04-06/07-18
  batches. This finding's rows carry `venue=SPOT` (which that doc's `venue=FX`-scoped census would never have seen) and
  DO have real, content-verified backing objects.
- **Not the same as `tradfi_yahoo_venue_vendor_conflation_2026_07_27.md`** (the `YahooFinanceAdapter` row-content
  `venue="YAHOO"` stamp) — that doc is about the row's own `venue` FIELD inside the parquet content; this finding is
  about the GCS PATH partition + manifest venue column landing on `SPOT`/`YAHOO_FINANCE`, a path-level triplication.
- **Storage + correctness impact**: every affected day's real FX daily bar exists 3× in GCS (only 1 canonical). Any
  consumer trusting the manifest's `venue` column for FX/KRW-USD before 2025-01-10 could double- or triple-count this
  instrument, or fail to find it under the canonical `FX` venue while it's actually only registered under `SPOT`.

## Not investigated here (out of scope for this read-only pass)

- The exact writer/script that created the `venue=SPOT` and `venue=YAHOO_FINANCE` duplicate GCS objects on 2026-07-20 —
  not traced. Given the ~7-minute gap between the two and their shared date range, they may be the same run, but this is
  not confirmed.
- Whether this triplication extends beyond the 7 manifest-registered `venue=SPOT` rows (2025-01-02..01-10) — the GCS
  side was only content-verified for one date. A `venue=SPOT` OR `venue=YAHOO_FINANCE` prefix count across the full FX
  date range was not run (would need a bounded read scoped to those two prefixes specifically, not a new whole-corpus
  walk).
- Whether the `venue=YAHOO_FINANCE` duplicate objects are already counted inside the existing
  `tradfi_yahoo_venue_vendor_conflation_2026_07_27.md` scope or are a distinct row population — not cross-checked.

## Recommended next steps

- [x] ✅ [DATA] P2. **DONE 2026-08-04.** Traced the 2026-07-20 write batch via code-trace of
      `migrate_tradfi_canonical_2026_07.py` (commit e16705db, 2026-07-19). Root cause: the July 2026 migration executor
      has NO `_VENUE_REMAP` dict (unlike predecessor `migrate_tradfi_to_hive.py`, which has carried
      `_VENUE_REMAP = {"YAHOO_FINANCE": "FX"}` from inception). As a result, any intermediate-format object in the
      enumeration with a wrong venue token is promoted to a canonical path preserving that token verbatim.
      `venue=YAHOO_FINANCE` (04:28:59Z): D_SINGLE_NOOP path, `_target_single` extracts `_kv(rel)["venue"]` verbatim;
      `_pipeline_mode("YAHOO_FINANCE","ohlcv_24h")` → YAHOO_FINANCE absent from `_VENUE_OVERRIDES` → SOURCE_PRIORITY
      lookup → `["yahoo"]` → `batch_yahoo`. `venue=SPOT` (04:35:37Z, ~7 min later, same run): D_NONHIVE_EQ path,
      `_target_nonhive_eq` extracts `bare[-1]="SPOT"` as venue from a non-hive object. Manifest rows for both venues
      were not registered on 2026-07-20 — the 7 `venue=SPOT` manifest rows appeared only on 2026-08-02 via the
      consolidation discovery run. Investigation script committed: market-tick-data-service@332f405b
      (`scripts/investigate_tradfi_fx_krw_usd_venue_triplication_provenance_2026_08.py`).
- [x] ✅ [DATA] P2. **DONE 2026-08-04.** Measured full scope: bounded reads scoped to `venue=SPOT`/`venue=YAHOO_FINANCE`
      confirmed exactly the 7+13=20 manifest rows already found (2025-01-02..01-10, KRW-USD only, no other
      instrument/date affected) — content-verified all 7 affected dates' `SPOT` and `YAHOO_FINANCE` GCS objects are
      byte-identical to their canonical `FX` twin (OHLC match on every date, not just the original sample). No broader
      corpus walk needed — the population was already fully bounded. (repo: market-tick-data-service)
- [x] ✅ [DATA] P3. **DONE 2026-08-04 — DELETED, not quarantined.** Fresh `gcs_bucket_soft_delete_retention_seconds()`
      check on the tradfi bucket confirmed 604800s (≥7-day floor, qualifies for the reversibility-verified
      autonomous-delete path, delete-safety protocol §3a). Deleted all 14 real duplicate GCS objects
      (`venue=SPOT`/`venue=YAHOO_FINANCE`, 7 dates each) via `gcs_conditional_delete` (generation-matched, 14/14
      succeeded, 0 failures). Snapshotted the manifest index first
      (`_index/backups/availability_index.pre_spot_yahoofinance_esm0_purge_20260804T092533Z.parquet`), then removed the
      corresponding 20 manifest rows (7 `SPOT` + 13 `YAHOO_FINANCE`, the latter including 6 rows with a blank
      `instrument_id` — redundant bookkeeping variants of the same shard) via a generation-matched CAS write (3 attempts
      needed — 2 safely rejected by concurrent writer activity from other slots, 3rd succeeded: 6,414,541 → 6,414,507
      rows). Fresh post-purge read confirms 0 rows with `venue` in `{SPOT, YAHOO_FINANCE}` remain. Quarantine was
      considered and rejected — these were 100%-confirmed redundant duplicates of already-correctly-captured data, not
      genuine residue worth preserving. (repo: market-tick-data-service)

## Progress Log

- **2026-08-04 (interactive session)**: filed from operator's live observation of the deployment-ui distinct-values
  panel. Root-caused via a bounded manifest read (7 rows, single object, no new walk) + content-verified GCS listing for
  one sampled date (3 real, identical-content objects across FX/SPOT/YAHOO_FINANCE partitions). Not fixed — read-only
  investigation.
- **2026-08-04 (interactive session, same day, operator direct — "purge, don't just report")**: closed todos 2+3.
  Content-verified all 7 affected dates (not just the original sample), deleted the 14 real duplicate GCS objects and
  the 20 corresponding manifest rows, verified 0 remain. Todo 1 (tracing the exact 2026-07-20 writer) stays open — the
  population is fully remediated but the root writer that created these duplicates was never identified, so a repeat
  occurrence (a different instrument/date) would not be structurally prevented. Also triggered a fresh
  `measure-honest-coverage` VM run (tradfi-scoped) so the deployment-ui distinct-values panel reflects this fix instead
  of its previous (up to 24h-stale) cached rollup.
- **2026-08-04 (AO dispatch agt-tradfi_fx_krw_usd_triplicate_venue_partitions-001, slot 2)**: closed todo 1. Code-traced
  `migrate_tradfi_canonical_2026_07.py` (commit e16705db, 2026-07-19) as the exact writer for both wrong-venue GCS
  objects. Root cause: missing `_VENUE_REMAP` dict — the July 2026 executor preserves source venue verbatim, unlike
  `migrate_tradfi_to_hive.py` (has `_VENUE_REMAP = {"YAHOO_FINANCE": "FX"}` from inception). The `venue=YAHOO_FINANCE`
  object (D_SINGLE_NOOP path) and `venue=SPOT` object (D_NONHIVE_EQ bare-segment extraction, ~7 min later) were both
  produced by the same migration run. Manifest rows registered only on 2026-08-02 by the consolidation job (not on
  2026-07-20 when the GCS objects were created). Investigation script committed: market-tick-data-service@332f405b.
- **context-scout 2026-08-06**: re-scouted; all 3 todos are now DONE (traced + measured + purged). Trimmed context_scope
  from 6 to 3 entries — dropped the two doc-only siblings whose content this doc already distinguishes itself from in
  prose, and `_umi_yahoo.py`/`venue_fetch.py` (neither is the confirmed root cause), swapped in the actually-implicated
  `migrate_tradfi_canonical_2026_07.py` (missing `_VENUE_REMAP`, the root cause per the 2026-08-04 code-trace — a repeat
  occurrence is not structurally prevented until that gap is closed).

## Follow-ups

- [x] ✅ [SCRIPT] P3. **Already resolved 2026-08-09 by a DIFFERENT plan's todo — confirmed 2026-08-16 (slot 30),
      flipping this doc's own copy rather than duplicating the fix.** `market-tick-data-service@ff6c2f4a`
      (`tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` todo 2, landed 2026-08-09T16:39:39Z — confirmed
      ancestor of `origin/live-defi-rollout`) added `normalize_tradfi_venue()` +
      `_TRADFI_VENUE_REMAP = {"YAHOO_FINANCE": "FX"}` in the new
      `_tradfi_migration_recurrence_fixes_2026_08_06.py` module, wired in as
      `migrate_tradfi_canonical_classify_2026_07.py`'s `_normalize_venue` (used by every one of
      `_target_single`/`_target_nonhive_eq`/`_target_chain` via `_canonical_single_path`/`_canonical_chain_path`,
      including the exact `_target_nonhive_eq` bare-segment path this doc's `venue=SPOT` finding traced through).
      Covers BOTH halves of this todo's ask, though the SPOT half is a GENERIC guard rather than a SPOT-specific
      remap (arguably the more correct fix — "SPOT" was never confirmed to always mean FX the way
      "YAHOO_FINANCE" does): any venue token NOT in `VENUES_BY_ASSET_GROUP['tradfi']` after the remap
      (`SPOT`/`BOGUS_STRAY_VENUE`/anything) makes `normalize_tradfi_venue()` return `None`, which makes
      `_canonical_single_path`/`_canonical_chain_path` return `None`, which routes the object to
      `A_CONTENT_REPAIR` (`_needs_content`) instead of a fake canonical path — never silently promoted verbatim.
      Test coverage confirmed live in `tests/unit/scripts/test_migrate_tradfi_canonical_2026_07.py`:
      `test_yahoo_finance_legacy_venue_remapped_to_fx` (the remap half),
      `test_unrecognized_venue_token_rejected_not_promoted` +
      `test_chain_bundle_unrecognized_venue_also_rejected` (the generic-rejection half that structurally covers
      SPOT). No new code needed — read-only verification only this session.

> **CORRECTED 2026-08-16 (slot 30)**: the banner below is now stale — the gap it flags was closed 2026-08-09
> (`market-tick-data-service@ff6c2f4a`, a different plan's todo) and the Follow-up above is now flipped `[x]`
> with that evidence. Every todo in this doc is now done and `locked_by` is empty — archiving in this same
> session per the plan-completion HARD RULE.
>
> **2026-08-06 archive-candidate audit (stale, kept for history)**: Doc's own Progress Log (context-scout
> 2026-08-06): 'a repeat occurrence is not structurally prevented until that gap is closed' — the root cause
> (missing _VENUE_REMAP in the July migration executor) was identified but never fixed, and that gap is not a
> tracked - [ ] todo.
