---
doc_type: issue
title: 3 new data-completeness findings surfaced while fixing coverage_floor_registries_no_cross_propagation-002
summary: >-
  Small standalone note (disk-full incident prevented editing the parent issue doc directly at write time — see
  coverage_floor_registries_no_cross_propagation_2026_07_17.md's [DATA] P1 status note for the full context). Fold these
  3 todos into that doc once disk recovers and delete this file.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [coverage-floor, backfill-gap, data-completeness]
related:
  [
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-27"
author: unknown
last_updated: "2026-07-27"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
source:
  "slot-6, 2026-07-27, coverage_floor_registries_no_cross_propagation-002, surfaced while manifest-probing 8 CeFi venue
  coverage floors"
resolved_by:
locked_by:
locked_since:
depends_on: []
archive_exempt: true
context_scope:
  [
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    unified-api-contracts/unified_api_contracts/registry/venue_mapping.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
  ]
---

# 3 new backfill/data-completeness findings

## Todos

- [x] [DATA] P1. **DONE 2026-07-27 (slot-15)** — **HYPERLIQUID never-attempted backfill gap, root-caused + backfill
      confirmed in flight.** Re-verified: `market-data-tick-cefi-prd-central-element-323112` has ZERO manifest rows of
      ANY `capture_status` (not even `expected_unattempted`) for HYPERLIQUID across ALL data_types (`book_snapshot_5`,
      `derivative_ticker`, `trades`) in the entire `2023-04-15..2023-12-31` window — confirmed via a bounded,
      column-projected manifest read (no VM, no corpus walk), not just the originally-cited `book_snapshot_5` slice.
      **Root cause: never scheduled, NOT an adapter/source gap.** The HYPERLIQUID S3 adapter
      (`market_tick_data_service/adapters/hyperliquid_s3.py`) hardcodes `S3_L2_BOOK_START = 2023-04-15` — verified real,
      live vendor data via a direct requester-pays S3 probe (`hyperliquid_s3_archives_dead_upstream_2026_07_13.md`) — so
      the source genuinely has data here; nobody ever dispatched a backfill job that enumerated these shards (a genuine
      source gap or adapter defect would still leave `attempted_failed`/`expected_unattempted` rows; total absence of
      ANY manifest row means the shards were never even in scope for a run). **Backfill: found ALREADY IN FLIGHT, not
      launched by me.** `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` already documents
      `HYPERLIQUID: 2023-01-01 → today` as its intended coverage. A DRY_RUN confirmed a scoped re-run
      (`YEARS=2023 OVERRIDE_START_DATE=2023-04-15 OVERRIDE_END_DATE=2023-12-31 DATA_TYPES="book_snapshot_5;derivative_ticker"`,
      `trades` excluded — no real trades source exists before 2025-03-22 per `S3_TRADES_START`) would correctly target
      this exact gap, so I launched it for real (5 SPOT shards, `SHARD_DAYS=60`). **Before those shards did any work,
      discovered a pre-existing VM `cefi-hyperliquid-2023-20260727-071055` (launched 2026-07-27T00:10:58-07:00, ~47 min
      before mine) already RUNNING with a SUPERSET scope** (`VM_START_DATE=2023-01-01`, `VM_END_DATE=2023-12-31`,
      `VM_DATA_TYPES=trades;book_snapshot_5;derivative_ticker`, `VM_VENUE=HYPERLIQUID`) — almost certainly a concurrent
      AO worker dispatched the same underlying finding (this doc's own summary notes it was surfaced from
      `coverage_floor_registries_no_cross_propagation-002`, slot-6, which independently found the same gap while fixing
      the coverage-floor registries). **Deleted my 5 redundant STAGING VMs immediately**
      (`gcloud compute instances delete`, confirmed clean — none had started real work, no wasted spend beyond ~1 min of
      boot) rather than duplicate in-flight work / risk a shard-write race. Verified the pre-existing VM is genuinely
      healthy, not zombied: `RUNNING` status, serial console shows continuous minute-cadence activity through 07:58Z
      (~15 min before my check). **Not yet independently confirmed via captured manifest rows** — the consolidated
      `_index/availability_index.parquet` still shows 0 rows for this window as of this check, which is EXPECTED
      (manifest consolidation runs on its own cadence, lagging behind per-VM-shard writes; `MANIFEST_PER_VM_SHARDS=true`
      is set on that VM) and is NOT evidence the backfill is stalled. **Residual**: re-verify captured rows for this
      window once the VM completes (a few hours, VM-scale — not re-dispatched as a separate todo here since it is a
      natural follow-up check on already-in-flight work, not new work).
- [x] ✅ [DATA] P2. **DONE 2026-08-02 (slot-9)** — **DERIBIT sparse/partial 2019 historical backfill — root-caused +
      code fix shipped.** Confirmed via a bounded, column-projected manifest read
      (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, no corpus walk) of
      DERIBIT/`trades` 2019-05-08..2019-12-31 (238 calendar days): 84 days carry real `capture_status=captured` rows
      (`source=tardis`, `instrument_count` 3,800-193,593/day — genuine partial historical data, not placeholders); the
      other 154 days have NO manifest row of ANY status (never attempted, not a failure). **Answer: YES, worth
      completing, and more is available than even the 2019-05-08 floor implies.** Queried Tardis's own exchange metadata
      (`GET https://api.tardis.dev/v1/exchanges/deribit`, public, read-only): `BTC-PERPETUAL`/`ETH-PERPETUAL`
      `trades`/`book_snapshot_5`/`derivative_ticker`/etc. are ALL `availableSince: 2019-03-30` — i.e. Tardis has dense
      vendor-side data 5+ weeks before our registry floor (2019-05-08) and 9+ months before `book_snapshot_5`/
      `derivative_ticker`'s clean 2020-01-01 start. **Root cause of why 2019 was never backfilled**: the standard
      sharded-backfill launcher (`deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh`)'s `_venue_years()`
      never included `"2019"` for DERIBIT (only `2020..2026`), even after the registry floor
      (`venue_mapping.py`/`coverage_starts.py`) was corrected to 2019-05-08 on 2026-07-27 — so no full-year sharded run
      has EVER targeted 2019; the existing sparse 84-day rows are the residue of some earlier ad-hoc/pre-launcher
      process, not this launcher's output. **Fix shipped**: added `"2019"` to DERIBIT's year list in `_venue_years()`,
      and generalized the `START_DATE` override (previously 2026-only) to non-2026 years, so a future launch can start
      exactly at `2019-03-30` (Tardis's real `availableSince`) instead of a year-granular launch wasting ~89 days
      (2019-01-01..2019-03-29) where the vendor has zero data. **Not launched as a live VM in this task** — the Tardis
      fleet's hard 1-concurrent-VM cap was clear at investigation time (verified via `gcloud compute instances list`,
      zero Tardis-consuming VMs running), but a DERIBIT 2019 heavy+light launch is 2 buckets (heavy=trades+
      book_snapshot_5, light=derivative_ticker+options_chain+futures_chain per `DATA_LIGHT_DERIBIT`) that must be
      sequenced one-at-a-time under the cap, plus real multi-day GCP/Tardis cost — out of scope for this investigation
      task to launch unilaterally. **Follow-up** (not re-dispatched as a separate todo — a natural next step on
      already-shipped code, same class as the HYPERLIQUID item above): dispatch
      `YEARS=2019 START_DATE=2019-03-30 LAUNCH_GROUPS=heavy VENUES=DERIBIT bash scripts/vm/launch-cefi-sharded-backfill.sh`
      (then `LAUNCH_GROUPS=light` once heavy completes/frees the Tardis slot). Evidence: `deployment-service@4fff44f`
      (quickmerge-landed, verified ancestor of `origin/live-defi-rollout`). (repo: market-tick-data-service backfill /
      deployment-service)
- [x] ✅ [DATA] P3. **BINANCE-DELIVERY — investigated 2026-08-05 (slot-5).** NOT a dead/never-implemented shard — the
      code is fully wired (venue_mapping.py, symbol_rules.py, Tardis adapter) and Tardis has real data (availableSince
      2020-06-16, 18 perpetuals + dated futures). But the venue is a ZOMBIE: deliberately removed from MVP scope
      (operator decision #3, 2026-06-27, mvp_scope.py v10), so the instrument catalog returns zero instruments. The
      forward/cron pipeline STILL attempts it daily (704 manifest rows: 669 attempted_failed + 35 empty_confirmed,
      2026-05-01..2026-08-04, 6 data_types, ALL with instrument_count=0.0) — the venue is in VENUES_BY_ASSET_GROUP so
      it's iterated, but catalog-tagging is MVP-gated so every shard fails. The backfill launcher
      (launch-cefi-sharded-backfill.sh) does NOT include it in default VENUES or _venue_years(), so no backfill has ever
      targeted it. **Resolution options: (1) remove from VENUES_BY_ASSET_GROUP["cefi"] to stop the zombie** (cleanest —
      keeps the code wiring for if/when COIN-M delivery becomes MVP); (2) operator re-adds to MVP scope + tags
      instruments (reverses #3); (3) do nothing (not recommended — 704 wasted rows and Tardis API quota burn for a venue
      nobody consumes). The venue_mapping.py coverage_start of 2020-01-01 slightly overstates vs Tardis's measured
      2020-06-16 but is cosmetic for a non-MVP venue. (repo: market-tick-data-service / unified-api-contracts)

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **slot-9 2026-08-02**: closed the DERIBIT P2 todo — root-caused (launcher's `_venue_years()` never had 2019 for
  DERIBIT) + fix shipped (`deployment-service@4fff44f`) + synced the duplicate todo in
  `coverage_floor_registries_no_cross_propagation_2026_07_17.md`. 1 of 3 todos in this doc now remain open (P3
  BINANCE-DELIVERY); the doc's own header note (fold into the parent doc + delete once disk recovers) is still
  outstanding but out of scope for this task.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — the 2 closed todos' targets (hyperliquid_s3.py,
  cefi_consolidated_closeout) dropped since only the open BINANCE-DELIVERY P3 investigation remains; swapped in
  `symbol_rules.py` (where BINANCE-DELIVERY is coded) and the sharded-backfill launcher (the DERIBIT fix's precedent the
  next launch would follow).
- **slot-5 2026-08-05**: closed the BINANCE-DELIVERY P3 investigation. Root cause: venue is a zombie — fully wired code
  (venue_mapping, symbol_rules, Tardis adapter), real Tardis source data exists (binance-delivery, availableSince
  2020-06-16, 18 perps + dated futures), but deliberately removed from MVP scope (operator decision #3, 2026-06-27,
  mvp_scope.py v10). The venue IS in VENUES_BY_ASSET_GROUP["cefi"] so the forward/cron pipeline attempts it daily, but
  catalog-tagging is MVP-gated → zero instruments → 704 attempted_failed/empty_confirmed rows (2026-05-01..2026-08-04,
  all with instrument_count=0.0). The sharded backfill launcher does NOT include it. Resolution: remove from
  VENUES_BY_ASSET_GROUP["cefi"] to stop the zombie (cleanest — keeps code wiring for future); OR operator re-adds to MVP
  (reverses #3). All 3 todos in this doc now closed; doc archival eligible but header note says fold into parent doc +
  delete — out of scope for this task. Evidence: manifest query (bounded column-projected read, features-service venv),
  Tardis API probe, code audit of venue_mapping.py, symbol_rules.py, mvp_scope.py v10, launch-cefi-sharded-backfill.sh.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (4 entries), unchanged — all 3 open Follow-ups
  (HYPERLIQUID row re-verify, DERIBIT 2019 dispatch, BINANCE-DELIVERY zombie cleanup) still map to this same 4-entry set
  (parent doc + the 2 registry/orchestrator files + the sharded-backfill launcher).
- **slot-7 2026-08-07**: dispatched DERIBIT 2019 heavy backfill follow-up (this task). Tardis fleet clear (0 running VMs
  via `tardis_running_vm_count`). Launched `cefi-deribit-2019-heavy-20260807-123219`
  (`YEARS=2019 START_DATE=2019-03-30 LAUNCH_GROUPS=heavy VENUES=DERIBIT`); VM RUNNING 34.146.248.9 zone
  asia-northeast1-c; VM_TARDIS_CONSUMER=1; covers trades;book_snapshot_5 2019-03-30..2019-12-31. Added new follow-up for
  LAUNCH_GROUPS=light dispatch once heavy finishes.
- **slot-13 2026-08-07**: closed HYPERLIQUID re-verify P2 follow-up. Bounded column-projected manifest read of
  `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` confirms 45,261 rows for
  HYPERLIQUID 2023-04-15..2023-12-31: book_snapshot_5 (8,917 captured/6,170 empty_confirmed), derivative_ticker (9,194
  captured/5,885 empty_confirmed/8 attempted_failed), trades (15,087 empty_confirmed as expected per
  S3_TRADES_START=2025-03-22). 261 calendar days now carry capture_status=captured. Backfill VM completed successfully.
- **slot-9 2026-08-07**: dispatched DERIBIT 2019 light backfill. Heavy VM `cefi-deribit-2019-heavy-20260807-123219`
  confirmed gone from fleet (completed). Tardis slot free (0 VMs with VM_TARDIS_CONSUMER=1 metadata). Launched
  `cefi-deribit-2019-light-20260807-194407` (`YEARS=2019 START_DATE=2019-03-30 LAUNCH_GROUPS=light VENUES=DERIBIT`); VM
  RUNNING at 35.194.123.82 (asia-northeast1-c). Covers derivative_ticker;options_chain;futures_chain
  2019-03-30..2019-12-31. Machine n2-highmem-16 (128GB, registry floor). All follow-up todos in this doc now closed.
- **slot-32 2026-08-10**: closed the BINANCE-DELIVERY P3 zombie follow-up — deregistered from
  `VENUES_BY_ASSET_GROUP["cefi"]` + `tardis_to_venue`/`all_tardis_exchanges` + `VENUE_DATA_TYPE_CAPABILITIES`
  (`unified-api-contracts@56db28e6`, QG green, 12,637 passed). Audit note: the MTDS daily forward-poll
  (launch-cefi-forward-poll.sh → `get_venues_for_asset_groups(["CEFI"])`) derives its venue set from
  `tardis_to_venue.values()`, NOT `VENUES_BY_ASSET_GROUP` — so the group removal alone (the option-1 letter) would not
  have stopped the 704 wasted rows/day; the tardis_to_venue removal was required (bare-OKX precedent, 5,225-row incident
  2026-08-04/05). Known residual (out of scope, noted for the doc's archival flow): instruments-service
  `scripts/enumerate_expected_universe.py` `_CEFI_EXPECTED_UNIVERSE_EXCLUDED_VENUES` comment block (~line 1113) says
  BINANCE-DELIVERY "stays REGISTERED in UAC VENUES_BY_ASSET_GROUP["cefi"]" — now stale post-deregistration (the
  exclusion set itself is unchanged + still correct as a guard). All todos in this doc now closed.
- **archive_exempt (2026-08-10, slot-32)**: the 0-open-todos state is TERMINAL — all 3 todos + all 3 follow-ups closed.
  `archive_exempt: true` here is the hygiene-gate escape hatch for the flip commit ONLY: archival (status → resolved +
  `git mv` to plans/archive/2026_08/issues/ + referrer fixes) follows in the immediately next commit, per the
  flip-then-mv discipline (never combine the checkbox flip with a git mv in ONE commit — see
  /codex/12-agent-workflow/plan-completion-and-archival-discipline.md). The header's fold-into-parent-and-delete note is
  superseded by direct archival (the parent doc already carries synced copies of all todo text).

## Follow-ups

- [x] ✅ [DATA] P2. Re-verify HYPERLIQUID captured rows for the 2023-04-15..2023-12-31 window — DONE 2026-08-07
      (slot-13). Manifest now shows 45,261 rows for HYPERLIQUID 2023-04-15..2023-12-31: book_snapshot_5 (8,917
      captured + 6,170 empty_confirmed), derivative_ticker (9,194 captured + 5,885 empty_confirmed + 8
      attempted_failed), trades (15,087 empty_confirmed — expected, S3_TRADES_START=2025-03-22). 261 distinct calendar
      days with capture_status=captured. Backfill confirmed complete.
- [x] ✅ [DATA] P2. **DONE 2026-08-07 (slot-7)** — Dispatched DERIBIT 2019 heavy backfill. Tardis fleet was clear (0
      running VMs confirmed via concurrency guard). Launched `cefi-deribit-2019-heavy-20260807-123219` with
      `YEARS=2019 START_DATE=2019-03-30 LAUNCH_GROUPS=heavy VENUES=DERIBIT`; VM RUNNING at 34.146.248.9
      (asia-northeast1-c). Covers `trades;book_snapshot_5` 2019-03-30..2019-12-31. VM_TARDIS_CONSUMER=1 stamped; shuts
      down on completion. Follow-up: dispatch LAUNCH_GROUPS=light (derivative_ticker;options_chain;futures_chain) once
      heavy completes and frees the Tardis slot.
- [x] ✅ [DATA] P2. **DONE 2026-08-07 (slot-9)** — Dispatched DERIBIT 2019 light backfill. Heavy VM
      `cefi-deribit-2019-heavy-20260807-123219` confirmed completed (no longer in fleet). Tardis slot free (0
      Tardis-consuming VMs via metadata filter VM_TARDIS_CONSUMER=1). Launched `cefi-deribit-2019-light-20260807-194407`
      with `YEARS=2019 START_DATE=2019-03-30 LAUNCH_GROUPS=light     VENUES=DERIBIT`; VM RUNNING at 35.194.123.82
      (asia-northeast1-c). Covers `derivative_ticker;options_chain;futures_chain` 2019-03-30..2019-12-31. Machine
      n2-highmem-16 (128GB, registry floor). VM_TARDIS_CONSUMER=1 stamped; shuts down on completion.
- [x] ✅ [INFRA] P3. **DONE 2026-08-10 (slot-32)** — BINANCE-DELIVERY deregistered from the cefi venue axis: removed
      from `VENUES_BY_ASSET_GROUP["cefi"]` (market_data_categories.py) AND from `tardis_to_venue`/`all_tardis_exchanges`
      (venue_mapping.py) — the audit showed the daily forward-poll derives its venue list from
      `tardis_to_venue.values()`, so the group removal alone would NOT have stopped the attempts (same class as the
      bare-OKX 5,225-row incident, 2026-08-04/05); `VENUE_DATA_TYPE_CAPABILITIES["BINANCE-DELIVERY"]` also removed (the
      cross-repo invariant `test_cefi_registry_expected_universe_invariant.py` demands a capability block for a
      never-declared venue be deleted, POLYGON precedent). Routing/adapter wiring kept intact for a future COIN-M MVP
      re-enable: `venue_instrument_type_to_tardis` (PERPETUAL/FUTURE → binance-delivery), `VENUE_TO_ADAPTER_KEY`,
      `symbol_rules.py`, `venue_start_dates`/`coverage_starts` (BARE_KEY mapping). Evidence:
      `unified-api-contracts@56db28e6` (quickmerge-landed, QG green 12,637 passed, verified ancestor of
      `origin/live-defi-rollout`; sentinel `.qg_last_passed_sha=56db28e6`). (repo: unified-api-contracts)

> **2026-08-06 archive-candidate audit**: All 3 checkboxes [x] but each describes a prose-only follow-up explicitly 'not
> re-dispatched as a separate todo': HYPERLIQUID post-backfill row re-verify, DERIBIT YEARS=2019 backfill launch (code
> fixed but never launched), and BINANCE-DELIVERY zombie still unresolved (704 wasted rows/day) — plus the header
> fold-into-parent-and-delete instruction never executed.
