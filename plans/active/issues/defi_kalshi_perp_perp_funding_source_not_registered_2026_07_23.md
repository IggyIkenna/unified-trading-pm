---
doc_type: issue
title: KALSHI_PERP perp_funding manifest emits fail — source='kalshi_perp' not registered for (defi, perp_funding)
summary: >-
  Discovered live during a scoped defi-rebuild pass for day=2026-07-22: every KALSHI_PERP perp_funding object
  (KXBCHPERP/KXBTCPERP/KXDOGEPERP/KXETHPERP/KXHYPEPERP) fails manifest emission with "source='kalshi_perp' which is not
  a registered source for asset_group='defi' data_type='perp_funding'. Allowed: ['hyperliquid']" — the objects exist on
  GCS and are written under asset_group=defi, but SOURCE_PRIORITY[(defi, perp_funding)] only lists hyperliquid, so these
  rows never enter the manifest at all (silent, logged-and-skipped, not a crash).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [defi, kalshi-perp, source-priority, manifest, registry-gap]
related:
  [
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-23
author: unknown
last_updated: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineer
drift_direction: worsening-slowly
depends_on: []
resolved_by:
locked_by:
source: ["discovered live during defi_consolidated_closeout_2026_07_18.md's manifest rebuild work, 2026-07-23"]
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_kalshi_polymarket.py,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
  ]
---

# KALSHI_PERP perp_funding manifest emits fail — source not registered

## What was measured (live, during a scoped defi-rebuild for day=2026-07-22)

`rebuild_defi_manifest` logged, for every KALSHI_PERP perp_funding object on that day:

```
manifest emit failed for raw_tick_data/by_date/day=2026-07-22/pipeline_mode=batch_kalshi_perp/asset_group=defi/
venue=KALSHI_PERP/chain=KALSHI_PERP/instrument_type=perpetual/data_type=perp_funding/KXBCHPERP.parquet:
Manifest write passed source='kalshi_perp' which is not a registered source for asset_group='defi'
data_type='perp_funding'. Allowed (UAC SOURCE_PRIORITY batch sources + live/replay vendors): ['hyperliquid'].
```

Same failure for KXBTCPERP, KXDOGEPERP, KXETHPERP, KXHYPEPERP — every KALSHI_PERP market symbol seen that day. The
objects themselves ARE written to GCS (confirmed present at the cited path); only the MANIFEST ROW never gets created,
so this data is invisible to any manifest-driven reader/coverage calculation.

## Likely relationship to the existing census finding

This directly parallels the `KALSHI_PERP`/`POLYMARKET_PERP` asset_group-classification ambiguity already documented in
`distinct_values_noncanonical_audit_2026_07_20.md` (KALSHI_PERP appears under BOTH defi and cefi in different contexts,
with an operator KEEP ruling preserving existing stamps rather than reclassifying). This writer stamps KALSHI_PERP's
perp_funding capture as `asset_group=defi` with `source=kalshi_perp`, but
`unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY[("defi", "perp_funding")]` only lists
`hyperliquid` as a registered source — so either (a) `kalshi_perp` needs adding to that SOURCE_PRIORITY entry, or (b)
KALSHI_PERP's perp_funding capture should be stamped under a different asset_group entirely (matching whatever the
eventual resolution of the broader classification question turns out to be). Not resolved here — this doc records the
concrete, currently-failing symptom; the classification question is the census audit's to rule on.

## Not yet done

