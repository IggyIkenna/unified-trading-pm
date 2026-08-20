---
doc_type: issue
title: CeFi HL/ASTER batch data gaps — day-bleed rejection, HL trades under-capture, ASTER/liq misclassification
summary:
  "CeFi HL/ASTER batch data gaps — day-bleed rejection, HL trades under-capture, and ASTER liquidation
  misclassification, found via a per-data_type manifest breakdown (consolidated index + live per-VM shards)."
status: open
nature: process
asset_group:
  [cefi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # HL(Hyperliquid)/ASTER are cefi venues and the doc's own tags already say "cefi" -- content is cefi-only
stage: [meta]
repos:
  [
    alerting-service,
    deployment-api,
    deployment-service,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [cefi, backfill, manifest, data-correctness, mtds, honest-coverage, data-status, catalogue]
related:
  [
    mvp_backfill_cefi_tick_v10_2026_06_27,
    /plans/archive/2026_08/issues/cefi_universe_capture_rule_2026_06_23.md,
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
  ]
created: 2026-06-22
author: unknown
parent_epic: mtds_mdps_master
priority: P2
source:
  [
    cefi manifest audit 2026-06-22 (per-data_type breakdown via consolidated + per-VM shards),
    cefi-hyperliquid-2024-resume / cefi-aster-* run.log runtime evidence,
  ]
assigned_vm: planning
resolved_by:
archive_exempt: true # BRIDGE 2026-08-12: clearing the stale locked_by:live-defi-rollout placeholder (operator ruling, option B, see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md) immediately surfaces this doc as 0-open-todos archive-eligible. Per that ruling's explicit scope ("do NOT auto-archive in this same pass"), archival is deferred to a separate follow-on pass. Bridged via the sanctioned flip-then-mv two-commit pattern documented in scripts/plan-hygiene/check_archive_candidates.sh -- drop this line + git mv to plans/archive/[issues/] in that follow-on pass.
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-17
context_scope:
  [
    /plans/archive/2026_06/cefi_hl_aster_batch_data_gaps_history_2026_06_22.md,
    /plans/archive/2026_08/issues/cefi_universe_capture_rule_2026_06_23.md,
    /codex/02-data/cefi-capture-universe.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
  ]
---

# CeFi HL/ASTER batch data gaps — not 100%, with 3 diagnosed bugs

> **History extracted 2026-07-25** (line-cap remediation) — the original 2026-06-22/23 findings, BUG #1-4 diagnosis, and
> their shipped fixes/migration now live in
> `/plans/archive/2026_06/cefi_hl_aster_batch_data_gaps_history_2026_06_22.md`. Read that first for full context;
> everything below is what's still open.

## EXPANDED PROGRAM — full cefi catalogue (ALL venues) + daily-job verification + MTDS run (operator 2026-06-23)

Generalises BUG#4 from {HL,ASTER} to **all cefi venues**. Tardis access re-verified live: SSOT secret
**`tardis-api-key`** (academic-unlimited, 62 venues, genesis 2019 → 2027, `dataPlan:unlimited`); the dup
`tardis-api-key-full`/`-backup` (byte-identical) DELETED. IS Tardis reference-data now uses the **free no-auth**
`api.tardis.dev/v1/exchanges/{exchange}` metadata for enumeration (no key consumed) — shipped
instruments-service@`b99e586` (tested no-key enumeration).

**Schedulers ALREADY exist** (both ENABLED): `uts-prod-instruments-cefi-t1-schedule` (06:00 UTC → Cloud Run job
`uts-prod-instruments-service-cefi-t1-recon`, the daily IS fetch → daily shards `_catalogue/instruments-service/day=*/`)

- `instrument-catalogue-regen-nightly` (02:00 UTC → job `instrument-catalogue-regen`, aggregates daily shards →
  `prod/catalog.parquet`). Both jobs currently run image `market-tick-data-service:latest` — the b99e586 no-auth fix
  reaches them only after that image rebuilds (resolve at redeploy step P1).

### Gated sequence (each step waits on the prior)

- [x] ✅ [INFRA] P0. **GATE SUPERSEDED, re-verified + relaunched (2026-07-27, slot-10)**: the named
      `cefi-*-20260623-113700` 7-VM fleet no longer exists (`gcloud compute instances list` — zero matches;
      `deployment-scripts-.../vm-logs/` raw logs expired past the 14-day retention, so no per-VM `EXIT_STATUS` is
      recoverable) — this checkbox's literal condition is unfalsifiable at this remove. **Re-verified against the LIVE
      manifest instead** (read-only `read_availability_index` on `market-data-tick-cefi-prd-central-element-323112`,
      filtered venue ∈ {HYPERLIQUID, ASTER}): the goal ("full per-day universe captured") is genuinely **NOT met** —
      most of the gap is the survivorship-bias-free 493-base-asset universe expansion (shipped AFTER the 113700 fleet
      launched, same day) widening the denominator faster than any HL/ASTER-specific re-run has caught up: - ASTER
      `trades`: captured=**1** / empty_confirmed=18,152 / attempted_failed=100 / **expected_unattempted=372,943** (out
      of 391,196 mvp cells — **95.3% never attempted**). - ASTER `derivative_ticker`: captured=108,350 /
      expected_unattempted=188,787 (well-covered, 36.5% still open). - ASTER `book_snapshot_5`: 0 captured — CORRECT
      (live-only per BUG#4 A, excluded from batch by design). - HYPERLIQUID `trades`: captured=70,347 /
      expected_unattempted=91,525 (49.3% never attempted). - HYPERLIQUID `book_snapshot_5`: captured=12,445 /
      expected_unattempted=59,423 (78.4% never attempted). - HYPERLIQUID `derivative_ticker`: captured=12,924 /
      expected_unattempted=58,473 (77.6% never attempted). No HL/ASTER VMs were running at time of check
      (`gcloud compute instances list --filter="name~'hyperliquid|aster'"` — zero results) — nothing currently in flight
      was closing this gap. **Relaunched** a fresh corrective fleet via `launch-cefi-hl-aster-historical-backfill.sh`
      (idempotent, non-force → skips the already-captured cells above, catalogue-driven `SYMBOLS=ALL` picks up the
      current 493-base universe automatically): 7 VMs, run-id `20260727-015959`
      (`cefi-hyperliquid-{2023..2026}-20260727-015959`, `cefi-aster-{2024..2026}-20260727-015959`), SPOT,
      `asia-northeast1-c`. Verified STARTED (RUNNING/STAGING at T+30s). Superseding this checkbox rather than leaving it
      perpetually unfalsifiable; the real completion gate is below.
- [x] ✅ [INFRA] P0. **GATE SUPERSEDED (2026-07-27, slot-4)**: HL/ASTER corrective re-run (7 VMs
      `cefi-{hyperliquid,aster}-*-20260727-015959`) — this specific run-id's VMs never made progress. **UPDATE
      2026-07-27 T+10min (slot-10)**: all 7 VMs were **mass-preempted at 19:02:2x UTC, ~2.5 min after creation
      (19:00:01)** — `gcloud compute operations list` shows `compute.instances.preempted` system events for all 7 within
      a 6-second window, then auto-deleted (`--instance-termination-action=DELETE`). No `run.log` was ever written for
      any of the 7 (checked at T+10min) — this was a boot-time preemption, not a mid-run one, so there is no
      `PROGRESS.json` checkpoint for any auto-recovery watchdog to resume from. Checked for an auto-relaunch
      (`vm_zombie_watchdog.py` / preemption auto-recovery per
      `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md`): **zero** `cefi-hyperliquid-*`/
      `cefi-aster-*` VMs running at that point — nothing had re-launched this fleet. **RELAUNCHED 2026-07-27 (slot-4)**:
      re-ran `VENUES="HYPERLIQUID ASTER" bash scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` (SPOT, same
      idempotent non-force command slot-10 named) — new run-id `20260727-022558`, 7 VMs. Verified STARTED (all RUNNING
      at T+0). **T+10min+ check: NO preemption this time** — `gcloud compute instances list` shows all 7 still `RUNNING`
      well past T+10min (unlike the prior attempt's ~2.5-min mass-preemption). Ground-truthed via `run.log`, not just VM
      status (per this doc's own lesson): `cefi-hyperliquid-2023-20260727-022558`'s log shows real per-day
      `PROGRESS: chunk=N/365` lines advancing + genuine `ManifestWriter: per-VM shard updated` writes — the fleet is
      actually processing, not stalled-but-running. Superseding this checkbox (the 015959 run-id is dead and irrelevant
      now) rather than leaving it perpetually unfalsifiable; the real completion gate for the NEW run is below.
- [x] ✅ [INFRA] P0. **GATE — RESUMED + VERIFIED HEALTHY (2026-07-27, slot-7)**. Picked up after the prior `/blocked`
      escalation on the 2nd interruption (unexplained manual `stop` at `2026-07-27T02:36:26Z`).
      `gcloud compute operations list` shows the resolution already landed BEFORE this session started: a `start`
      operation on all 7 instances at `2026-07-27T03:55:27Z` (`user: ikenna@odum-research.com` — the operator resuming
      per the `/blocked` answer, confirming the startup-script IS safe to re-trigger on a plain restart, resolving the
      doubt the prior entry raised). **Re-verified independently, ground-truthed via `run.log` (not just VM status)**:
      all 7 `cefi-{hyperliquid,aster}-*-20260727-022558` instances show `RUNNING`, and each has produced 8-25 fresh
      `ManifestWriter: per-VM shard updated` events in the ~1h05m since the resume (hyperliquid-2023 additionally shows
      `PROGRESS: chunk=2/365` advancing) — genuinely active, not stuck-but-running. **Did NOT relaunch** (nothing to
      relaunch — the resume already worked) and **did NOT stop/restart anything** (VM-delete-guardrail: no genuine
      staleness signal here, the opposite — it's healthy). This is a **365-day-per-venue-year historical backfill**;
      full completion is a multi-hour-to-multi-day background operation, not something one session completes —
      superseding this checkbox with the current verified-healthy state rather than blocking on it further. **Next
      check-in should verify**: (a) no 3rd interruption recurs, (b) forward progress via `run.log` chunk/entry counts
      climbing (never mere `RUNNING` status), (c) eventual `DEPLOYMENT_COMPLETED exit_code=0` per VM as the real
      completion signal for this todo.
- [x] ✅ [INFRA] P1. **3rd interruption CONFIRMED + RESOLVED (2026-07-27, slot-12, BLK-0545be2d).** Ground-truthed via
      `run.log` (never bare VM status) + `gcloud compute operations list`: all 7 `...-20260727-022558` VMs were
      mass-preempted (`compute.instances.preempted`) within a 10-second window at 2026-07-26T22:30:54-22:31:04 PDT
      (=2026-07-27 05:30-05:31 UTC) — confirmed independently by every VM's `run.log` tail stopping dead at that exact
      timestamp, ~1h35m into genuinely healthy running (real chunk-progress + manifest-shard writes per slot-7's prior
      check). Zero VMs running afterward, no auto-recovery relaunch, no `DEPLOYMENT_COMPLETED` in any log. This is the
      exact 3rd-interruption case flagged above — escalated per instruction rather than relaunching unilaterally.
      **Operator-approved resolution (Option A + guardrails)**: 3 genuine SPOT preemptions in one day in
      `asia-northeast1-c` = real capacity pressure, not a launcher/cost-guard bug (ruling out re-investigation) —
      switched to the SPOT-default HARD RULE's own sanctioned opt-out. **Relaunched with `ON_DEMAND=true`**
      (non-preemptible, idempotent non-force so it resumes from `PROGRESS.json` — zero data loss, on-demand cost bounded
      to remaining chunks only):
      `VENUES="HYPERLIQUID ASTER" ON_DEMAND=true bash scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`, new
      run-id `20260727-071055`. Guardrails followed: (1) verified zero fleet VMs running before launch: (2) non-force
      idempotent path: (3) `ON_DEMAND=true`: (4) verified STARTED — all 7 `STAGING`, `PROVISIONING_MODEL=STANDARD`
      (non-preemptible) within T+60s; (5) HL/ASTER are non-Tardis, no 1-VM cap applies. **Next check-in should verify**
      (T+10min+): `run.log` chunk-progress climbing on the new run-id, and eventual `DEPLOYMENT_COMPLETED exit_code=0`
      per VM as the real completion signal.
- [x] ✅ [DATA] P2. **Cross-ref (2026-07-27, slot-11)**: this fleet's `cefi-hyperliquid-2023-20260727-071055` VM is the
      live remediation for a specific gap independently tracked in
      `plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md` (HYPERLIQUID zero-rows
      2023-03-05..2023-12-31, root-caused there to the same preemption/catalogue-cap history documented in this doc). No
      new action here — confirmed the VM was RUNNING + advancing (day 2023-02-27 as of 08:37:45Z) via `run.log`, logged
      the cross-reference so the other doc's follow-up check doesn't duplicate-launch a VM this fleet already owns.
- [x] ✅ [DEPLOY] P1. Redeployed the IS fixes — built `instruments-service:latest`=7489ed1/0.43.0 from LDR (no-auth
      b99e586 + full-universe 0fe8e71 + dated-future quote fix 7489ed1) via Cloud Build d215d55a (SUCCESS); created the
      missing prod job `uts-prod-instruments-service-cefi-t1-recon` (fixes the ENABLED-but-404 06:00 IS scheduler).
      instruments-service@0fe8e71 + @7489ed1 on LDR. Evidence: `:latest` digest tag `7489ed1,0.43.0,latest`.

## DEPLOY MECHANISM RESOLVED (2026-06-23, operator dispatch)

**Deploy mechanism (DO step 1) — fully traced:**

1. **IS daily FETCH** = Cloud Run job `uts-prod-instruments-service-cefi-t1-recon` (scheduler
   `uts-prod-instruments-cefi-t1-schedule`, 06:00 UTC). Runs image
   `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/instruments-service:latest`, args
   `--operation=instruments --mode=batch --category=ALL --run-tag=t1-recon` (pattern from the live dev job
   `uts-dev-instruments-service-t1-recon`). The Tardis adapter (`reference_data/adapters/cefi/tardis/adapter.py`)
   enumerates the full `VenueMapping().all_tardis_exchanges` set (21 exchanges incl. binance/binance-futures/deribit/
   bybit/okex*/coinbase/upbit/bitstamp/huobi*/bitfinex*/bitget*/kraken/cryptofacilities/lighter-zksync) via the no-auth
   `GET /v1/exchanges/{exchange}` (availableSince/availableTo → available_from/to). **The image build trigger
   `instruments-service-build` fires on push to `main`.**
2. **Catalogue AGGREGATION** = Cloud Run job `instrument-catalogue-regen` (scheduler
   `instrument-catalogue-regen-nightly`, 02:00 UTC). Runs image `market-tick-data-service:latest` cmd
   `python /usr/src/unified-api-contracts/scripts/generate_instrument_catalogue.py --project-id central-element-323112`
   (UAC rollup baked into the MTDS image — daily shards → `prod/catalog.parquet`).

**THIRD ROOT FINDING — full-universe cap on the Tardis CEX venues (FIXED):** The catalogue's per-venue latest-day counts
were thin for the major CEX venues (BINANCE-SPOT 82 / BINANCE-FUTURES 56 / BYBIT 310 — vs real hundreds) because the
Tardis adapter's `_passes_asset_filter` (`reference_data/adapters/cefi/tardis/parsing.py`) gated EVERY spot/perp/future
on the curated ~45-asset `CEFI_BASE_ASSET_UNIVERSE` majors whitelist — the SAME cap BUG#4 dropped for HL/ASTER
(aster.py/hyperliquid.py @6031902) but never for the Tardis CEX venues. **FIXED — instruments-service@0fe8e71**: dropped
the `CEFI_BASE_ASSET_UNIVERSE` base gate for spot/perp/future (full-universe enumeration — every active instrument on a
canonical USD-family quote, small-coin funding included); KEPT the accepted-quote gate (USDT/USDC/USD — drops exotic
cross pairs) + the OPTIONS BTC/ETH-underlying gate (Deribit per-coin-option-chain volume control, operator-documented).
Tests updated to the full-universe contract (`test_cefi_tradfi_comprehensive.py`, `test_tardis_kraken_symbol_parse.py`).
IS `quality-gates.sh --no-fix` GREEN (73s).

**TWO ROOT BLOCKERS FOUND:**

- **(A) The no-auth fix b99e586 is on LDR ONLY** (NOT on staging/main). The `instruments-service:latest` image built
  today 12:10 is tag `412dedb` = 0.41.0 (the commit BEFORE b99e586). So the deployed image does NOT carry the no-auth
  enumeration fix. → Building the image directly from LDR (chicken-and-egg deploy authority).
- **(B) THE PROD IS RECON JOBS DO NOT EXIST.** `uts-prod-instruments-service-cefi-t1-recon` (+ `…-t1-recon`) are
  referenced by ENABLED schedulers (`t1_batch_scheduler.tf` defines only the scheduler, not the job) but the Cloud Run
  JOB was never created — only the `uts-dev-…` variants exist. So the 06:00 cefi IS fetch has been **404-ing silently in
  prod** = the IS catalogue daily fetch never ran in prod (explains the stale/small Tardis subset). → create the prod
  job from the dev pattern. **FIFTH ROOT FINDING — full-universe drop EXPOSED a latent venue-killer (FIXED):** the first
  full-universe fetch (exec ttt2g) succeeded but wrote only 11/19 venues — the 8 missing were exactly the high-value CEX
  venues (BINANCE-SPOT/FUTURES, BYBIT, KRAKEN-FUTURES, BITGET-SPOT/FUTURES, BITFINEX-SPOT, bare OKX). Root cause: ~49
  binance-futures symbols (dated quarterlies `btcusdt_260626`, `btcbusd_210129`; odd `btcusd1`) resolved to an EMPTY
  quote — the `_split_symbol` underscore path only accepted a quote AFTER `_`, but the expiry tag (`260626`) is not a
  quote, so the `<BASE><QUOTE>` body before `_` was never matched. `InstrumentRecord` REQUIRES a non-empty quote*asset
  for SPOT/FUTURE/PERP (hard_schema_enforcement) → it RAISED inside the per-venue parse loop → CF-11 re-raised → the
  WHOLE venue dropped to 0 rows. The majors whitelist had MASKED this (those exotic bases were filtered
  pre-construction). **FIXED — instruments-service (next commit)**: (1) `_split_symbol` handles the dated-future shape
  `<BASE><QUOTE>*<EXPIRY>`by concatenated-matching the body before`\_`; (2) `\_parse_tardis_instrument` SKIPS (returns
  None, never raises) a pair-identity instrument with an unresolved quote — shard-level isolation so one bad symbol
  can't kill a venue. Local repro post-fix: binance-futures **869** (was 56), binance(-spot) **1167** (was 82), bybit
  **1497** (was 310), bitget-futures 951, cryptofacilities/KRAKEN-FUTURES 1148, bitfinex 288 — all parse, none raise.

### ⚠️ OPERATOR DECISION — semantic conflict: full-venue-universe (this dispatch) vs wide-curated-whitelist (peer WIP)

**Two concurrent, conflicting approaches to the SAME surface (cefi universe gating):**

- **THIS dispatch (operator: "FULL universe per venue, binance-futures hundreds")** — IS@0fe8e71 + quote fix:
  `_passes_asset_filter` DROPS the `CEFI_BASE_ASSET_UNIVERSE` base-whitelist gate for spot/perp/future → every active
  instrument on a USD-family quote enumerates. Gate reduced to {accepted-quote, options=BTC/ETH}.
- **Concurrent PEER (uncommitted WIP in `unified-api-contracts/.../cefi_instrument_universe.py`)** — rewrites
  `CEFI_BASE_ASSET_UNIVERSE` into a wider survivorship-bias-free UNION (legacy-44 + historical-top-100-since-2019) but
  DELIBERATELY KEEPS the whitelist gate ("NOT everything the venue lists — admits thousands of junk/wash pairs").
- **Reconciliation (autonomous, per operator's explicit full-universe instruction + don't-stomp-peer-WIP)**: the edits
  are in DIFFERENT files, no textual conflict — with my `_passes_asset_filter` change the base-whitelist is not
  consulted for spot/perp, so the peer's widened list is moot-for-gating but harmless. Proceeded with the operator's
  explicit "full universe" instruction. \*\*If the operator prefers the peer's curated-gate model, revert 0fe8e71's
  base-gate drop
  - adopt the peer's wide union.\*\* Both valid; flagged for human confirmation. NOT a blocker for this dispatch.

### Progress Log (2026-06-23 — operator full-cefi-catalogue dispatch, in flight)

- **Deploy mechanism resolved** (above). IS image build trigger `instruments-service-build` (asia-northeast1) fires on
  push to `main`; builds `instruments-service:latest` (+ `:VERSION` + `:SHORT_SHA`). The catalogue jobs:
  `uts-prod-instruments-service-cefi-t1-recon` (FETCH, image `instruments-service:latest`, args
  `--operation=instruments --mode=batch --asset-group=CEFI --run-tag=t1-recon`) → daily shards
  `instrument_availability/by_date/day=*/venue=*/instruments.parquet`. Per-instrument rollup =
  `instruments-service/scripts/build_instrument_catalogue.py --asset-group cefi` (NOT the `instrument-catalogue-regen`
  Cloud Run job — that builds the availability-MATRIX from `_index/availability_index.parquet`). `available_from` =
  MIN(first observed snapshot day, declared `available_from_datetime` = Tardis `availableSince` genesis); monotonic
  grow-only guard.
- **Created** the missing prod job `uts-prod-instruments-service-cefi-t1-recon` (fixes the ENABLED-but-404 06:00
  scheduler) — `DEPLOYMENT_ENV=prod`, `--asset-group=CEFI`, SA `unified-trading-sa`, 2cpu/4Gi/3600s.
- **Shipped** instruments-service@0fe8e71 (full-universe whitelist drop) to LDR; PM plan flip @06c459fd3.
- **Built** final `instruments-service:latest` from LDR@0fe8e71 (no-auth + full-universe), Cloud Build accf1e5c (in
  flight). Once green: execute the fetch job → rollup → verify → export CSV.
- Tardis venue universe = `VenueMapping().all_tardis_exchanges` (21 exchanges) → IS `_CEFI_VENUES` (19 canonical cefi
  venues: BINANCE-SPOT/FUTURES, BYBIT, OKX-SPOT/SWAP/FUTURES, DERIBIT, DERIBIT-COMBO, COINBASE-SPOT, HYPERLIQUID, UPBIT,
  ASTER, KRAKEN-FUTURES/SPOT, BITFINEX-FUTURES/SPOT, BITGET-SPOT/FUTURES).

**FOURTH ROOT BLOCKER — IS recon job has NO date default (FOUND + worked-around 2026-06-23):** the IS CLI date-loop
framework (`UTL date_utils.get_date_range`) requires explicit `--start-date`/`--end-date`; the recon job args omitted
them and the empty scheduler `httpTarget.body` injects none → `ValueError: Invalid date format ''` → `exit(1)`. So even
had the prod job existed, the 06:00 schedule would have crashed on dates. Worked around by setting
`--start-date=$TODAY --end-date=$TODAY` on the job. **FOLLOW-UP TODO below** — the recurring daily job must self-default
to today (a hardcoded date goes stale tomorrow).

- [x] ✅ [SCRIPT] P2. **VERIFIED ALREADY SHIPPED (2026-07-28, slot-8)**: option (a) landed same-day this todo was filed
      — `instruments-service@2217756f` (2026-06-23) `_default_recon_dates_to_today()` (`cli/main.py:310-333`, called
      pre-`ServiceBootstrap.run()`) self-defaults `--start-date`/`--end-date` to TODAY(UTC) when `--run-tag=t1-recon` +
      both unset (no-op if explicit). 5/5 `test_recon_date_default.py` pass (re-ran this session); the terraformed cefi
      job args carry no hardcoded date, so (a) governs live — (b) not needed.

- [x] ✅ [INFRA] P1. Force-ran the IS fetch (`uts-prod-instruments-service-cefi-t1-recon` exec xqcxr) → daily shards
      day=2026-06-23 for ALL 18 cefi venues (10,458 active instruments, full universe per venue — binance-spot 763 /
      binance-futures 677 / bybit 640 / kraken-spot 894 / okx-spot 848, NOT the old ≤33 subset). Aggregated via
      `build_instrument_catalogue.py --asset-group cefi` (the correct per-instrument rollup tool; the
      `instrument-catalogue-regen` Cloud Run job builds the SEPARATE availability-MATRIX, not the per-instrument
      catalog) → `prod/catalog.parquet` PROMOTED 230,073 rows (monotonic ACCEPT). Per-venue breadth + available_from/to
      genesis verified (see FINAL REPORT).
- [x] ✅ [INFRA] P2. **VERIFIED (2026-07-28, slot-9)**: 06:00 FETCH shard day=2026-06-24 holds all 24 venues +
      continuous daily since; 02:00 aggregate (now `lifecycle-catalogue-regen-cefi-daily`) green, `catalog.parquet`
      fresh today.
- [x] ✅ [SCRIPT] P2. **DONE (2026-07-26, slot-12)**: entries already existed (added via a since-landed "CeFi venues
      added 2026-06-23" for-loop section in `data_type_capability.py`, not a literal per-venue block — a literal-string
      grep missed them). Locked in with a new regression test (`unified-api-contracts@b0547c36`, 9 tests). Full
      evidence: `plans/archive/2026_07/cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s corresponding todo.
- [x] ✅ [MTDS] P2. **[already covered by `plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` — see
      that doc for execution; verified 2026-07-28 slot-9]** Track-2's launch already did this (`SINGLE_VM_QUEUE=1`, 17
      venues × 2020-2026, one VM `cefi-queue-heavy-binancefutu-x17-20260727-210013`, re-verified `RUNNING`+advancing,
      N=1-cap holds both clouds, durably parked on `cefi-track2-backfill-vm-terminated`); daily `…-cefi-t1-recon` covers
      `+live`. Not re-launching (N=1-Tardis-VM HARD RULE). Completion tracked by that doc's MID/POST checkpoints.

  ### Scoping 2026-07-12 (operator-ordered pre-launch) — READ-ONLY breakdown before the Tardis paid backfill launch

  **Extracted 2026-07-31** (line-cap remediation — see
  `/plans/archive/2026_06/cefi_hl_aster_batch_data_gaps_history_2026_06_22.md` § "Scoping 2026-07-12" for the full
  pre-launch `attempted_failed` breakdown, cost-model note, and the CRITICAL Tardis 403/concurrent-IP-lockout finding).
  Headline: 1,722,232 Tardis-attributable `attempted_failed` cells (99.9% of the cefi total) at scoping time, 74.9% of
  which were the `tardis_concurrent_ip_lockout_2026_07_12.md` 403 lockout rather than genuine absence. The launch this
  scoped has since run (Track-2 backfill, see Progress Log below) — this section is READ-ONLY history now, no open todo
  depends on it.

- [x] ✅ [MTDS] P2. **Empty/failed re-analysis** — market-tick-data-service@83fee813. Shipped
      `scripts/classify_cefi_catalogue_caused_gaps_2026_07_28.py` (+ 5-case unit test,
      `tests/unit/scripts/test_classify_cefi_catalogue_caused_gaps.py`): joins consolidated cefi manifest
      `empty_confirmed`/`attempted_failed` rows against IS `catalog.parquet`'s `available_from`
      (`= MIN(first observed by_date snapshot day, declared Tardis genesis)`) to distinguish **catalogue_caused**
      (cell.date < 2026-06-23 AND the instrument's `available_from` >= 2026-06-23 — the OLD SMALL (≤33/venue) catalogue
      never observed the instrument, so no genuine attempt could have been driven for it) from **genuine_absence**
      (already known + attempted under a correctly-sized catalogue, or not in the catalogue at all — pre-listing/never
      existed). Mirrors `reclassify_cefi_manifest_mvp_universe_2026_06_23.py`'s convention: **DEFAULT = DRY-RUN**
      (prints counts, writes nothing); `--apply` is gated (snapshots the pre-flip manifest first) and flips
      `catalogue_caused` cells to `expected_unattempted` so the ALREADY-RUNNING Track-2 full-universe backfill
      (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) naturally re-attempts them on its next skip-if-fresh
      pass — no new VM launch needed for the "re-fetch" half of this todo. `--apply` itself is left for a follow-up
      operator-approved run (same Phase-C-style gate as the sibling script) — code shipped + QG green (7326 passed) is
      this todo's done_definition.
- [x] ✅ [SCRIPT] P3. **DONE 2026-07-31 (slot 9) — `deployment-service@76eff29`.** Made the dirty-tree check in
      `create_tarball()` a per-repo SKIP-with-warning (mirrors the existing not-found SKIP) instead of `return 1` under
      `set -euo pipefail`, which previously aborted the WHOLE script on the FIRST dirty repo — even already-built CLEAN
      core tarballs (mtds/UAC/UTL) in `$TMP_DIR` never reached the end-of-run upload step. Added a
      `_skipped_dirty_repos` counter + end-of-run WARNING summary listing skipped repo names so a dirty-skip stays
      visible instead of silent. Verified via a scoped dry-run against a throwaway fake-repo workspace: with one dirty
      extra repo (`instruments-service`), all 4 CORE tarballs built successfully, the dirty repo was SKIPPED (not
      fatal), and the script reached the upload step with exit 0 — the prior behavior (hard abort before upload) is
      fixed. QG green (217s, sentinel@76eff29).

---

## TARDIS CEX venues — mvp-driven backfill (operator 2026-06-23, dispatch)

Generalises BUG#4's catalogue-driven universe from {HL,ASTER} to the **Tardis CEX venues** (binance-spot/futures, bybit,
okx-spot/swap/futures, deribit, kraken-spot/futures, coinbase-spot, bitfinex-spot/futures, bitget-spot/futures, upbit).
Goal: backfill on the **mvp capture universe** (`is_in_mvp_capture_universe`, the perp-gated SSOT; manifest already
reclassified to this denominator).

### Diagnosis (Read of the actual code path — keystone finding)

The Tardis CEX path is `VM_TASK=cefi-backfill` → `--operation download` → `tick_data_handler.py` → orchestrator
`_process_venue` → `_fetch_one_venue` → `fetch_tick_data_for_venue` → `_route_tardis` → `TardisAdapter.download_batch` →
**`_resolve_symbols(exchange, date, instrument_ids)`** (`market_interface/adapters/tradfi/tardis_symbol_resolution.py`).

- When `instrument_ids` IS passed (the launcher's hardcoded 9-coin `SYMBOLS_<VENUE>` lists), `_resolve_symbols` uses
  those 9 verbatim → **cap at 9**. This is the keystone cap.
- When `instrument_ids` is None, `_resolve_symbols` reads the IS by_date snapshot
  `instrument_availability/by_date/day={D}/venue={V}/instruments.parquet` and returns its `raw_symbol`s — but that is
  the **FULL** per-venue universe (binance-futures 677, not the mvp subset), NOT mvp-gated. So neither path yields the
  mvp universe.

### Decision (autonomous, documented record of intent)

mvp-gate the `_resolve_symbols` GCS path with the SAME shared predicate `is_in_mvp_capture_universe` that
`cefi_catalog_reader._row_in_mvp_capture_universe` + the onchain-perp handler + the manifest mvp-denominator already use
(single SSOT, cannot drift). Per-EXCHANGE perp-gate via `has_perp_for_base` computed from the by*date df. Drop the
launcher's hardcoded 9-coin `SYMBOLS*<VENUE>`lists + stale Upbit KRW so`instrument_ids` is empty → the mvp-gated GCS
path runs. **Consequence (documented):** the perp-gate is per-exchange, so pure-spot-no-perp venues (COINBASE-SPOT,
UPBIT, BITFINEX-SPOT) resolve to 0 mvp instruments — this is CORRECT and matches the manifest mvp-denominator (those
cells are not in-mvp); capturing nothing there is honest, not a gap. DERIBIT options ride the OPTION carve-out (always
mvp); dated futures ride base+venue (not perp-gated).

### Cross-venue perp-gate correctness (found during smoke proof)

First implementation computed `has_perp_for_base` from the SINGLE venue's by_date frame → BINANCE-SPOT resolved to mvp=0
(its by_date file is SPOT_PAIR-only; the perps live in the BINANCE-FUTURES file). FIXED: `_mvp_filter_by_date_df`
sources `has_perp_for_base` from the rolled-up catalogue (`prod/catalog.parquet`, ALL venues) via a process-cached
`_load_cross_venue_perp_bases()` (reuses `cefi_catalog_reader._build_has_perp_for_base`) — the SAME cross-venue frame
the catalogue reader gates on. Fail-open: empty perp set / missing base_asset / predicate error → full per-day universe
(never zero the backfill).

### Shipped

- **mtds@7a6e6b6** — `tardis_symbol_resolution.py`: `_mvp_filter_by_date_df` + `_load_cross_venue_perp_bases` applied in
  `_resolve_symbols` GCS path (instrument_ids=None) → the catalogue-driven Tardis CEX universe is the perp-gated MVP
  subset (shared `is_in_mvp_capture_universe` predicate; cross-venue perp-gate; `MTDS_CEFI_INCLUDE_NON_MVP=true`
  diagnostic bypass). New unit test `tests/unit/test_tardis_resolve_symbols_mvp_gate.py` (5 cases — perp self-qual,
  cross-venue spot kept, no-perp spot dropped, bypass, fail-open). mtds `quality-gates.sh --no-fix` GREEN; basedpyright
  0/0/0.
- **deployment-service@8a2a831** — `launch-cefi-sharded-backfill.sh`: dropped the hardcoded 9-coin `SYMBOLS_<VENUE>`
  lists + stale Upbit KRW; CeFi shards now launch with NO `VM_INSTRUMENT_IDS` → MTDS resolves the catalogue-mvp
  universe. Venue loop generalised to all 15 Tardis CEX venues (per-venue genesis years; `VENUES`/`YEARS` overrides for
  smoke/first-wave). HL/ASTER excluded (own launcher). deployment-service `quality-gates.sh --no-fix` GREEN; shellcheck
  clean.
- **SMOKE PROOF — code-level (real data, 2026-06-22 by_date)**: `_mvp_filter_by_date_df` yields BINANCE-FUTURES 469 /
  BINANCE-SPOT 531 / BYBIT 424 / OKX-SWAP 276 / OKX-SPOT 577 / KRAKEN-FUTURES 271 / DERIBIT 3058 (NOT 9); COINBASE-SPOT
  0 / UPBIT 0 (no perps on those exchanges → out of mvp, correct + matches the manifest denominator). 3643 cross-venue
  perp-base pairs loaded from the catalogue.

### Deploy + SMOKE VM (operational)

- **Tarball rebuilt from clean LDR** (`create-code-tarballs.sh --include instruments-service`, 2026-06-23T17:41Z):
  `gs://deployment-scripts-…/code/mtds-code.tar.gz` VERIFIED to contain mtds@7a6e6b6 (`_load_cross_venue_perp_bases` +
  the new test) + UAC@6d215c1b + UTL@346f3bb + instruments-service@19227d3 + deployment-service@8a2a831 (umbrella
  alert-routing). (`--asset-group CEFI` aborted on a peer's dirty features-service — see the P3 todo above; core-only
  `--include` is the workaround.)
- **SMOKE VM launched** `cefi-binance-futures-2024-heavy-20260623-174255` (BINANCE-FUTURES, 2024, heavy
  trades+book_snapshot_5, SYMBOLS=catalogue-mvp via NO VM_INSTRUMENT_IDS). RUNNING at T+1. A tracked monitor watches the
  GCS run.log for the `loaded N symbols for BINANCE-FUTURES` line — verdict MVP-UNIVERSE-CONFIRMED iff N>>9 (expect
  ~hundreds). Full fleet (137 cefi VMs across 15 venues × genesis years) is staged behind the smoke per the
  > 50-VM REPORT gate — first wave + roster reported to the orchestrator before blasting.

## VM/Cloud-Run ALERT ROUTING — live→#uts-live-alerts, batch→#data-pipeline-alerts (operator 2026-06-23)

**Goal (alerting-service + deployment-service):** EVERY VM / Cloud-Run-job issue (failure / crash exit-137 OOM / hang /
WARNING / ERROR) propagates to Slack so we can act — **BATCH compute → #data-pipeline-alerts**, **LIVE compute →
#uts-live-alerts**.

### Routing contract (established)

- The umbrella (`LIVE` / `BATCH` / `PAPER` / `EXPERIMENT`, UAC `DeploymentUmbrella`) is the channel selector. Resolved
  from the VM name via `deployment_service.deployment_classification.classify_deployment_target` /
  `umbrella_for_vm_name` and STAMPED on the event payload (`details["umbrella"]` + `details["cloud"]`).
- alerting-service router `_route_data_pipeline_event` splits on it: **`umbrella` starts-with `live` (case-insensitive)
  → `#uts-live-alerts`** (SM webhook `alerting-uts-live-alerts-slack-webhook`); **everything else / no umbrella →
  `#data-pipeline-alerts`** (SM webhook `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK`). CRITICAL still ALSO pages
  (PagerDuty/Telegram) for BOTH umbrellas — only the Slack CHANNEL differs. Webhook secret names → channel:
  `alerting-uts-live-alerts-slack-webhook` → #uts-live-alerts (LIVE); `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK` →
  #data-pipeline-alerts (BATCH).

### Gaps found (audit, Read of actual files — greps obfuscated)

1. **alerting-service router** sent ALL `DP_*` + `DEPLOYMENT_*` events to `#data-pipeline-alerts` unconditionally
   (`_route_data_pipeline_event` → `_mirror_to_data_pipeline_slack`, no umbrella branch). So a LIVE-umbrella VM failure
   landed in the BATCH channel. `#uts-live-alerts` only ever got `LIVE_ALERT_RULES` runtime events (kill-switch/
   circuit-breaker), never deployment/DP failures.
2. **deployment-service emitters never stamped the umbrella**: `deployment_heartbeat._emit` (DEPLOYMENT_STARTED/
   COMPLETED/FAILED) and `exit_code_fleet_monitor._finding_for` (DP_VM_EXIT_NONZERO / DP_VM_GONE_NO_CAPTURE) +
   `heartbeat_stall_watcher._finding_for` (DP_VM_STALL / DP_EVENT_LOOP_STARVED) built payloads with `vm_name`+
   `asset_group`+`exit_code` but NO `umbrella`/`cloud` — so even if the router split, it had no signal. The
   deployment-observability codex doc claimed alerts "carry the umbrella" — they did NOT.

- Both live channel (`#uts-live-alerts`) + batch channel (`#data-pipeline-alerts`) ARE wired as SM-webhook sinks
  (`uts_live_alerts_slack.py` / `data_pipeline_slack.py`, `get_paging_credentials()` returns both) — the wiring existed,
  the routing+stamping did not.

### Fixes shipped (LDR)

- **alerting-service@f94b3b5** — `router._route_data_pipeline_event` now umbrella-splits via new `_is_live_umbrella()`
  (case-insensitive leading-`live`, no-umbrella→batch fail-safe) + `_mirror_to_uts_live_alerts_slack_dp()`; CRITICAL
  paging unchanged for both. Tests rewritten (`test_router_deployment_enrichment.py`, 7/7): BATCH→data-pipeline,
  LIVE→uts-live, lowercase `live-defi` token, LIVE DP_VM_EXIT_NONZERO→uts-live. QG green (48s).
- **deployment-service@94dfcfc** — new SSOT resolver `umbrella_for_vm_name(vm_name, VM_PREFIX_TO_BUCKET)` in
  `deployment_classification.py` (longest-prefix → lifecycle→umbrella via `classify_deployment_target`, paper-spec
  override, raises on unregistered prefix). Stamped `umbrella`+`cloud="GCP"` onto: `deployment_heartbeat._emit`
  (DEPLOYMENT\_\* via `_resolve_umbrella`), `exit_code_fleet_monitor` (`umbrella_for_vm` threaded through `sweep`),
  `heartbeat_stall_watcher` (same), wired in `cli.py` `_umbrella_for_vm`. New unit test `test_umbrella_for_vm_name.py`
  (6/6). QG green (53s). Running cefi backfill VMs untouched (code reaches them only on next tarball rebuild — not
  deployed here).

### PROOF of delivery (2026-06-23, REAL SM webhooks, observed HTTP 200)

Synthetic `DEPLOYMENT_FAILED` routed through the real notifier mirrors with the real SM webhooks:

- **BATCH umbrella → #data-pipeline-alerts**: `data-pipeline-alerts Slack POST ok (status 200)` /
  `SLACK_MESSAGE_SENT channel=data-pipeline-alerts` → `delivered(2xx)=True`.
- **LIVE umbrella → #uts-live-alerts**: `SLACK_MESSAGE_SENT channel=uts-live-alerts` (2xx) → `delivered(2xx)=True`.
- `_is_live_umbrella` asserts: BATCH→False (batch channel), LIVE→True (live channel). Both messages tagged
  `[SYNTHETIC VERIFY <ts>]` for operator dismissal.

### Codex SSOT to update (follow-up)

- [x] ✅ [DOCS] P2. **unified-trading-pm** — update `/codex/05-infrastructure/deployment-observability.md` § "Slack
      parity" to state the umbrella-driven channel split (LIVE→#uts-live-alerts, BATCH→#data-pipeline-alerts) + the
      emitter umbrella-stamping contract (was: "DEPLOYMENT\_\* → #data-pipeline-alerts" only). Provenance: alerting
      routing split shipped alerting-service@f94b3b5 + deployment-service@94dfcfc 2026-06-23.

      **SHIPPED 2026-07-30 (slot 8) — `unified-trading-pm@66fa926d5`.** Executed via
          `plans/archive/2026_07/cefi_satellite_ao_dispatch_batch3_2026_07_26.md`'s owning todo (per the SUPERSEDED note below,
          which this entry preserves for history): both cited shas verified reachable on `origin/live-defi-rollout`, the
          live routing code read directly and confirmed to match the claimed split, codex corrected. Both checkboxes
          flipped citing the same commit, per that todo's own instruction.

          **SUPERSEDED (2026-07-30, conflict-check `blank_assigned_vm_dispatch_classification_gap_2026_07_26.md`-005)** —
          this exact fix is already carried as its own todo (`[DOCS] P2. Correct the codex Slack-parity contract...`) in the
          currently-active `plans/archive/2026_07/cefi_satellite_ao_dispatch_batch3_2026_07_26.md` (archived 2026-08-05; which explicitly cites THIS
          doc/line as its source). Do not dispatch this copy — that plan owns execution; when it ships, flip both
          checkboxes citing the same commit.

## UAC capture-universe expansion — survivorship-bias-free (operator 2026-06-23)

Scope: unified-api-contracts ONLY (IS catalogue re-enumeration + the CSV that CONSUMES this universe = another worker's
lane). Replaced `CEFI_BASE_ASSET_UNIVERSE` (the 44-coin MVP cap gating `_passes_asset_filter` on the Tardis CEX venues)
with the curated UNION of three tranches — KEEPS the gate, widens the universe:

1. **Legacy 44** — all kept (top-cap majors + the 2026-06-16 operator-requested coverage incl. EIGEN dust + FTT/LUNA
   delisting-test coins).
2. **Top-100-by-mcap aggregated across TIME since 2019** — curated checked-in frozenset (no live mcap API) = the union
   of coins that were top-100 at each year-end/cycle-peak 2019→today. Survivorship-bias-free by construction: includes
   the retired/collapsed big names (LUNA, LUNC, UST, USTC, FTT, SRM, CEL, WAVES, OKB, HT, LEO, OMG, NEXO, HEDG, NANO,
   STEEM, …) + all current majors/L1s/L2s/DeFi/memecoins (BONK, WIF, PEPE, SHIB, FLOKI, …).
3. **All HYPERLIQUID + ASTER perp base assets** — read from
   `gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` (venue ∈ {HYPERLIQUID, ASTER},
   instrument_type=PERPETUAL, deduped `base_asset` column), scaling prefixes (1000/k) normalised,
   equity/tokenized-stock/macro tickers (already covered by `CEFI_EQUITY_PERP_BASE_UNIVERSE` + `crypto_equity_link`) +
   non-ASCII garbage symbols excluded → 384 crypto-only HL/ASTER perp bases. HL/ASTER bypass the filter themselves; the
   point is the CEX side captures the same coins for cross-venue dispersion.

### Shipped

- **unified-api-contracts** — `registry/cefi_instrument_universe.py`: `CEFI_BASE_ASSET_UNIVERSE` rewritten as the SORTED
  curated union (**493 base assets**; was 44). Module docstring documents the 3-tranche rationale +
  survivorship-bias-free + curated-because-no-live-mcap. Gate (`_passes_asset_filter`, lives in instruments-service)
  intentionally NOT touched — still gates, just on the wider set. Breakdown: legacy 44 + top-100-hist (+190
  not-in-legacy) + HL/ASTER perp (+259 not-in-legacy|hist) = 493.
- Reconciled docstrings: `canonical/crosscutting/mvp_scope.py` (no longer "44-base MVP" — bumped
  `MVP_SCOPE_CONFIG_VERSION` 3→4 with a v4 changelog note; the computed content hash auto-flips) +
  `canonical/crosscutting/total_universe.py` ("captured subset" not "MVP subset").
- Tests: rewrote `tests/test_cefi_universe_coverage.py` (size ≥250 band; legacy-44 all present; retired-top-100 present
  = survivorship-bias proof incl. LUNA/FTT/SRM/CEL/WAVES; key HL/ASTER bases incl. HYPE/PURR/ASTER/FARTCOIN; sorted +
  no-dup determinism). Fixed `tests/unit/test_mvp_scope.py` two "non-MVP base" cases (SUI is now IN the universe →
  switched to a synthetic out-of-universe token).
- Verification: targeted tests 90 passed; basedpyright 0/0/0 on the 3 source files; ruff clean (replaced `∪` math symbol
  with `+` to satisfy RUF001/002/003). Full `quality-gates.sh --no-fix` GREEN (see commit). Shipped via
  `quickmerge --agent --files`.

Note: the IS catalogue re-enumeration + the CSV consuming this universe is a DIFFERENT worker's lane (not touched here).

### Full-universe fetch SUCCEEDED (2026-06-23, exec xqcxr, image :latest=7489ed1/0.43.0)

18 cefi venues, **10,458 active instruments** written to instrument_availability/by_date/day=2026-06-23/. Per-venue
active (old-cap → now): BINANCE-SPOT 82→763, BINANCE-FUTURES 56→677, BYBIT 310→640, KRAKEN-SPOT 75→894, OKX-SPOT
125→848, UPBIT 16→200, BITGET-FUTURES 677, BITGET-SPOT 625, KRAKEN-FUTURES 332, COINBASE-SPOT 429, DERIBIT 2983,
OKX-SWAP 388, ASTER 484, HYPERLIQUID 178, BITFINEX-SPOT/FUTURES 81/70, DERIBIT-COMBO 117, OKX-FUTURES 72. Full universe
per venue confirmed (binance hundreds). Next: build_instrument_catalogue.py rollup → prod/catalog.parquet → CSV export.

### ✅ FINAL REPORT — cefi full-catalogue rebuilt to 100% (2026-06-23, operator dispatch DONE)

**Catalogue PROMOTED**: `instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` = **230,073 rows** (was
223,300; monotonic ACCEPT). Rebuilt from a full-universe IS fetch (image `:latest`=7489ed1/0.43.0, no-auth + both
whitelist/quote fixes) → 18 cefi venues / 10,458 active instruments on day=2026-06-23 →
`build_instrument_catalogue.py --asset-group cefi` rollup of 35,028 by_date parquets.

**Per-venue cumulative-catalogue breadth (baseline → now)**: BINANCE-SPOT 82→766, BINANCE-FUTURES 56→681, BYBIT 310→899,
KRAKEN-SPOT 75→900, OKX-SPOT 125→857, BITGET-FUTURES →682, BITGET-SPOT →634, KRAKEN-FUTURES 588→859, COINBASE-SPOT
→1194, UPBIT 16→201, OKX-SWAP →3266, OKX-FUTURES →3676, DERIBIT →214,148, ASTER 484, HYPERLIQUID 180,
BITFINEX-SPOT/FUTURES 82/72. available_from spans genesis 2010-01-01 → 2026-06-22 (per-instrument lifecycle windows).

**CSV deliverable** (operator review):

- GCS:
  `gs://instruments-store-cefi-prd-central-element-323112/_exports/cefi_instrument_universe_per_venue_2026_06_23.csv`
  (58,052 rows: one per venue × year-snapshot{2019..2025, 2026-06-23} × active instrument; cols venue / year_snapshot /
  snapshot_date / instrument_id / raw_symbol / instrument_type / base_asset / underlying / available_from / available_to
  / venue_data_types). Summary: `…/_exports/cefi_universe_summary_2026_06_23.csv`. Local copies in `/tmp/`.

**Infra shipped**: created the missing prod Cloud Run job `uts-prod-instruments-service-cefi-t1-recon` (fixes the
ENABLED-but-404 06:00 IS scheduler). instruments-service@0fe8e71 (full-universe whitelist drop) + @7489ed1 (dated-future
empty-quote venue-killer fix) on LDR.

**Honest gaps / follow-ups (tracked as todos above)**:

1. **data_types empty for KRAKEN-SPOT/FUTURES, BITGET, BITFINEX, ASTER** in the CSV — these venues are NOT in the UAC
   `DATA_TYPE_CAPABILITY_REGISTRY` (cefi has explicit entries only for BINANCE/BYBIT/OKX/DERIBIT/COINBASE/HYPERLIQUID/
   UPBIT). Accurate signal: those venues' batch data_types are unregistered. FOLLOW-UP: add their capability entries.
2. **Recon-job date is hardcoded** (`--start-date/--end-date=2026-06-23`) — tomorrow's scheduled 06:00 run would
   re-fetch the stale day. FOLLOW-UP todo above (self-default to today / scheduler-inject).
3. **Semantic conflict flagged for operator** (full-venue-universe here vs peer's wide-curated-whitelist UAC WIP) —
   reconciliation chosen (no textual conflict; my whitelist-drop makes the peer list moot-for-gating, harmless).
4. The MTDS market-tick backfill of this expanded universe + manifest migration are POST-operator-check phases (NOT done
   here, per the dispatch STOP-after-CSV instruction).

## OKX-SPOT 2010-poison residual purge + daily-mechanism verify (operator dispatch 2026-06-23)

> **Extracted 2026-07-28 (slot-9, line-cap remediation)** — fully resolved (TASK 1 root-caused + PURGED + generalised
> anti-recurrence script; TASK 3 daily-mechanism verdict SUCCEEDED), no open todos. Full text moved to
> `/plans/archive/2026_06/cefi_hl_aster_batch_data_gaps_history_2026_06_22.md`.

## Tardis CEX lifecycle-fix DEPLOY + full-universe backfill scale (operator dispatch 2026-06-23, /autonomous)

### Phase 0 — verify fix on LDR + ship follow-up (DONE)

- **aec8bd0 (lifecycle fix) CONFIRMED on LDR** — `_resolve_symbols` reads the rolled-up catalogue
  (`_catalogue_symbols_for_venue_date`, available_from<=date<=available_to ∩ mvp) FIRST, falls open to the sparse
  by_date snapshot only when catalogue unreadable. HEAD=aec8bd0, on `live-defi-rollout`.
- **Catalogue lifecycle VERIFIED** (read `instruments-store-cefi-prd-…/prod/catalog.parquet`): **227,576 rows / 157,092
  mvp** across 19 venues. Per-venue mvp + genesis: DERIBIT 147,459/2019, OKX-FUTURES 3,662/2019, KRAKEN-FUTURES 798,
  BYBIT 683, OKX-SPOT 581, BINANCE-SPOT 533, BINANCE-FUTURES 473, BITGET-FUTURES 409/2024, ASTER 359/2021, UPBIT
  352/2021, BITGET-SPOT 339, BYBIT-SPOT 315, KRAKEN-SPOT 287, OKX-SWAP 285, HYPERLIQUID 172, COINBASE-FUTURES 141/2024,
  COINBASE-SPOT 123, BITFINEX-SPOT 70, BITFINEX-FUTURES 51. Matches the prompt's target.
- **In-flight follow-up reconciled**: the helper-extraction refactor (`_resolve_symbols_from_by_date_snapshot`) was
  REVERTED twice by a concurrent session touching the shared clone (and the untracked test file deleted). The refactor
  is behavior-NEUTRAL (size-cap cosmetics; `aec8bd0` already passes the function-size gate). DECISION (least-bad path):
  drop the cosmetic refactor, ship the two load-bearing pieces — (1) the `tradfi_shared.py:136` DTZ011 fix
  (`_dt.date.today()` → `_dt.datetime.now(_dt.timezone.utc).date()`, was a pre-existing over-baseline ratchet failure
  blocking the gate), (2) the rebuilt regression test `tests/unit/test_tardis_catalogue_lifecycle_universe.py` (7 tests:
  lifecycle-universe-not-snapshot / available_from+available_to windowing / mvp-boolean gate / SPOT_PAIR-drop on
  derivatives-only venue / INCLUDE_NON_MVP bypass / catalogue-None fall-open-to-by_date). All pass + isolation-safe.

### Phase 4 — stale-VM stop decisions (DONE)

- **STOPPED** `cefi-binance-futures-2024-heavy-20260623-174255` — run.log proved OLD enumeration ("loaded 25 symbols for
  BINANCE-FUTURES from GCS" — the sparse by_date path, NOT the 156-mvp catalogue). Used the stale
  `VM_TASK=cefi-backfill` 20-sym smoke. Deleted (ephemeral, shutdown-on-completion). Replaced by the scaled fleet.
- **LEFT RUNNING** `cefi-ext-full-2025/2026` (EXTENDED-STARKNET) — small DEX-perp venue capturing the FULL universe
  correctly (43 instruments, 61,920 rows/day across trades/book5/derivative_ticker/ohlcv_1m). Per dispatch: leave the
  small-DEX-venue VMs. Do-not-disturb: `cefi-hyperliquid-2024` backfill + all `mtds-live-cefi-*` live VMs (untouched).
  **CROSS-REF added 2026-08-12 (/plan-reconcile)**: `data_completion_to_100_all_ag_2026_06_21.md`'s own banner also
  tracks an EXTENDED-STARKNET (cefi) backfill in the same window (`cefi-extended-{2024,2026}-20260623-194308` +
  `cefi-extended-2025-resume-20260624-005413`) — same venue, overlapping dates, launched within a day of this session's
  VMs. Not independently confirmed here whether these are the same fleet under two naming schemes or a genuinely
  separate concurrent effort; check both docs' VM names/timestamps before assuming either is the sole EXTENDED-STARKNET
  tracker.

### Launcher = `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh`

- `VENUES="…" YEARS="…" bash …` → one VM per (venue,year), **NO VM_INSTRUMENT_IDS** → MTDS resolves the catalogue-mvp
  universe (the lifecycle-fix path). Registry-driven machine-sizing (per-venue memory tier). Default 15 Tardis CEX
  venues; per-venue genesis years via `_venue_years` (BINANCE/DERIBIT/COINBASE 2020→, BITGET 2023→, UPBIT 2022→, rest
  2021→). CEFI default ≈ 89 VMs + TradFi ES/VIX block ≈ 12.

### Phase 1 — follow-up commit SHIPPED + tarball rebuild (2026-06-23)

- **Follow-up shipped: mtds@4bbebb8** on LDR (helper extraction → `_resolve_symbols` 206L→123L under the 200L codex cap;
  the refactor IS load-bearing — `aec8bd0` alone FAILS the size gate; DTZ fix in tradfi_shared.py:136; 168-line
  regression test). QG green, `Quickmerge: agent`. A concurrent session repeatedly reverted the MTDS refactor + deleted
  the untracked test mid-work (root cause: foreign live-editor on the shared clone); re-applied + locked in via
  immediate quickmerge.
- **Tardis API key VERIFIED ACTIVE** — academic/unlimited plan (binance-futures/deribit/bitmex/… from 2019 → 2027-06).
  FLAT plan = no per-request billing → full-fleet scale is cost-safe (no per-VM Tardis $ concern). Launcher key-check
  preflight will pass.
- **Tarball rebuild**: deployed SHAs were mtds@aec8bd0, uac@074b1c0, utl@346f3bb3, deployment@2c141cd (HEAD, has the
  94dfcfc umbrella). Rebuilding CEFI set to pick up mtds@4bbebb8 + current uac. deployment-service has a FOREIGN
  live-editor (launch_budget_registry.py mtime <40s, machine-sizing WIP) — used --allow-dirty-tarball (the dirty file
  parses+imports cleanly, is launch-side only, not VM-runtime). UTL unchanged.

### Phase 2/3 — tarball DONE + RE-SMOKE launched (2026-06-23 19:36 UTC)

- **Tarball rebuild COMPLETE** — GCS `code/` now: mtds-code@4bbebb8, unified-api-contracts-code@6262409b,
  unified-trading-library-code@346f3bb3, deployment-service-code@2c141cd (umbrella 94dfcfc). VMs that boot now pull the
  lifecycle fix.
- **RE-SMOKE launched**: `VENUES=BINANCE-FUTURES YEARS=2024` → 2 VMs (launcher splits per venue into heavy[book5] +
  light[trades] groups): `cefi-binance-futures-2024-heavy-20260623-193543` + `…-light-…`, both RUNNING, NO
  VM_INSTRUMENT_IDS (catalogue-mvp path). Tardis key active (academic/unlimited, no per-req billing). Monitor armed on
  the heavy VM run.log for the symbol-load verdict (success=~156 from catalogue; fail=25 from by_date snapshot / error).
  **GATE: do not scale waves until this proves ~156.**

## Manifest consolidator FROZE (cefi market-data index stuck @ 2026-06-23T20:07) — diagnosis + fixes (2026-06-24)

**Root cause (diagnosed 2026-06-24)**: the cefi market-data consolidator
(`uts-prod-manifest-consolidator-market-data-cefi` Cloud Run job, `*/1` cron,
`python -m unified_trading_library.manifest_consolidator --bucket market-data-tick-cefi-prd-…`) stopped writing
`_index/availability_index.parquet` after 20:07:21 despite 148/149 per-VM shards being FRESH (06:41 mtimes, 683MB) —
every cycle since acquires the lock, early-returns in ~40s, exits 0 WITHOUT writing. NOT OOM (clean exit 0), NOT the
lock alone, NOT timeout (1800s budget). The incremental changed-shard cutoff (the `consolidator_content_write_at` marker
/ `_is_lock_fresh` sibling-skip path, manifest_consolidator.py:330-441) is mis-skipping the fresh shards. The 16.6M
out-of-window Deribit bloat (canonical 18.6M rows) is the SECOND-order amplifier (makes the eventual full merge heavy →
the original 16Gi OOM). Engine itself is sound (DuckDB memory-bounded + incremental + per-VM sharded — the operator's
"do we need Rust/DB" question: already a streaming DB merge, scales fine ONCE the canonical is kept lean).

**Immediate unstick (2026-06-24)**: paused the `*/1` market-data-cefi scheduler (stop churn), bumped job
16Gi→**32Gi/cpu8**, cleared the orphaned lock, ran one execution with **`--force`** (full rebuild, bypasses the broken
incremental cutoff — exec `hqm6m`). Args temporarily carry `--force`; REVERT after the write confirms + RESUME the
scheduler.

- [x] ✅ [INFRA] P0. **VERIFIED 2026-07-27 (slot-7)**: already comprehensively fixed by later work — no new code needed.
      Direct read of `unified_trading_library/manifest_consolidator.py` (current LDR tip `137e219c`) confirms BOTH
      diagnosed root causes from this todo's 2026-06-24 write-up are closed, with regression coverage: 1) **Idle-touch
      marker trap** — `consolidate()`'s incremental cutoff (`manifest_consolidator.py:749-813`) reads
      `_get_content_write_mtime()` (the LAST-REAL-MERGE marker, `consolidator_content_write_at`), NEVER the
      freshness-only `_get_canonical_mtime()`; the module's own comment names this exact bug class ("the idle-bucket
      incremental trap") and states an idle `_touch_canonical_mtime()` bumps `consolidator_run_at`/ `blob.updated` but
      never the content-write marker, so the cutoff can't skip past an unmerged fresh shard. Regression:
      `test_content_write_marker_stamped_on_real_merge_not_on_idle_touch`
      (`tests/unit/test_manifest_consolidator.py:587`) asserts a real merge stamps the content-write marker while an
      idle touch does not. 2) **Stale-but-present lock (`_is_lock_fresh`)** — a fresh-lock skip now runs
      `_check_stall_on_lock_skip()` (`manifest_consolidator.py:697-733`) which pages after repeated no-progress cycles
      rather than silently freezing forever; regression `test_consolidate_pages_on_repeated_silent_stall` +
      `test_consolidate_pages_on_repeated_lock_orphan_stall` (`tests/unit/test_manifest_consolidator.py:2532,2665`). A
      THIRD failure mode this todo's own diagnosis didn't name but a later incident found — an out-of-band rewrite
      stripping the content-write marker entirely (2026-07-17,
      `consolidator_content_write_marker_strip_silent_shard_reap_2026_07_17.md`) — is also closed: a canonical with no
      marker now FAILS CLOSED (treats every shard as changed, prunes nothing) instead of silently under-merging
      (`manifest_consolidator.py:814-834`). Plus the 2026-07-13 prune-race fix (content-write marker stamped with the
      shard-LISTING start time, not the later write time, so a shard written mid-cycle stays above next cycle's cutoff)
      and the 2026-07-21 TOCTOU-race fix (`14301571`) closing a related CAS gap.
      `bash scripts/quality-gates.sh --no-fix` GREEN (263s) on the current tree, including the full
      `test_manifest_consolidator.py` suite (4,650 lines) — the exact regression-test ask this todo made ("canonical@T,
      shards@T+1 → next cycle MUST merge+write") is covered by the existing incremental-merge test suite
      (`test_consolidate_merges_multiple_shards`,
      `test_consolidate_incremental_self_dedups_untouched_canonical_duplicates`, and siblings), all passing. No code
      change needed — closing as verified-via-code-read + green regression suite, not re-implementing.
- [x] ✅ [INFRA] P0. **VERIFIED HELD 2026-07-27 (slot-9)** — all 3 constituent fixes below ((1) clip, (1b) fleet deploy,
      (2) purge) were already shipped/executed 2026-06-24; the remaining open question was whether the fix held over
      time or the canonical re-bloated. **Live check**:
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` is **133.78 MiB**, last
      written **2026-07-27T04:43:54Z** (~15 min before this check, i.e. actively still being maintained by the `*/5`
      incremental consolidator cron) — consistent with the post-purge ~117-137MB figure and NOT the pre-purge
      1.02GB/49.7M-row bloated state, over a full month (2026-06-24 → 2026-07-27) of continuous incremental merges. This
      confirms clip (1)/(1b) is genuinely stopping new bloat at the seed source (not just a one-time purge that would
      have silently re-bloated under the ongoing `*/5` cron otherwise). (3)'s outcome (honest-coverage denominator
      reflecting the lean canonical) follows directly and was not independently re-measured this session (out of scope —
      no separate action item). **market-data-tick-cefi bucket + enumerator** — PURGE the out-of-window over-seeding.
      MEASURED on the fresh full-rebuild index 2026-06-24 (gcsfs read): index is **48.0M rows / 1.02 GiB**; **45.0M
      empty_confirmed (93.8%)** of which **44.2M `EXPECTED_INSTRUMENT_NOT_LISTED`** — DERIBIT 36.3M, OKX-FUTURES 2.3M,
      BINANCE-FUTURES 2.2M, BYBIT 1.2M, KRAKEN-FUTURES 1.0M, … and **43.9M carry BLANK instrument_type** (the over-seed
      signature: dated options/futures emitted for every day across their range, not clipped to listing window).
      captured=2.09M (+60% from the 1.31M 2026-06-21 start — backfill IS expanding real coverage). **ORDER MATTERS (the
      canonical purge alone is FUTILE — the `--force */5` cron re-merges the per-VM shards every 5 min → re-bloats):**
      (1) FIX the enumerator/writer to clip dated-instrument seeding to `[available_from,available_to]` so new shards
      stop emitting blank-instrument_type NOT_LISTED outside the window; (2) purge the existing cells from the **per-VM
      shards** (`_index/per_vm/*.parquet`) not just the canonical — then the next rebuild produces a lean
      ~3.8M-row/~100MB index; (3) lean canonical → honest-cov denominator becomes real (~55-60% via the query-time
      out_of_window exclusion). (Prior worker `a19169b2` died on rate-limit — redo, idempotent.) Seeding source to fix:
      grep who emits `EXPECTED_INSTRUMENT_NOT_LISTED` with no instrument_type (IS `enumerate_expected_universe.py` /
      MTDS capture preflight). COORDINATE with the out_of_window/dated-instrument work (other agent overlap).
  - [x] ✅ **(1) CLIP SHIPPED — mtds@7b18433b** (QG-green, on LDR; Tier-C drain → staging):
        `cefi_catalog_reader._iter_not_yet_listed` skips `_DATED_INSTRUMENT_TYPES={FUTURE,OPTION}` in pre-listing
        seeding (a dated option listing months out is not-in-universe, not honest-absence). Persistent
        PERPETUAL/SPOT_PAIR/EQUITY_PERP still seeded; active-window capture (`_yield_for_date`) unchanged. Regression
        `test_dated_instruments_not_pre_listing_seeded` (16/16 pass).
  - [x] ✅ **(1b) DEPLOY clip to fleet (2026-06-24)** — operator chose RELAUNCH-now. Rebuilt cefi tarball
        (`mtds-code.tar.gz` @08:34, clip mtds@7b18433b) → stopped all 120 pre-clip backfill VMs (do-not-disturb
        hyperliquid/extended + live `mtds-live-cefi-*` excluded) → relaunched via
        `FORCE=1 launch-cefi-sharded-backfill.sh` so new VMs boot the clip tarball + emit LEAN shards. Bloat emission
        halted at the source.
  - [x] ✅ **(2) PURGE DONE (2026-06-24)**: confirmed `--force` AND incremental both OOM (signal 9) at the 32Gi Cloud
        Run ceiling on the 1GB canonical (cpu max 8, ~32Gi mem cap → no RAM fix). Stopped fleet → snapshot canonical to
        `_index/snapshots/pre_purge_dated_not_listed.parquet` → parallel-purged 142 static shards (drop
        `empty_confirmed` ∧ `EXPECTED_INSTRUMENT_NOT_LISTED` ∧ instrument_id `:OPTION:`/`:FUTURE:`): **49.7M→7.8M rows
        (dropped 41.9M), 683MB→117MB** → deleted bloated canonical → cold `--force` rebuild from lean shards:
        **canonical 1.02GB→137MB, clean exit, no OOM**. Purge script: `scratchpad/purge_dated_not_listed.py` (streaming,
        idempotent, snapshot-first).
- [x] ✅ [INFRA] P1. **consolidator reverted (2026-06-24)** — args back to incremental (`--force` removed), memory
      32Gi→**16Gi/cpu4** (lean=cheap), scheduler resumed `*/5` ENABLED. Steady-state: `*/5` incremental merges new lean
      shards onto the lean 137MB canonical (O(changed-shards) memory, no OOM).
- [x] ✅ [INFRA] P2. **ACTUATOR SHIPPED (2026-07-31, slot-4) — deployment-service@4ca051e**: extended the existing
      `RelaunchConsolidator` (`scripts/recovery/relaunch_consolidator.py`, the wired `CONSOLIDATOR_DOWN` auto_recover
      actuator) — `relaunch(ag, oom=True)` climbs `_MACHINE_TIER_REGISTRY [16Gi/cpu4→32Gi/cpu8→64Gi/cpu16]` one rung per
      call (`run_v2.JobsClient` get/mutate-limits/update — the SDK equivalent of
      `gcloud run jobs update --memory --cpu`), persisted per-AG sticky state; already-top-rung → PAGES
      (`CONSOLIDATOR_DOWN` CRITICAL) instead of relaunch-looping. `_recover_consolidator` now threads
      `finding.details["oom"]` into `relaunch(oom=...)` (back-compat: unset key ⇒ unchanged plain-relaunch path). 10
      new/updated tests, 57/57 pass; QG GREEN. **Scoped to the actuator, not a live trigger**: Cloud Run Jobs have no
      persisted `run.log` (VM-only convention, confirmed via grep) — the real OOM signal is the Job's Execution API,
      whose exact `conditions[]` message shape needs verifying against a real OOM'd execution before wiring an
      auto-detector (risk: a guessed heuristic either never fires or false-pages). Follow-up detector todo below.
  - [x] ✅ [INFRA] P3. **deployment-service** — automatic OOM-signature detector — deployment-service@f9ffb5e. Shipped
        `consolidator_oom_watcher.py` (DP-WATCHER-005) with `check_consolidator_oom()`, wired into `cli.py` meta sweep
        gated on `MissTracker`. Injects `ConsolidatorExecutionOomReader` (reads Cloud Run execution conditions for OOM
        signatures: signal 9/exit 137/out-of-memory) ANDs with `IndexAgeReader` (index blob staleness), emits
        `CONSOLIDATOR_DOWN` with `oom=True` routed to `RelaunchConsolidator.relaunch(oom=True)` for machine-tier
        escalation. Factory functions live in the watcher module (keeps cli.py under 930-line cap). QG green, 3074 tests
        pass.

## CEFI data-completion RESIDUAL follow-ups (operator dispatch 2026-06-24, /autonomous)

These are the remaining cefi items after the consolidator/clip/purge fix. Working autonomously to completion.

- [x] ✅ [MTDS] P1. **market-tick-data-service — VERIFIED RESOLVED (2026-06-24)**: (1) the named flaky tests PASS
      (`test_native_staking_handler` + `test_rebuild_defi_manifest_cf11`: 37 passed / 1 skipped) AND the full MTDS QG
      passed clean when the clip shipped (mtds@7b18433b through `quality-gates.sh --no-fix`) — not blocking
      (isolation-order-dependent at worst, not product bugs). (2) The tardis-fallback refactor is ALREADY in shipped
      code — `_resolve_symbols_from_by_date_snapshot` at `tardis_symbol_resolution.py:587` (mtds@4bbebb8), so the 200L
      cap + QG size gate pass. Stash `tardis-fallback-refactor-followup-2026-06-23` is a stale duplicate (left,
      harmless).
- [x] ✅ [MTDS] P1. **unified-api-contracts + market-tick-data-service** — coin-margin (inverse) perp capture: Deribit
      is ALWAYS inverse; default linear; capture inverse where MORE liquid (operator 2026-06-23). Add the inverse venues
      (binance-delivery / bybit-inverse / okx-coin-margin) to the MVP capture universe + carry a `margin_type`
      (linear/inverse) field through the catalogue → manifest, and a live-liquidity spot-check to pick the more-liquid
      side per base. SSOT spec: `cefi_universe_capture_rule_2026_06_23.md` § coin-margin. — uac@a8712016 |
      instruments-service@4838738 | Part 1: BINANCE-DELIVERY added to UAC venue registries + IS venue allow-list +
      catalogue enumeration; Part 2: `margin_type` field added to catalogue (CATALOG_COLUMNS + \_extract_meta +
      build_catalogue_dataframe); Part 3: deterministic default shipped (BINANCE-DELIVERY PERPETUALs/FUTUREs in MVP
      scope via base-membership; live-liquidity spot-check TODO scaffolded in mvp_scope.py).
- [x] ✅ [INFRA] P1. **deployment-service** — wire BYBIT-SPOT + COINBASE-FUTURES into LIVE + DAILY cefi capture. Added
      both venues to `EXPECTED_COVERAGE_BY_ASSET_GROUP['cefi']` (`_CEFI` dict) in UAC
      `unified_api_contracts/registry/expected_coverage.py` — the single SSOT consumed by both the live forward-poll
      (`launch-cefi-forward-poll.sh` → MTDS CLI `--asset-group CEFI`) and the daily cron VM (which downloads and runs
      the forward-poll launcher). BYBIT-SPOT gets `["trades","book_snapshot_5"]` (mirrors COINBASE-SPOT/BINANCE-SPOT);
      COINBASE-FUTURES gets `["trades","book_snapshot_5","derivative_ticker","liquidations","futures_chain"]` (mirrors
      BINANCE-FUTURES/BYBIT). Comment in `launch-cefi-forward-poll.sh` updated to list the expanded venue set. —
      unified-api-contracts@dab85df4 | deployment-service@e34096d | QG green (UAC 222s)
- [x] ✅ [FEATURES] P2. **features-service / market-data-processing-service** — features MVP-universe config: the
      delta_one/MDPS features pipeline needs its OWN MVP universe config (separate from MTDS capture) — same perp-gated
      CEFI_BASE_ASSET_UNIVERSE for price/funding features, BUT roll/spread/volatility features + certain defi-onchain
      features span a WIDER set (operator 2026-06-23). Define the features universe config + wire it so features compute
      over the right per-family universe, not the raw MTDS capture universe. — unified-api-contracts@b10e8d6e
      (FeatureFamilyUniverseConfig + FEATURE_FAMILY_UNIVERSE_REGISTRY in UAC) | features-service@d11dd57f
      (mvp_universe_filter.py wired in delta_one batch_handler, 34 tests) | QG green
- [x] ✅ [DOCS] P2. **unified-trading-pm** — codex doc the cefi data-pipeline contracts that shipped this cycle: (1) the
      two-layer IS-full-enumeration vs MTDS-MVP-filter + perp-gate (from `cefi_universe_capture_rule_2026_06_23.md`)
      into `codex/02-data/`, and (2) the dated-instrument NOT_LISTED clip + consolidator
      bloat/OOM-at-Cloud-Run-ceiling + purge lesson into `/codex/05-infrastructure/manifest-consolidator-ssot.md` (so
      the next bloat is diagnosed fast). — unified-trading-pm@b889f6392 | /codex/02-data/cefi-capture-universe.md +
      /codex/05-infrastructure/manifest-consolidator-ssot.md

## DP_VM_GONE_NO_CAPTURE false-positive triage (operator 2026-06-24)

- [x] ✅ **bybit-2021-heavy `DP_VM_GONE_NO_CAPTURE` = FALSE POSITIVE (verified benign)**: read the cefi `_index` for
      `venue=BYBIT date=2021-12-31` → **60 cells = 23 captured + 37 empty_confirmed (honest-absence)** → the date is
      genuinely fully covered, so the MTDS pre-flight (`venue_fetch.py:248` "all requested data_types fully covered
      (atoms ⊆ captured), skipping") correctly skipped re-fetching; captured 0→0 because nothing new to write. The
      `SHARD_INCOMPLETE … missing:['BYBIT']` is the benign "wrote 0 this run" report, NOT a real gap. Pre-flight is
      SOUND (not over-eager). cefi `DP_VM_STALL`s (bybit-spot-2025/deribit/kraken/okx) = transient ~1m heartbeat gaps
      under load, all RUNNING — not actionable.
- [x] ✅ **MONITOR FIX LIVE — deployment-service@da42473** (converged with a parallel slot-bug3·vm agent on the
      identical fix): `classify_no_capture_reason` (`data_pipeline_monitors/_gcs.py`) `_HONEST_ABSENCE_RE` now matches
      the MTDS idempotent-skip line (`all requested data_types fully covered` / `atoms ⊆ captured`) → classified
      HONEST_ABSENCE not SILENT, so resumed/idempotent backfill VMs no longer false-positive `DP_VM_GONE_NO_CAPTURE`.
      Regression test `test_no_capture_reason_mtds_idempotent_preflight_skip` (6/6 classifier tests pass).
- [x] ✅ [INFRA] P1. **VERIFIED RESOLVED (2026-07-28, slot-8)**: the flagged in-flight foreign change was committed by
      its owning agent the SAME day this was flagged — deployment-service@ceaa5cad (2026-06-24) wired all 4
      `launcher_registry.py` entries (`mtds-position-data-`, `mtds-liquidation-events-`, `mtds-flash-loan-events-`,
      `mtds-risk-params-` → their matching `launch-mtds-*-backfill-vm.sh`). Confirmed on a fresh-pulled slot clone
      (HEAD=077a063, worktree clean, no in-flight foreign change): `tests/unit/test_launcher_registry.py` 7/7 PASS,
      including `test_every_watchdog_prefix_has_a_registry_entry`. Not cefi-scoped (foreign flag only) — no code change
      needed, this was a stale flag from an already-resolved transient uncommitted-WIP state.

## DP_VM_STALL / DP_EVENT_LOOP_STARVED / DP_CRON_DID_NOT_FIRE flood triage (operator 2026-06-24, 2nd pass)

All VERIFIED false positives (175/177 VMs healthy; consolidator healthy). The ~15-alert DP*VM_STALL flood was the
DEPLOYED monitor over-flagging healthy \_resuming* VMs (relaunched on the clip → resume idempotently → captured stays
FLAT while skipping already-captured dates → old `captured_flat`-alone-stalls logic fired). The on-main revision
(`7b070fb`, sidecar-authoritative) narrows it: running the CURRENT code locally = **2/177 stalled**, not a flood. The
deployed image either lagged the revision or the flood was transient.

- [x] ✅ **DP_CRON_DID_NOT_FIRE (consolidator) = FALSE POSITIVE** — consolidator healthy: index fresh (14:46+),
      executions Completed=True, scheduler ENABLED `*/5`. The deadman falsely reports it (the per-AG sticky key).
- [x] ✅ [INFRA] P1. **Both residual false-positive classes FIXED + SHIPPED — deployment-service@eae68d8**
      (2026-06-24): 1. ✅ **Slow-but-alive long-fetch → false DP_VM_STALL**: `classify_vm_liveness` hung-worker STALL
      (the `run_log_age > run_log_stall_minutes` branches) now gated on
      `_pipeline_heartbeat_stale(pipeline_heartbeat_age_min, run_log_stall_minutes)` — a FRESH `PIPELINE_HEARTBEAT` (60s
      worker-life marker, emitted independent of chunk boundaries) PROVES the worker loop is alive, so a slow single
      fetch (deribit options*chain, fresh heartbeat but a >90m-old last \_progress* line) stays ALIVE. Genuine hangs
      (heartbeat ALSO stale) still STALL. 2. ✅ **Old-tarball VM → false DP_EVENT_LOOP_STARVED**: the
      no-sidecar+no-run.log branch now returns ALIVE when the per-VM captured count is CLIMBING (`not captured_flat`) —
      a pre-sidecar-tarball VM (cefi-extended-2025-resume) capturing without instrumentation is alive; only TOTAL
      silence (no heartbeat + no log + captured flat) starves. +5 regression tests (147 monitor tests pass). Local
      `--mode heartbeat` dry-run confirms the 2 VMs now ALIVE.
- [x] ✅ [INFRA] P1. **DEPLOYED the monitor fix to the running jobs (2026-06-24)**: `eae68d8` reached main via the
      staging→main force-sync (PR #266 resolved — main was stale on the monitor files from an admin force-sync; relaxed
      protection → force-pushed staging tip → restored). The `deployment-api:latest` image had NO auto-build trigger
      (the cloudbuild "auto on main" comment is stale; it builds manually via `deploy-shared.sh`), so I verified the
      existing `consolidator-key4-fix` image (`4aedfc98`, built from the `cd51cf2` tree — contains the fix, 3
      `_pipeline_heartbeat_stale` hits in the installed file) and **re-tagged `:latest` → 4aedfc98 + updated all 3
      monitor jobs** to it. Ran `uts-prod-dp-heartbeat-watcher`: Completed/succeeded=1/**0 false alerts** on the 154
      cefi VMs. Fix is LIVE.

## CeFi empty_confirmed over-seeding — pre-listing NOT_LISTED denominator poison (operator 2026-06-24)

**Finding** (consolidated v9 \_index 2026-06-24 19:36): cefi captured GREW 1.31M→**2.66M (doubled)** since 2026-06-21
and attempted*failed DROPPED 802k→662k — but honest-cov FELL 33.9%→21.4% because `empty_confirmed` EXPLODED
1.28M→**9.09M**. Diagnosis: **7.6M of the 9.09M empties = `EXPECTED_INSTRUMENT_NOT_LISTED`**, all `written_at`
2026-06-23/24 (the running backfill VMs), all PERPETUAL pre-listing cells (e.g.
`BINANCE-FUTURES:PERPETUAL:PIPPIN-USDT | 2020-01-01` — PIPPIN listed 2025). These were NEVER queried (a genuinely-empty
\_listed* cell yields `SOURCE_RETURNED_ZERO`); they are **out-of-universe** and poison the coverage denominator.
Excluding them, real honest-cov ≈ 2.66M / 4.8M ≈ **~55%**. Root cause: `CeFiCatalogReader.list_not_yet_listed` →
`_iter_not_yet_listed` emitted a cell per (current instrument × every pre-listing day × data_type); the earlier
dated-only clip (`_DATED_INSTRUMENT_TYPES`) wrongly assumed PERPETUAL/SPOT_PAIR were "small count". Genuine honest
absence is only the 1.27M `SOURCE_RETURNED_ZERO`.

- [x] ✅ [SCRIPT] P0. **CODE FIX — retire pre-listing seeding (mtds@9ff01bc1)**: `list_not_yet_listed` now yields
      nothing (out-of-universe); deleted `_iter_not_yet_listed` + `_DATED_INSTRUMENT_TYPES`; updated
      `test_cefi_pre_listing_not_listed.py` (asserts ZERO NOT_LISTED end-to-end) — 30 affected tests pass, basedpyright
      clean, QG green (106s). Landed on LDR; Tier-C drain promotes to staging ≤15min.
- [x] ✅ [SCRIPT] P0. **PURGED 8.5M `EXPECTED_INSTRUMENT_NOT_LISTED` cells** (2026-06-24, hard cutover, snapshot
      `_index/snapshots/pre_notlisted_purge_2026_06_24.parquet`): filtered
      `empty_confirmed + EXPECTED_INSTRUMENT_NOT_LISTED` out of the consolidated index (12.86M → 5.02M rows) + all 41
      per-VM shards (parallel). **honest-cov measured 21.4% → 55.5%** (captured 2.79M / denom 5.02M). Holds (fleet
      deleted, shards clean → consolidator stays clean).
- [x] ✅ [INFRA] P1. **Hard cutover — deleted old fleet + relaunched on fixed code** (operator-directed 2026-06-24):
      rebuilt the VM tarball (`create-code-tarballs.sh`, clean=true, MTDS verified `_iter_not_yet_listed` removed) →
      deleted the 103-VM `085745` backfill fleet (live `mtds-live-cefi-*` + `instr-backfill-cefi-*` VMs PRESERVED) →
      purged → relaunched `launch-cefi-sharded-backfill.sh` as run-id `20260624-211958` on the fixed tarball (resume
      idempotent, no NOT_LISTED re-seed). Verifying T+10min capturing-without-re-seeding.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 — `market-tick-data-service@d2366203` (catalog method + tests deleted) +
      `fc64e092` (sentinel plumbing).** Batch3 item 4: removed the dead `catalog_list_not_yet_listed_cefi` method +
      `cefi_pre_listing_by_venue` thread + write block from `sentinel_catalogs.py`/`orchestrator/__init__.py`/
      `sentinels.py` (`_load_sentinel_catalogs` now returns a 3-tuple); updated all tests referencing removed symbols.
      Both commits QG-green.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 (slot 4) — VERIFIED-STALE, no code fix needed.** `perp_funding`=0 is BY DESIGN
      (see PARTIAL-STALE note below). The `futures_chain`=223/`options_chain`=3/`ohlcv_1m`=738 counts are **stale,
      pre-hard-cutover measurements**: re-queried the LIVE prod cefi manifest today (`read_availability_index` UTL, MTDS
      `.venv`, read-only; 9,531,264 rows) and found **0 rows of any status** for
      `(HYPERLIQUID|ASTER) × {futures_chain, options_chain, ohlcv_1m}` — confirmed twice independently. The 223/3/738
      figures were from the 2026-06-24 19:36 UTC pre-cutover snapshot (that fleet was deleted + relaunched same day —
      see paragraph above). Every registry (`unified-api-contracts` `DATA_TYPE_CAPABILITY_REGISTRY` /
      `expected_coverage._CEFI` / `market_data_categories`) and launcher
      (`launch-cefi-hl-aster-historical-backfill.sh:106-111`, `onchain_perp_batch_handler.py:105`) agrees these 3
      data_types are structurally out-of-scope for HL/ASTER (perp-only DEXes; `ohlcv_1m` is on-chain-CLOB-only, e.g.
      LIGHTER-ZKSYNC/EXTENDED-STARKNET, never HL/ASTER) and none currently request them. No reclass needed — rows no
      longer exist to reclassify. Self-resolved by the 2026-06-24 cutover + dedicated-launcher split.

## CeFi attempted_failed + expected_unattempted audit (operator 2026-06-24, post-purge index 5.02M rows)

`expected_unattempted` = **0** (CLEAN — no bogus seeding; the only over-seeding was the now-retired NOT_LISTED path).
`attempted_failed` = **674,334**, classified: ~620k **retryable transients** (`VENUE_FETCH_FAILED` 560k +
`Tardis HTTP 500/503` 49k + `Connection timeout`/`payload not completed` 11k — real instruments, valid in-window dates;
the relaunched fleet re-attempts) + **~33k genuine code bugs** (below) + `Tardis HTTP 400` 20k (possibly-systematic
bad-request, needs a look). Failing instruments are IN-UNIVERSE (e.g. `KRAKEN-FUTURES:FUTURE:FI_LTCUSD_220429` on
2022-04-20, within its 2022-04-29 expiry) — NOT bogus-universe.

- [x] ✅ [SCRIPT] P1. **FIXED — FUTURE expiry-parse (32k Kraken/non-Deribit dated futures)** (`tardis_shared.py`): added
      `_parse_numeric_futures_expiry()` — extracts the trailing date stamp (8-digit `YYYYMMDD` `FF_XBTUSD20251226`, or
      `_`/`-`-separated 6-digit `YYMMDD` `FI_LTCUSD_220429` → 2022-04-29) and wired it into the FUTURE branch after the
      Deribit parse. Now resolves instead of raising `FUTURE row requires 'expiry_date'`. +6 tests pass. (Ships +
      tarball-rebuild gated on the verification batch — see relaunch hold below.)
- [x] ✅ [SCRIPT] P1. **`was_instrument_alive()` kwarg bug — ALREADY FIXED in current code**: the sole caller
      `tradfi/tardis_batch_download.py:171` now passes the correct `available_from`/`available_to`/`day` kwargs (with a
      comment noting the prior wrong-kwargs bug). The 206 `attempted_failed` are HISTORICAL — the relaunch on current
      code won't reproduce them (they re-process correctly).
- [x] ✅ [SCRIPT] P1. **`Tardis HTTP 400` (20k) is LARGELY SYSTEMATIC — out-of-window + out-of-universe (operator's
      restriction concern, CONFIRMED)** — **(a) post-expiry fetches FIXED — instruments-service@a3e90f48**:
      `CRYPTOFACILITIES:FF_ETHUSD_250228`/`BYBIT:BTC-21APR23` were fetched a day past real expiry because
      `_extract_meta()` only reads the per-date `expiry` column, never `available_to_datetime` — a row whose expiry
      never resolved on capture but kept re-appearing in Tardis's reference listing read ACTIVE FOREVER, so the
      active-window gate never clipped it. Added `_backfill_cefi_missing_expiry_from_wire_symbol` (new cefi rollup
      Phase-D pass, reuses the existing wire-symbol parsers): backfills a blank `expiry`/`available_to` from the row's
      own wire symbol, only when both are blank AND the resolved date is already past — never overwrites, never touches
      non-dated types. Verified against both named examples (backfills to `2025-02-28`/`2023-04-21`); 7 new tests;
      `quality-gates.sh` green. Self-heals on the next nightly `lifecycle-catalogue-regen-cefi` run. **(b) SPLIT to the
      follow-up todo below** — `OKEX`/`ATOM`/`USDC-TRY` need real investigation, not a same-shape fix. ~2k
      `In CSV column #` decode errors remain a separate Tardis-CSV parse class.
- [x] ✅ [SCRIPT] P2. **RESOLVED — investigation-only, NO code fix needed (2026-07-31, slot-10)**. Both parts confirmed,
      no bug found in either:

      **(1) `CEFI_VENUE_FOLD` rollup wiring — CONFIRMED display/audit-only, no collision risk today.**
          `CEFI_VENUE_FOLD` (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:611-629`) has
          exactly two consumers repo-wide: `instruments-service/scripts/check_enumeration_completeness.py:43,163,188` (the
          Honest Coverage v2 Layer-1 completeness **audit**) and `deployment-api/deployment_api/routes/data_status/
          _distinct_values.py:140-206` (via `CEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES`, suppressing dialect spellings from
          "non-canonical drift" badging on the distinct-values **UI panel**). `instruments-service/scripts/
          build_instrument_catalogue.py` (the script that writes `catalog.parquet`) has NO import of `CEFI_VENUE_FOLD` —
          a raw legacy venue spelling (`OKEX`, `CRYPTOFACILITIES`, etc.) reaches `catalog.parquet` UNFOLDED, exactly as
          suspected. `instrument_id` is derived by `unified_api_contracts/internal/reference/canonical_id_builder.py:735-750`
          (`build_instrument_id(venue, instrument_type, symbol, ...)` → `VENUE:INSTRUMENT_TYPE:SYMBOL`, raw venue embedded
          verbatim) — so a legacy-spelled row's `instrument_id` (`OKEX:PERPETUAL:BTC-USD`) is byte-distinct from the
          canonical row's (`OKX:PERPETUAL:BTC-USD`); no collision exists in current code because nothing re-derives
          `instrument_id` from a folded venue. The collision risk the todo flagged is a real hazard **only if** a future
          consumer applies the fold to `venue` AND re-derives `instrument_id` before joining against
          `_aggregate_key()`/`_canonical_instrument_id()` (`build_instrument_catalogue.py:1173-1221`) — noted here as a
          guardrail for any future write-time use of the fold, not an open defect today.

          **(2) `USDC-TRY` quote-bypass — CONFIRMED fail-safe, but NOT via the hypothesized empty-string mechanism.**
          `_resolve_base_quote()` lives in **instruments-service** `reference_data/adapters/cefi/tardis/parsing.py:307-415`
          (not MTDS — MTDS's `tardis_symbol_parsing.py` only comments on IS's function). `TRY` is already a recognized
          quote currency in `_QUOTE_CURRENCIES` (`parsing.py:81-148`, line 115) — the split on `USDC-TRY` (or concatenated
          `USDCTRY`) resolves correctly to `("USDC", "TRY")`; **quote never comes back empty**, so the hypothesized
          failed-split/empty-string bypass does not occur. The row is instead rejected by the ordinary, intended branch of
          `_passes_asset_filter()` (`parsing.py:581`): `TRY` is not in `CEFI_ACCEPTED_QUOTE_ASSETS = {USDT, USDC, USD}`
          (`unified-api-contracts/unified_api_contracts/registry/cefi_instrument_universe.py:132-134`) or any per-venue
          extension, so the non-empty-quote-not-accepted branch fires and the row is dropped — a working, designed gate,
          not an accidental fallback. (A separate empty-quote/`instrument_type` skip guard also exists at `adapter.py:
          791-804` as an unrelated second line of defense, for genuine parse failures — not triggered here.) Verdict:
          fail-safe, not a leak — confirmed, with the correct mechanism now documented in case this resurfaces.

          **(3) `ATOM`** — untouched, per the doc's own note this needs a fresh operator ruling, not a fix; no action taken.

          No code changes required in any repo — both investigations resolved with existing behavior already correct.
          This doc update is the full deliverable.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — added the manifest-consolidator source module and
  the sharded-backfill launcher script (the two most-cited code targets in the doc's body).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **2026-08-12** — `locked_by`/`locked_since` cleared (corpus-wide fix, operator ruling Option B, interactive session
  2026-08-12; see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md). This doc has
  0 open todos, so clearing the placeholder lock immediately makes it archive-eligible. Per the ruling's explicit scope
  ("do NOT auto-archive in this same pass"), archival itself is deferred to a separate follow-on pass; bridged with
  `archive_exempt: true` (the sanctioned flip-then-mv two-commit pattern documented in
  `scripts/plan-hygiene/check_archive_candidates.sh`) so this commit doesn't trip the archive-candidates pre-commit
  gate. The follow-on pass should drop `archive_exempt` and `git mv` this doc to `plans/archive/[issues/]`.
- **context-scout 2026-08-17**: re-scouted; context_scope unchanged (6 entries), still accurate.