- **UPDATED 2026-07-28 (slot-16) — corpus-wide scope now measured, replacing the single-day framing.** Scanned GCS under
  the scoped prefix `raw_tick_data/by_date/day=<D>/pipeline_mode=batch_kalshi_perp/asset_group=defi/venue=KALSHI_PERP/`
  (single-prefix listing per day, never a whole-corpus walk). A bucket-root delimiter-descent first confirmed exactly
  2,400 `day=` partitions total (2020-01-01..2026-07-27); the per-day scoped scan below was bounded to that window,
  live-verified empty on both edges (back through 2026-01-01, forward through 2026-07-27) rather than assumed:
  - **Full affected window: 2026-05-29 through 2026-07-25** (55 of 58 calendar days in that span carry >=1 KALSHI_PERP
    defi-labeled object). Confirmed **zero** objects before 2026-05-29 and **zero** from 2026-07-26 onward — the latter
    confirms the `market-tick-data-service@2aa23de5` cefi-reroute fix (already shipped earlier in this same batch1 plan)
    took effect for new writes: no further DEFI-asset_group KALSHI_PERP objects appear after it landed.
  - **13 distinct real perp symbols observed, not 5** (this doc's original single-day spot-check only saw the 5 that
    happened to exist on 2026-07-22). Coverage grew in 3 steps: `KXBTCPERP/KXETHPERP/KXSOLPERP/KXXRPPERP` from
    2026-06-03; `+KXHYPEPERP` from 2026-06-08; `+KXBCHPERP/KXDOGEPERP/KXKSHIBPERP/KXLINKPERP/KXLTCPERP/KXSUIPERP` from
    2026-06-09 (11 symbols, steady through 2026-06-23); `+KXNEARPERP/KXZECPERP` from 2026-06-24 (13 symbols, steady
    through the last active day 2026-07-25). 2026-05-29 through 2026-06-02 carry no real-symbol data yet (see marker
    finding below).
  - **TOTAL (day, symbol) GCS-present instances: 567** across the 13 real symbols.
  - **3 zero-object gap days inside the otherwise-daily-cadence active window**: 2026-07-17, 2026-07-20, 2026-07-21 —
    not root-caused here (read-only audit scope); tracked as a new follow-up below.
  - **Secondary finding — non-symbol marker objects**: a `_migrated_kalshi_perp_<UTC-timestamp>.parquet` object (one per
    day, e.g. `_migrated_kalshi_perp_20260714182652`) appears under the SAME scoped venue prefix every day from
    2026-05-29 through 2026-07-16 (57 total instances), then stops appearing entirely from 2026-07-17 onward. Not a real
    perp market symbol — reads as a one-off migration/backfill script's marker artifact left in the live data path. Not
    root-caused here; tracked as a new follow-up below.
  - **Manifest-side cross-check**: streamed the full DEFI availability manifest (26,978,131 rows,
    `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, never materialized whole) and
    confirmed **zero** rows with `venue=KALSHI_PERP` (any `data_type`) — every one of the 567 GCS-present (day, symbol)
    instances above is manifest-absent, with no exceptions. (The 4 stale pre-existing KALSHI_PERP/ POLYMARKET_PERP
    manifest rows this same batch1 plan's `remove_kalshi_polymarket_defi_manifest_rows_2026_07_26.py` cleanup removed
    are confirmed gone via this same live read.)
- Decide the registry fix: add `kalshi_perp` to `SOURCE_PRIORITY[("defi", "perp_funding")]`, or confirm the asset_group
  should be something else for this venue/data_type pair. **Effectively already decided for NEW writes**: the routing
  fix shipped earlier in this batch1 plan (`market-tick-data-service@2aa23de5`) reroutes captures to `asset_group=cefi`
  instead (option b) — confirmed live above (zero new defi-labeled objects after 2026-07-26). **RULED 2026-08-06
  (operator, chat): option (b)** — re-emit the 567 already-written, still-GCS-present, still-manifest-absent
  2026-05-29..2026-07-25 DEFI objects into the CEFI manifest to match the now-shipped routing fix (not backfilled into
  DEFI as-is, not accepted as a historical gap). See the execution todo below.
- Once decided, ship the fix and re-run affected-day manifest rebuilds to backfill the missing rows.

## Follow-up (filed 2026-07-28, from the corpus-wide scope audit above)

- [x] ✅ [DIAG] P2. **CLOSED 2026-08-05 (slot-4, data_engineering, batch-6 todo 10)** — Root-cause of the 3 zero-object
      gap days inside the KALSHI_PERP defi capture window (2026-07-17, 2026-07-20, 2026-07-21). **Verdict: Transient
      upstream API condition.** The handler's `_collect_kalshi_perp` calls the Kalshi API
      `GET /margin/markets?status=active` — when this returns zero tickers, the handler returns 0 without writing any
      GCS object. The scattered, non-sequential pattern (Saturday/Monday/Tuesday with data on Sunday) is consistent with
      a transient upstream condition, not a code bug. The gap-day backfill is a recovery item, not a code fix. Full
      analysis in `defi_satellite_ao_dispatch_batch6_2026_07_30.md` Progress Log (2026-08-05, slot-4).
- [x] ✅ [DIAG] P2. **CLOSED 2026-08-05 (slot-4, data_engineering, batch-6 todo 10)** — Root-cause of the daily
      `_migrated_kalshi_perp_<timestamp>.parquet` marker objects (2026-05-29 through 2026-07-16, 57 instances, then
      stops). **Verdict: Inert R3 migration artifacts — renamed empty bundled parquet files from the pre-per-instrument-
      sharding era.** The R3 migration renamed bundled `kalshi_perp_{ts}.parquet` files to `_migrated_{stem}.parquet`
      (safety-rename convention, never deletes). Markers stop on 2026-07-17 because per-instrument sharding was deployed
      from 2026-07-18 onward. All markers are 0-row empty parquet files — safe to delete via existing tooling. The
      abrupt stop is unrelated to the gap-day finding (the two phenomena share a trigger date but have different root
      causes). Full analysis in `defi_satellite_ao_dispatch_batch6_2026_07_30.md` Progress Log (2026-08-05, slot-4).
- [ ] [DATA] P1. **Execute the 2026-08-06 operator ruling (option b, above).** Re-emit all 567 GCS-present/
      manifest-absent KALSHI_PERP/POLYMARKET_PERP perp_funding (day, symbol) instances (2026-05-29..2026-07-25) into the
      CEFI manifest under the now-shipped cefi-routing classification — NOT the DEFI manifest, and NOT left as a gap.
      This is `defi_satellite_ao_dispatch_batch2_2026_07_26.md` todo `-011`'s own blocked prerequisite
      (`defi_kalshi_perp_perp_funding_recovery_operator_decision`) — once this re-emit ships and is verified
      (`quality-gates.sh` green, manifest row count == 567 under `asset_group=cefi`), flip that prerequisite so `-011`
      unparks. Repo: market-tick-data-service (manifest rebuild), unified-trading-pm (unpark). **Duplicate-claim note
      (2026-08-07): `defi_satellite_ao_dispatch_batch2_2026_07_26.md` line ~306 already carries an open `[DATA] P2` todo
      for this exact re-emit (same 567-row scope, same source-doc citation, status: active). Do NOT reclassify this
      checkbox independently — it would open a second dispatch path for the identical fix. Close both together once
      either ships.**

## Codex SSOTs

- `/codex/02-data/defi-canonical-naming-ssot.md` (KALSHI_PERP classification)
- UAC `unified_api_contracts/canonical/crosscutting/source_priority.py` (`SOURCE_PRIORITY` registry)

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - the doc's central open item is a prose-only (a)/(b)/(c)
  operator-design decision on 567 already-written manifest-absent objects; the 2 checkbox DIAGs are bounded but
  secondary
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): KEEP-NA valid (2026-07-30 verdict re-
  affirmed) — re-read end to end; content unchanged since that verdict (context-scout backfill only). The doc's central
  open item is still the prose-only (a)/(b)/(c) operator/design decision on the 567 already-written, manifest- absent
  2026-05-29..2026-07-25 DEFI objects (backfill into DEFI as-is / re-emit under CEFI to match the shipped `@2aa23de5`
  reroute / accept as a historical gap). The 2 `[DIAG] P2` checkboxes are bounded but secondary, and the same gap-day +
  `_migrated_kalshi_perp_*` forensics are already claimed by an active planning plan
  (`defi_satellite_ao_dispatch_batch6_2026_07_30.md:310`), so flipping this doc would dispatch a duplicate.
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) — still accurate against the doc's central open
  (a)/(b)/(c) operator decision and the 2 secondary `[DIAG]` todos.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA-STALE (already-duplicated) — the 2
  `[DIAG] P2` checkboxes are extracted verbatim (combined into one todo) in the ACTIVE `assigned_vm: planning` doc
  `defi_satellite_ao_dispatch_batch6_2026_07_30.md:310` (still open as of today), which explicitly cites this issue doc
  as its source; the checkboxes were never flipped to point to that extraction. Fixed the citation on both checkboxes
  above (not reclassified — flipping `assigned_vm` here would dispatch a duplicate). The doc's central prose-only
  (a)/(b)/(c) operator-design decision on the 567 already-written manifest-absent objects remains genuine NA judgment
  work, unchanged. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA, stale item closed — re-read end to end (2 open items at
  entry). The `[OPERATOR] P2` "Decide the (a)/(b)/(c) disposition" checkbox below is now stale: the operator RULED
  2026-08-06 (option b, see line 111-114 above), and the corresponding `[DATA] P1` execution todo above already
  operationalizes that ruling — closed by citation, not reclassified. Separately, conflict-checked the `[DATA] P1`
  execution todo against the active corpus: `defi_satellite_ao_dispatch_batch2_2026_07_26.md` (status: active) already
  carries an open todo (~line 306) claiming the identical 567-row re-emit, citing this same source doc — a genuine
  duplicate claim, not a reclassification opportunity (flipping this doc's `assigned_vm` would create a second dispatch
  path for the same fix). Added a duplicate-claim note inline on that checkbox. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — added
  `/plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md`, the doc holding the blocked-prerequisite todo
  (`-011`) the open `[DATA] P1` re-emit todo unblocks once shipped.
- **round11-sweep 2026-08-09** (defi tranche, satellite-extraction + RECLASSIFY re-check): re-read end to end (1 open
  `[DATA] P1` re-emit todo at entry). Re-verified the duplicate-claim citation live: `defi_satellite_ao_dispatch_batch2_2026_07_26.md`
  line ~307 still carries the identical open `[DATA] P2` re-emit todo (unchecked, same 567-row scope, explicit `Source:`
  citation to this doc) — not stale, genuinely still in-flight there. Checked whole-doc RECLASSIFY against every
  accumulated round11 precedent (IAM self-service, D16 all-repos, S5.1 tiering,
  plan-destination-defaults-AO-dispatched, escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM
  secret + 5 Slack webhooks now existing) — none apply; this doc's sole open item is a pure duplicate of an
  already-dispatched `assigned_vm: planning` todo, not a fresh RECLASSIFY signal. No satellite-extraction candidate
  (flipping this doc's `assigned_vm` would open a second dispatch path for the identical fix, exactly the risk the
  doc's own text warns against). Doc stays `assigned_vm: NA` (KEEP-NA-STALE-DUPLICATE, round11).

## Follow-ups

- [x] ✅ [OPERATOR] P2. **CLOSED 2026-08-07 (na-eligibility-audit, stale — decision already made).** Decide the
      (a)/(b)/(c) disposition of the 567 already-written, still-GCS-present, still-manifest-absent
      2026-05-29..2026-07-25 KALSHI_PERP defi perp_funding objects — **RULED 2026-08-06 (operator, chat): option (b)**,
      see line 111-114 above. Execution tracked in the `[DATA] P1` todo above (and duplicated in
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s own open todo, ~line 306).

> **2026-08-06 archive-candidate audit**: Doc's central item is prose-only: 'Still open: whether the 567
> already-written, still-GCS-present, still-manifest-absent 2026-05-29..2026-07-25 DEFI objects above should be (a)
> backfilled into the DEFI manifest as-is, (b) migrated/re-emitted into the CEFI manifest... or (c) left as an accepted
> historical gap — an operator/design decision, not resolved here' — never converted to a `- [ ]` todo; the 2
> `[DIAG] P2` checkboxes are closed but secondary (na-eligibility-audit 2026-08-02/04 re-affirms the (a)/(b)/(c)
> decision is genuine NA judgment work).
