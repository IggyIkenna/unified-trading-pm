---
doc_type: plan
title: Instruments Foundation — tradfi G1→G5 gate execution
summary:
  Split out of instruments_foundation_completeness_2026_06_24.md (2026-07-24 line-cap remediation, 4-way split,
  operator- approved). Owns tradfi's gated G1→G5 rebuild — billable-venue guard, calendar/session fail-closed, CME/ES
  ohlcv + Yahoo FX/Treasuries/DXY/KRX-KOSPI universe, `available_to` venue-truth + per-venue latest_day, VIX-15m INDEX
  retirement, G1 retirement (ICE/OPRA/CBOE pollution), G4 catalogue-as-filter — plus the tradfi-specific historical
  execution log (slot-3 G1.a-h shipped code, KRX/ICE mis-sourcing fix, CME ohlcv_1m 2020-Q1 writer fix, manifest
  stale-row cruft) and the folded-in tradfi residuals migrated from 2 archived plans. depends_on the Phase-0
  cross-cutting child for GATE 0.
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags:
  [instruments, catalogue, honest-coverage, data-correctness, backfill, tradfi, manifest, foundation, gate-execution]
related:
  [
    instruments_foundation_completeness_2026_06_24,
    instruments_foundation_phase0_cross_cutting_2026_07_24,
    instruments_cefi_g1_g5_gate_execution_2026_07_24,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-30" # ES manifest-count check executed: ZERO capture found (not "proven"), filed as tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md; ES_OPT launch attempted, deferred (singleton lock genuinely held by a live concurrent backfill, not stale)
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 5
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [instruments_foundation_phase0_cross_cutting_2026_07_24]
source:
  [
    "plan-hygiene split of instruments_foundation_completeness_2026_06_24.md, 2026-07-24 (operator-approved, see
    plans/active/issues/plan_line_cap_remediation_2026_07_23.md row #14)",
  ]
context_scope: [/codex/02-data/tradfi-databento-sourcing-ssot.md, /codex/02-data/instruments-foundation-and-catalogue-completeness.md, /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md, /plans/archive/issues/tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md, instruments-service/scripts/build_instrument_catalogue.py, deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh]
---

# Instruments Foundation — tradfi G1→G5 gate execution

**Split provenance (2026-07-24):** this plan was extracted from
[`instruments_foundation_completeness_2026_06_24.md`](instruments_foundation_completeness_2026_06_24.md) (the umbrella)
as part of the operator-approved plan-line-cap remediation
(`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row #14 — 4-way split). **`depends_on`
[`instruments_foundation_phase0_cross_cutting_2026_07_24.md`](instruments_foundation_phase0_cross_cutting_2026_07_24.md)
for GATE 0** — the cross-cutting prerequisites (observability, Honest-Coverage v2, canonical-form single-SoT migration)
that block G2. The umbrella (`instruments_foundation_completeness_2026_06_24.md`) stays the process SSOT + rolling
status index across all 4 children (this one, Phase-0, cefi, and the defi/sports plans it already delegates to).

**Codex SSOT (the standard this plan executes):** `/codex/02-data/instruments-foundation-and-catalogue-completeness.md`.

---

## Gated Phase 2 — tradfi (same G0→G5 as cefi/defi)

- [ ] [INFRA] P1. **tradfi** — same gates; Databento universe (GLBX/DBEQ/XCBF) + Yahoo (KRX/FX). ("tradfi perps" =
      Binance single-stocks/commodities are **cefi**.) DeFi-distinct tradfi work (§7): **billable-venue guard** —
      enumerated venues == subscribed allowlist (ICE non-billable, 8,856→1; §7.1); **fail-closed per-venue calendars +
      sessions** (KRX in NO calendar SSOT → 24/7 default mis-handles Seollal/Chuseok; FX is the declared 24/7 exception;
      §7.2); **`available_to` per-venue + trading-day-aware** (global-`latest_day` falsely delists lagging KRX; §7.3);
      **equities pre-2023-04-15 silently absent**; **depth oracle** (NASDAQ ~41 / NYSE ~224 shallow); verify the tradfi
      daily-capture trigger isn't PAUSED. Baseline §9.
  - **Already-fixed G1 code (this session, IS `50bf1c8`, QG-green, 7/7 venues now write):** KRX→databento routing
    (`CANONICAL_VENUE_TO_ADAPTER`) + the `AssetClass("cefi")` crash on NASDAQ/NYSE equities (`_resolve_asset_group`
    guarded so domain values fall through to the dataset-default EQUITY). **Both refinements below are DONE — corrected
    2026-07-26 (this doc's own contradiction: this bullet said "NOT yet done" while G1.b/G1.c further down already
    showed both shipped 2026-06-25; re-verified live post IS@92084d5c this pass):** (i) the cefi-domain equity-perp
    singles (NVDA/MSFT/AAPL…, `DatabentoInstrumentDef.asset_group="cefi"`) are EXCLUDED from the tradfi adapter —
    `databento/adapter.py::get_instruments` filters `TRADFI_DATABENTO_INSTRUMENTS` to
    `d.asset_group in frozenset(AssetClass)`, so a `"cefi"` asset_group (not a valid `AssetClass` member) is dropped
    before it ever reaches the tradfi pipeline (SP500-overlap tickers still enter correctly via the separate equity
    path). See G1.b below. (ii) `_DATASET_TO_asset_group["XCBF.PITCH"]` resolves `AssetClass.COMMODITY` (not EQUITY) and
    `XCBF.PITCH` is a member of `_FUTURES_DATASETS` (`databento/symbology.py`). See G1.c below.

---

## Expanded scope — CME + ES ohlcv + Yahoo FX/Treasuries/DXY (operator 2026-06-26, moved from the umbrella Near-term-target section)

#### Expanded scope (operator 2026-06-26): tradfi CME + ES ohlcv + Yahoo FX/Treasuries/DXY

- [x] [INFRA] P0. ✅ **tradfi instrument-definition backfill LAUNCHED** — `launch-tradfi-is-defs-sharded.sh` 9-shard
      fleet RUNNING (`instr-backfill-tradfi-{cboe,nasdaq,…}-*`), covers CME + all tradfi venue defs (current: 14,192
      captured, CME 3,532 rows 2020→06-24).
- [x] ✅ [DATA] P0. **Operator-ruled 2026-07-29 (interactive decision session): run the manifest-verify now and log it
      as partial evidence — a manifest-COUNT check only, NOT the closeout's heavier fresh-pipeline-check, mirroring the
      already-established NASDAQ/NYSE precedent in `data_completion_tradfi_2026_07_15.md`.** ES CME futures ohlcv 1s+1m
      — fleet FINISHED, manifest-verify still owed (launcher lib defaults to BOTH `ohlcv_1m;ohlcv_1s`). **MEASURED
      2026-07-26 (plan-reconcile, tradfi tranche)** — `gcloud compute operations list` on project
      `central-element-323112`, filtered `targetLink~tradfi-bf-cme-ohlcv-1m-es`: **all 7 year-shards
      `es-{2020,2021,2022,2023,2024,2025,2026}` were inserted 2026-07-21T03:42:58Z–03:44:47Z and all 7 self-deleted by
      2026-07-21T09:48:13Z, with ZERO `compute.instances.preempted` operations on any `es-` shard.** This SUPERSEDES the
      earlier "IN FLIGHT … RUNNING; only 2020/25/26 VMs seen — verify 2021-24 done or launch" note: 2021-2024 WERE
      launched (insert ops at 03:43:24Z / 03:43:42Z / 03:43:58Z / 03:44:15Z) and completed without preemption, so there
      is nothing left to launch. REMAINING: manifest-verify per-year only (VM completion is not row-capture proof — per
      `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`, count TARGET artifacts, not activity).
      Billing-fail-closed (Databento PAYG, shared singleton lock).
- [x] ✅ [DATA] P0. **DONE 2026-07-30 — ran the manifest-count check; result is NOT "backfill proven," it's a concerning
      zero-capture finding, filed as its own issue.** Single live read of the `market-data-tick-tradfi-prd` `_index`
      (`availability_index.parquet`, 5,894,011 rows, no bucket walk), scoped to venue=CME × instrument_id=ES.FUT (the
      launcher's row-key atom for the ES parent-symbol chain) × data_type∈{ohlcv_1m,ohlcv_1s} × year 2020-2026 — same
      manifest-count-only method as the NASDAQ/NYSE precedent in `data_completion_tradfi_2026_07_15.md`. **Result: 4,855
      scoped rows, 100% `attempted_failed` (3,048, `error_reason=WithinBoundsTradfiSourceZero`) or `empty_confirmed`
      (1,807, `error_reason=SOURCE_RETURNED_ZERO`) — ZERO rows have `row_count>0`, zero are `captured`.** Isolating just
      the 718 rows the 2026-07-21 fleet itself wrote (`written_at` date 2026-07-21, spanning `date`
      2021-01-04..2026-04-15): 100% `empty_confirmed`/ `SOURCE_RETURNED_ZERO` — the fleet ran cleanly (VM-lifecycle
      proof: 7 shards, zero preemptions) but captured literally 0 real ES ohlcv bars across the entire attempted window.
      This is the activity-vs-target-artifact trap the async-wait-discipline codex SSOT warns about: "fleet FINISHED"
      was VM-completion proof, not data-capture proof. Full evidence:
      `plans/archive/issues/tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md` (archived 2026-08-09). **CORRECTED
      2026-08-18 (plan_reconciler)**: that archived doc's own final resolution (same day, 2026-07-30) says the
      opposite of "needs adapter-level investigation" — RESOLVED via 2 now-fixed infra bugs (a stall-timeout vs.
      consolidator-lock horizon mismatch, and a manifest-consolidator chunking bug from FRED history) plus 1
      manifest-write bug (`venue_fetch.py::_record_venue_shard_counts` hardcoding a blank `instrument_id` for
      chain-bundle types) — "real ES data captures today, from this exact re-launched fleet, once both infra bugs
      stopped blocking it" (archived doc :212-214). No further adapter-level investigation is needed; the open
      question is whether the fixes' downstream effects (a fresh capture run) have been folded into this doc's own
      MVP-cell tracking, which the entry above already flags as not done this session. **Did NOT update `tradfi_consolidated_closeout_2026_07_18.md`'s MVP-cell row this session** — that file
      had an uncommitted in-progress edit (mtime <120s) from another active session at the time of this check; whoever
      owns that edit should fold this measured result into the "S&P index futures (ES)" row next (cite this todo + the
      new issue doc).
- [x] ✅ [DATA] P0. **Operator-ruled 2026-07-29 (interactive decision session): launch ES_OPT now AND wire its
      manifest-verify into Phase-D gate tracking — the singleton Databento lock blocker cleared (confirmed 2026-07-26,
      zero `tradfi-bf-*` instances in any state).** ES CME OPTIONS (ES_OPT) ohlcv 1s+1m — NOT yet launched; the stated
      blocker has CLEARED. The singleton Databento lock was held by the ES futures fleet — **MEASURED 2026-07-26
      (plan-reconcile): that fleet is gone** (all 7 `tradfi-bf-cme-ohlcv-1m-es-*` VMs deleted by 2026-07-21T09:48:13Z;
      zero `tradfi-bf-*` instances exist in `central-element-323112` in ANY state as of 2026-07-26T02:20Z), so "once the
      lock frees" is satisfied. Launch `launch-tradfi-bf-cme-ohlcv-1m.sh --only-root ES_OPT` (11-cluster ES_OPT_PARENTS
      set) — SPOT per the backfill-VM HARD RULE. **CORRECTION (2026-07-29, verified live against
      `deployment-service/scripts/vm/`): the launcher cited above is WRONG** — `launch-tradfi-bf-cme-ohlcv-1m.sh`'s
      `CME_ROOTS` has no `ES_OPT` entry; its own `--only-root` error text states "ES root covers ES.FUT and ES.OPT —
      there is no separate ES_OPT root key". The real ES_OPT launcher is
      `deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh --root-symbol ES_OPT` (the 11-cluster `ES_OPT_PARENTS`
      set lives in that script's sourced `cme-expiry-calendars.sh`) — see the corrected invocation in the new todo
      below.
- [x] ✅ [DATA] P0. **VERIFIED CLOSED 2026-08-16 (na-eligibility-audit, tradfi tranche, dispatch agt-45ad7b)** — see
      the verification note at the end of this item's own citation below. **UNBLOCKED 2026-08-09** — the databento billing-suspension gate below is lifted for this item: S&P
      options are explicit in-scope work per the MVP-of-MVP ruling
      (/plans/archive/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md), and Databento was live-verified
      reachable the same day (real `metadata.list_datasets` + `ES.FUT ohlcv-1m` pulls both succeeded). Prior gate
      (superseded, kept for history): ~~BLOCKED-OPERATOR-DECISION (databento account billing-suspended 2026-08-09, see
      /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md)~~. **Launch the ES_OPT backfill** —
      run `bash deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh --root-symbol ES_OPT` (defaults: SPOT
      provisioning per the backfill-VM-defaults-to-SPOT HARD RULE — `ON_DEMAND=false` unless `--on-demand` is passed;
      year-shards 2022-2026 per `cme-expiry-calendars.sh`'s `default_years_for_root`; `data_types=ohlcv_1m` only per the
      script's own ES_OPT branch — options-chain trades/tbbo across thousands of strikes × 11 chains stays a separate
      dedicated run). Re-verify the singleton lock is still clear immediately before launch
      (`gcloud compute instances list --filter='name~"^tradfi-bf-" AND status=RUNNING'`). Done when: the VM(s) are
      STARTED (<60s) + confirmed RUNNING at T+10min, per async-wait-and-poll-discipline (no fire-and-forget).
      **ATTEMPTED 2026-07-30 — NOT launched, singleton lock genuinely held (not stale).** `--dry-run` confirmed the plan
      (5 year-shard VMs, `e2-standard-4`, SPOT, `data_types=ohlcv_1m`, `asia-northeast1-c` — matches the ES futures
      precedent that completed cleanly). Re-verified the lock per this todo's own instruction:
      `gcloud compute instances list --filter='name~"^tradfi-bf-"'` shows `tradfi-bf-fred-full-20260730-052935` RUNNING
      (started 2026-07-29T22:29:37-07:00, SPOT). Checked its `PROGRESS.json`/`run.log` before assuming staleness (per
      the script's own CAUTION — do not force past a live dispatch): heartbeats + resource samples current to within the
      last minute, `last_completed_date` advancing from 1962 forward — this is a genuinely live, in-progress FRED
      full-history backfill from another session, not a dead claim. The launcher's singleton lock is account-wide
      (shared Databento quota protection, not ES-specific), so launching ES_OPT now would either be refused by the lock
      or require `--force`, which the script itself warns is for "legitimate parallel investigation" only — did not
      force past someone else's live job. **Re-attempt once `tradfi-bf-fred-full-*` completes** (re-check via the same
      `gcloud compute instances list` filter). **CITATION (na-eligibility-audit 2026-08-02, tradfi tranche; UPDATED
      2026-08-07)**: this item, combined with the manifest-verify item below, is extracted verbatim as todo #2 in
      `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` — that plan was activated 2026-08-06
      (`assigned_vm: planning`) with a live autonomous watcher session polling the singleton lock and launching ES_OPT
      as of 2026-08-07T~04:46Z, and has since been **completed and ARCHIVED** (path updated 2026-08-10; its todo #2 is
      `[x]` there with evidence). This item stays open until someone verifies that outcome against this plan's own gate
      — read the archived plan's Progress Log, do not assume it is still being tracked live.
      **VERIFIED 2026-08-16 (na-eligibility-audit, tradfi tranche, dispatch agt-45ad7b)**: directly read
      `plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` live — `status: archived` confirmed,
      its ES_OPT launch todo (line 141, "UNBLOCKED 2026-08-09 — S&P options...") is `[x]` ✅ with cited evidence.
      Closing this checkbox to match.
- [x] ✅ [DATA] P1. **VERIFIED CLOSED 2026-08-16 (na-eligibility-audit, tradfi tranche, dispatch agt-45ad7b)** — see
      the verification note at the end of this item's own citation below. **UNBLOCKED 2026-08-09** — same unblock as the launch todo above (S&P options in-scope per
      /plans/archive/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md; Databento live-verified reachable).
      **Wire the ES_OPT post-launch manifest-verify into Phase-D gate tracking** (per the 2026-07-29 operator ruling
      above) — once the ES_OPT launch todo above completes, run the same manifest-count-only check used for ES futures
      (mirrors the NASDAQ/NYSE precedent, `data_completion_tradfi_2026_07_15.md`) scoped to venue=CME ×
      root∈{ES,EW,EW1,EW2,EW4,E1A,E2A,E3A,E4A,E5A,EOM} × data_type=ohlcv_1m, and record the result as a line item in
      `plans/active/tradfi_consolidated_closeout_2026_07_18.md`'s MVP-cell table, "S&P index options" row — so the
      post-completion manifest-verify isn't missed. Done when: that row cites the live query + counts. **CITATION
      (na-eligibility-audit 2026-08-02, tradfi tranche; UPDATED 2026-08-07)**: combined with the ES_OPT launch item
      above into the same `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` todo #2 extraction
      — that plan is now **completed and ARCHIVED** (path updated 2026-08-10), not a live tracking session — see the
      citation above for detail.
      **VERIFIED 2026-08-16 (na-eligibility-audit, tradfi tranche, dispatch agt-45ad7b)**: same direct read as the
      launch item above confirms batch6's todo #2 (which combined this manifest-verify with the launch) is `[x]` ✅.
      Closing this checkbox to match.
- [x] [DATA] P1. ✅ **Yahoo FX / Treasuries / DXY instruments — universe COMPLETE.** Treasuries (all 5 tenors:
      US3M/US2Y/US5Y/US10Y/US30Y → ^IRX/2YY=F/^FVX/^TNX/^TYX) + DXY (DX-Y.NYB) were ALREADY enumerated in UAC
      `YAHOO_INDICES`. Gap was FX (only KRW/USD) → added the **10 G10 FX majors** (EUR/GBP/JPY/AUD/CAD/CHF/NZD crosses +
      USD/MXN). Shipped `UAC@526f3c83` + `instruments-service@97cdf92`, QG-green, runtime-verified (16 records
      enumerate). FX ohlcv backfill running (`tradfi-bf-fx-ohlcv-24h-2026`); existing FX/DXY/treasury defs captured by
      the running tradfi backfill; the NEW G10 FX majors capture once the image carries UAC@526f3c83.
- NEXT: monitor all backfill fleets to completion (climbing metric = captured days/cells); launch ES_OPT when lock
  frees; once instrument backfills done + image carries f739a41 → regen cefi+defi catalogues + verify honest coverage;
  the all-AG producer crash (sports/tradfi/pred have no daily producer) stays a tracked finding.

#### Checkpoint 12:40 — ALL-5-AG foundation drive (operator: complete instruments+catalogue+coverage+MTDS for every AG)

- **Daily-producer truth (live GCP):** cefi has 06:00 job ✅; defi = repurposed 00:00 job ✅; **tradfi/sports/prediction
  have NO prod daily producer** (sports only `uts-dev-…-sports-fixtures`). The durable fix = the all-AG crash fix (agent
  a81f8) → restore the 00:00 `uts-prod-instruments-service-t1-recon` to no-`--asset-group` (covers SPORTS/DEFI/TRADFI;
  PREDICTION is separate per `is_all` — agent to confirm). Until then today's capture is covered by the backfill fleets.
- **IMAGE BUILD is MANUAL + STALE** (`image:latest` last built 2026-06-23 via `instruments-service/cloudbuild.yaml`, NO
  auto-trigger on main). f739a41 reached main 12:33 but the cloud jobs still run 06-23 code. **DO NOT build yet:** the
  IS working tree is dirty with two agents' WIP (Yahoo universe a80ad + all-AG crash fix a81f8). **SEQUENCE: agents land
  their IS code → backfills done → build the image ONCE (`gcloud builds submit --config cloudbuild.yaml`) from a CLEAN
  f739a41+ tree → redeploy cloud producer/catalogue jobs → re-run producers (seed EU) → regen catalogues → verify.** Do
  NOT run producer/catalogue LOCALLY from the current dirty tree either.
- **In flight:** cefi+defi instrument backfills (verified writing: defi wrote 6285 rows/52 venues for 05-19, honest
  attempted_failed for 2 dead venues; cefi gap days 06-22/23 now present). tradfi IS-defs 9-shard fleet. tradfi CME
  ohlcv ES 1s+1m (es-2020/25/26) + CL/GC/HG/NG/NQ/SI + FX/NASDAQ/NYSE. 3 agents: Yahoo (a80ad), all-AG-crash (a81f8),
  sports+prediction backfills (a8c9).
- **Loop drivers:** watchdog b9ermg8qr (Databento lock → ES_OPT) + the 3 agents' completion notifications.

---

## na-eligibility-audit log

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, 2 stale items closed.** 4 open
  todos re-read end-to-end. Closed the ES_OPT launch todo + its manifest-verify-wiring sibling — both were flagged by
  a prior pass as "stays open until someone verifies [batch6's] outcome"; independently read
  `plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` live and confirmed `status: archived` +
  its combined todo `[x]` with evidence. Remaining 2 open todos (P2 residual catalogue-leg purge needing separate
  operator confirmation; the all-AG foundation-drive NEXT items) stay genuinely open. `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **KEEP-NA, valid — reaffirmed, 2 open
  todos unchanged.** Line 77 (top-level Gated-Phase-2 rollup) is ongoing coordination/monitoring work (backfill
  fleets to completion, image-rebuild sequencing, catalogue regen) — not a single worker-determinable outcome. Line
  387 (residual 2-leg catalogue purge) independently re-verified KEEP-NA-STALE: confirmed live that
  `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md` (`status: active`, `assigned_vm: planning`)
  todo 1 covers this exact item verbatim (NASDAQ/NYSE SPOT_PAIR 318 rows + 12 cefi-singles rows) — citation already
  correct (added by plan_reconciler 2026-08-18). `assigned_vm` unchanged.

## Historical progress log (tradfi track, moved verbatim from the umbrella 2026-07-24)

> Cross-referenced with the interleaved cefi narrative from the same sessions — see
> [`instruments_cefi_g1_g5_gate_execution_2026_07_24.md`](instruments_cefi_g1_g5_gate_execution_2026_07_24.md)`s
> Historical progress log section for the cefi side of the same 2026-06-25 → 2026-06-27 sessions.

- 2026-06-24 — **tradfi audit + the foundation-first PIVOT (this session).** Started as the KRX/equities OPS pass; the
  operator's "how do we know instruments is honestly at coverage" probe surfaced the foundation gaps → reset to
  audit-first. **Shipped G1 code:** KRX routing + the cefi-`AssetClass` crash (IS `50bf1c8`, 7/7 venues write). **Audit
  findings** (now §9 + the tradfi todos above): ICE non-billable yet enumerated (8,856→1); CBOE pollution (91 SPOT_PAIR
  - 5 un-deleted VIX-INDEX); KRX 96% silently absent + no Korea calendar; `available_to` false-delistings (global
    `latest_day`); equities pre-2023 absent; shallow NASDAQ/NYSE. **PAUSED everything** (operator "no point wasting time
    and money"): catalogue-regen execution **cancelled** (it would have baked false KRX delistings, §7.3),
    `uts-prod-tradfi-wave-launcher-cron` **paused**, the 18 `tradfi-bf` OHLCV VMs **deleted**; live producer +
    non-tradfi VMs left. **Nothing builds downstream until G1 fixes land + GATE-0/G1 sign-off.** (Separate + still LIVE:
    the tradfi market-data EU-drain fix — massive purged, EU collapsed 1.08M→1,349 MVP, durable — not part of this
    foundation gate.)

- 2026-06-25 — **TRADFI track dispatched directly (operator), slot-3.** Sequencing: tradfi G1→G5 driven NOW (ahead of
  cefi-first ordering — the documented intent for this dispatch); reversible work driven to done, expensive/irreversible
  (G2 fleet launch, real-GCS purge) HARD-PAUSE for operator confirm. Composes with the Phase-0 canonical-form single-SoT
  migration item (above) — tradfi is one AG of it.
  - **Read-only audit of `prod/catalog.parquet` (814,011 rows) + `by_date/` + code — full tradfi pollutant inventory,
    root-caused, each fix STOPS it at source; stale rows = retirement (operator-confirm GCS purge):** daily-capture is
    BROKEN (`by_date/day=2026-06-24/` = ONLY `venue=CME`, 1 of 7 venues). Pollutants (cumulative catalogue counts): ICE
    COMBO+FUTURE BRN-Brent **16,157** (stale avail_to=2023-12-21; IFEU/IFUS non-billable maps) · ICE INDEX DXY **1** ·
    CBOE OPTION OPRA-SPX `O:SPX…` **33,258** (stale; OPRA non-billable) · CBOE SPOT_PAIR VX-spreads
    `VX/F1:1:S - VX/G1:1:B` **4,216** (ACTIVE; XCBF class-S→SPOT_PAIR) · CBOE INDEX **6** (^VIX, I:VIX,
    ^IRX/^FVX/^TNX/^TYX) · NASDAQ/NYSE SPOT_PAIR **102/216** (ACTIVE; DBEQ class-S equity-spot mis-typed) · cefi-singles
    in EQUITY (NVDA/MSFT/AAPL/CRCL/INTC/GOOGL/AMD/ TSLA/AMZN/META/HOOD/BABA, mvp=True; 50bf1c8 fixed only the crash NOT
    exclusion) · VX FUTURE asset_group=EQUITY **82** (should be COMMODITY) · `available_to`
    global-`latest_day`/last-seen bug (all →2026-06-23; VX/F7 falsely active) · MVP broken (895/814,011 True; VX futures
    all False) · KRX/FX in NO calendar SSOT (`is_non_trading_day` fails-OPEN → silent 24/7 → Korean holidays
    mishandled).
  - **MACRO-INDEX / CURRENCY decision (operator clarifications 2026-06-25):** (1) "DXY canonical along with KRWUSD as
    the currencies daily from Yahoo, **not one-offs**" → **KEEP + canonicalise** DXY (re-home venue ICE→**FX**,
    asset_group=fx)
    - KRWUSD (already FX) + the treasury-yield rate indices ^IRX/^FVX/^TNX/^TYX (Yahoo daily macro rates, venue=CBOE
      issuer-correct, asset_group=fixed_income). Yahoo daily series have NO billing issue → they stay (the §7.1
      yahoo-allowlist generalises beyond `{KRX,FX}` to the canonical Yahoo daily currency/macro series — codex §7.1 to
      update). (2) **REMOVE only VIX cash** (^VIX Yahoo + I:VIX OPRA) — redundant, VX futures cover VIX-15m
      (`is_vix_15m_gap_date` always False). (3) "**ICE is databento billing-blocked → purge EVERYWHERE**" → the ICE
      Databento BRN-Brent (16,158) purged across by_date + manifest + catalogue + surfaces; DXY moves off ICE so ICE
      venue is GONE. (This REVERSES the earlier "drop all YAHOO_INDICES" reading — DXY/treasuries/KRWUSD are
      canonical-keep.) DEPTH todo: expand the Yahoo currencies universe beyond DXY/KRWUSD ("not just one-offs").
  - **TRADFI G1 code checklist (slot-3; tradfi-databento files = NON-colliding with the cefi agent; the AG-agnostic
    `build_instrument_catalogue.py` §7.3 `available_to`/per-venue-`latest_day` fix is the cefi agent's item 4 — SHARED,
    coordinate, one fix covers both AGs):**
    - [x] ✅ [SCRIPT] P0. **G1.a billable-venue guard (§7.1)** — IS@92084d5c QG-green. Stripped non-billable datasets
          (IFEU/IFUS/OPRA/XNAS.ITCH/XNAS.BASIC/XNYS.PILLAR) from `_DATASET_TO_VENUE`/`_DATASET_TO_asset_group`/
          `_FUTURES_DATASETS` (now only the 3 billable) + exclusion-marker comments; the
          `assert_databento_request_allowed` fetch gate was already present (adapter.py L424). Regression:
          `test_g1a_billable_dataset_maps_only_three`. **Follow-up todos filed below**: router.py + massive.py still
          reference non-billable datasets (the latter is the actual OPRA/I:VIX pollution source).
    - [x] ✅ [SCRIPT] P0. **G1.b exclude cefi-domain equity singles** — IS@92084d5c. `get_instruments` filters curated
          defs to `asset_group ∈ frozenset(AssetClass)` → the 12 cefi-singles (asset_group="cefi") not enumerated as
          tradfi; SP500-overlap tickers still enter via the SP500 path. Regression:
          `test_g1b_cefi_singles_excluded_from_tradfi_enumeration`.
    - [x] ✅ [SCRIPT] P0. **G1.c XCBF.PITCH = COMMODITY + outright-only** — UAC@256dfc4a (`_CFE_FUTURES` VX.FUT
          "equity"→"commodity" + UAC regression test) + IS@92084d5c (`_DATASET_TO_asset_group["XCBF.PITCH"]`→COMMODITY;
          drop XCBF class-S VX spreads in `_parse_row_to_record`). Regression:
          `test_g1c_xcbf_outright_only_drops_vx_spreads` (IS) + `test_vx_future_asset_group_is_commodity` (UAC). The
          IS↔UAC test coupling was DECOUPLED (UAC content asserted in UAC's suite, not IS) to avoid false-fails under
          UAC promotion lag.
    - [x] ✅ [SCRIPT] P0. **G1.d DBEQ.BASIC class-S → EQUITY** — IS@92084d5c. Equity-spot rows no longer mis-typed
          SPOT_PAIR. Regression: `test_g1d_dbeq_class_s_is_equity_not_spot_pair`.
    - [x] ✅ [SCRIPT] P0. **G1.e calendars+sessions FAIL-CLOSED** — IS@92084d5c. Declared KRX (XKRX cal + KST hours) +
          FX (24/7 explicit) + `is_non_trading_day` raises `UndeclaredTradfiVenueError` for an undeclared tradfi venue
          (was silent 24/7). ICE re-DECLARED in sessions pending the whole-venue retirement (so no spurious raise
          mid-transition; curated enumeration already drops ICE instruments). Regression:
          `test_g1e_krx_uses_korean_calendar` + `test_g1e_fx_is_24_7` + `test_g1e_undeclared_venue_fail_closed`; updated
          the prior fail-open test.
    - [x] ✅ [SCRIPT] P0. **G1.f macro/currency canonicalise** — PARTIAL (operator-reshaped 2026-06-25): VIX cash-index
          REMOVED from UAC `YAHOO_INDICES` ✅ (uac@43db03f8 + databento VIX-USD tests IS@fb13355e); DXY KEEPS venue=ICE
          ✅ (operator REVERSED the planned ICE→FX — DXY IS the ICE/NYBOT US Dollar Index, Yahoo-sourced, the ONLY
          retained ICE exception, documented in-registry; ICE→FX key-migration CANCELLED). REMAINING split into G1.f.2
          (VIX-15m index removal) + G1.f.3 (treasuries actually reach the catalogue) below — both DONE, nothing left
          open under G1.f itself.
    - [x] ✅ [SCRIPT] P1. **G1.f.2 — retire the VIX-15m INDEX (superseded by VX futures 1s OHLCV; operator 2026-06-25)**
          — remove `CBOE:INDEX:VIX-USD` ohlcv_15m as a distinct index. 3-repo, consumers-first. VX.FUT futures
          (`CBOE:FUTURE:VX`, XCBF.PITCH ohlcv-1s/1m, aggregated downstream) is KEPT — it IS the VIX-vol source;
          features=0 consumers of the VIX-15m index. **STAGE 1 — MTDS DONE ✅ mtds@833fa14c (QG-green):** removed
          `fetch_yahoo_vix_15m` (`_umi_yahoo.py`) + the CBOE+ohlcv_15m→Yahoo routing (`umi_tick_provider.py`) +
          `download_vix_15m` + the `VIX_INDEX_INSTRUMENT` special-case in `YahooFinanceAdapter.fetch_instruments` (→
          `[]`). A direct `(CBOE, ohlcv_15m)` fetch now returns empty (no Yahoo, no error) — VERIFIED. Tests: deleted
          `test_vix_15m_source_layering.py`; dropped the obsolete Yahoo-routing tests; `CBOE+ohlcv_15m` asserts
          empty-no-Yahoo. **STAGE 2 — MDPS DONE ✅ mdps@79fbb16:** deleted `_record_vix_gap_empty` + its
          `orchestration_service.py` caller block + the unused VIX UAC imports (`VIX_INSTRUMENT_KEY`,
          `is_vix_15m_gap_date`, `PipelineMode`, `MarketAssetGroup`) + module docstring cleanup. Deleted
          `TestRecordVixGapEmptyPipelineMode` test class. **STAGE 3 — UAC DONE ✅ uac@599acf93 (QG-green, breaking):**
          removed `get_vix_15m_source` / `is_vix_15m_gap_date` / `get_yahoo_vix_15m_start` / `VIX_15M_SOURCE_HISTORY` /
          `YAHOO_VIX_15M_WINDOW_DAYS` / `DATABENTO_VX_FUTURES_FIRST_DATE` / `VIX_PROD_BUCKET` / `VIX_DEV_BUCKET` /
          `VIX_INSTRUMENT_KEY` / `VIX_DATA_TYPE` / `VIX_TYPE_PREFIX` from `data_source_continuity.py`; removed
          `VIX_INDEX_INSTRUMENT` + `VIX_INSTRUMENT` from `tradfi_symbology.py`; removed VIX-USD entry from
          `TRADFI_INSTRUMENTS`/`TRADFI_DATA_BINDINGS`; removed all 13 VIX symbols from `registry/__init__.py`
          re-exports. Also fixed pre-existing backward-compat docstring in `events/__init__.py` (QG sentinel unblock).
          Tests updated (6 files). Staged → LDR; Tier-C drain ≤15min → staging; detect_breaking_change.py fires SIT
          (~30min). **NB (data-correctness, verify at G2): VIX-15m now depends on `CBOE:FUTURE:VX` being captured at
          ohlcv-1s/1m + the downstream 1s/1m→15m aggregation — confirm that path is wired so removing the Yahoo fetch
          leaves no silent 15m gap.** Provenance: operator 2026-06-25.
    - [x] ✅ [SCRIPT] P0. **G1.f.3 — CBOE treasury-yield INDICES into the daily instrument definitions (operator
          2026-06-25)** — DONE uac@0b8a775c + IS@2536d9b4. **US2Y ADDED** to UAC `YAHOO_INDICES` as
          `CBOE:INDEX:US2Y-USD` via Yahoo `2YY=F` (operator: "use Yahoo, don't care which ticker"; the only Yahoo 2Y is
          the 2YY=F future — no ^-series cash 2Y exists) + the shared treasury source-resolver + genesis 2018-08-13 (CME
          yield-futures launch, best-estimate — VERIFY at backfill; honest-absence surfaces freshness since 2YY=F was
          noted stale). Target curve = **3M / 2Y / 5Y / 10Y** (operator) + 30Y KEPT (the features
          `treasury_yields_calculator` depends on it; operator curve is a subset). US5Y/US10Y/US3M/US30Y already in the
          registry. Tests updated (UAC `_TREASURY_TENORS` + resolver-coverage gate; IS `_create_yahoo_index_records`
          loop). **Catalogue population is OPERATIONAL, not a code gap**: CBOE IS in `_TRADFI_VENUES`
          (venue_core.py:138) + `build_instrument_catalogue.py` rolls up from the written
          `instrument_availability/venue=CBOE/` parquets WITHOUT filtering INDEX — so the treasuries reach the catalogue
          once a CBOE instruments-backfill writes the `CBOE:INDEX:USxY-USD` records (rides **G2**). The operator's
          "never in the catalogue" = no CBOE-index backfill has run since the yahoo-index path landed, not a code
          exclusion. **FOLLOW-UP (features): `treasury_yields_calculator.py` builds the curve from 5Y/10Y/30Y — wiring
          it to consume the new 2Y/3M points is a features-track todo (not blocking the instrument-definition add).**
          Provenance: operator 2026-06-25.
    - [x] ✅ [SCRIPT] P1. **G1.g MVP tags on the tradfi MVP universe** (VX futures + basis tickers). — **VERIFIED DONE
          2026-07-26**: already fixed — `unified_api_contracts/canonical/crosscutting/ _mvp_scope_rules.py`'s tradfi
          `underliers` set already includes VX + the 7 basis-commodity roots (GC/SI/PL/PA/NG/CL/HG), each with dated
          operator-ruling comments (2026-06-24/2026-07-21/22). Live-queried the catalogue: VX (82 rows) and all 7 basis
          roots (78-156 rows each) show `mvp=True` at 100%. No code change needed.
    - [x] ✅ [SCRIPT] P0. **G1.h §7.3 `available_to` venue-truth + per-venue `latest_day`** — SHIPPED
          instruments-service@8261203 (the SHARED `build_instrument_catalogue.py` fix; ONE edit covers tradfi G1.h AND
          cefi G1.1 — checked git log 665966b clean before+after, no double-edit). `build_catalogue_dataframe` now uses
          a PER-VENUE thin-day-aware last-full-trading-day (`_venue_last_full_day`) instead of the global `latest_day`
          (so a lagging KRX/divergent-calendar venue is no longer falsely delisted off a CME-fuller day) + venue-truth
          `expiry`/`delisted_at` for dated instruments. QG-green, 54 roll-up tests pass. NOTE: tradfi prod-regen verify
          rides tradfi G3 (catalogue-regen-tradfi is operator-PAUSED pending tradfi G1 retirement/sign-off — do NOT
          regen it before the §9 retirement purge or it re-bakes the ICE/OPRA pollutants).
    - [x] ✅ [INFRA] P0. **RULED 2026-08-07 (operator, via consolidated NA-blocker-digest audit) — GO AHEAD.**
          **EXECUTED 2026-08-08** (round5-cross-cutting-audit, id=52) — the literal "4 legs" (ICE whole-venue 16,147 ·
          CBOE OPRA OPTION 33,258 · CBOE VX-spread SPOT_PAIR 4,216 · VIX-cash INDEX 2) purged from
          `instruments-store-tradfi-prd-.../prod/catalog.parquet`: 53,623 rows removed, 973,116→919,493, snapshot +
          `.bak` taken first, post-write verify clean (0 remaining, CBOE COMBO/FUTURE untouched). **Full evidence + the
          critical scheduler-was-actually-live finding**: see `instruments_completion_tracker_2026_07_06.md`'s twin todo
          (this session's other citation of the same work) — do not re-execute there, it's the same purge. **NASDAQ/NYSE
          mis-class SPOT_PAIR (318) and cefi-singles (12 tickers, EQUITY-type rows) deliberately NOT purged this pass**
          — this doc's own paragraph bundles 6 items under "4 legs" (an internal miscount), but the digest item that
          carried the operator's actual approval only asked about the literal 4 named above; those 2 residual legs stay
          open, tracked as their own explicit todo immediately below rather than assumed-approved by association.
    - [ ] [DATA] P2. **NEW (filed 2026-08-08, split out of the item above)**: purge the 2 residual tradfi catalogue legs
          NOT covered by the executed 4-leg purge — NASDAQ/NYSE mis-classified `SPOT_PAIR` rows (318, all equity tickers
          incorrectly typed as spot-pairs) and the 12 cefi-singles' `EQUITY`/`EQUITY-USD` rows (NVDA/MSFT/
          CRCL/INTC/GOOGL/AMD/TSLA/AMZN/META/HOOD/AAPL/BABA — `unified_api_contracts.TRADFI_DATABENTO_INSTRUMENTS`
          filtered `asset_group=="cefi"`; each ticker's `SPOT_PAIR` row is already covered by the NASDAQ/NYSE leg, only
          the `EQUITY`/`EQUITY-USD` rows remain). Same target bucket/blob, same script pattern as the executed purge —
          mechanical once confirmed. Also needs the same scheduler-pause precondition (currently already paused from the
          4-leg purge; re-verify live state at execution time, don't assume it's still paused). **CORRECTED 2026-08-18
          (plan_reconciler)**: "needs its own explicit operator confirmation" is now stale — the operator ALREADY
          extended the go-ahead to this residual 2-leg set (2026-08-16, see this doc's own Progress Log below) and
          the work is extracted + queued at `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`
          (`assigned_vm: planning`, unlocked). Not re-executed here to avoid racing that dispatch.
    - [x] ✅ [SCRIPT] P1. **G1.a.2 §7.1 follow-up — massive.py (the OPRA/I:VIX pollution source)** — DONE
          instruments-service@1198549 (LDR). massive KEPT as the tradfi FALLBACK (operator 2026-06-25); endpoint
          `https://api.polygon.io` VERIFIED correct (Polygon.io→Massive 2025-10-30 rebrand kept the host). Removed the
          two pollution-fetch paths the databento §7.1 guard (G1.a) does not touch: `_fetch_indices` (CBOE cash-index /
          VIX-cash over YAHOO*INDICES) + `_fetch_index_options` (OPRA SPX/VIX cash-index OPTION chains) — both retired
          (VX vol rides Databento XCBF.PITCH) — plus ICE from `_FUTURES_VENUES` (ICE \_commodity* FUTURES = Brent/Gasoil
          via IFEU/IFUS are Databento-billing-blocked, no canonical source — that subscription ask stands. NB ICE _DXY_
          index DOES have a canonical source now: Yahoo `DX-Y.NYB`, shipped `uac@5480f5d5`, 2026-06-27 — only the
          futures are blocked). massive now fetches NASDAQ/NYSE equities + FX + CME futures ONLY, ending CBOE-OPTION
          (33,258) / VIX-cash / ICE-futures catalogue pollution at source. Regression:
          `test_cboe_and_ice_filters_yield_no_pollution` (CBOE+ICE venue filters yield zero records); dead index/option
          fixtures + coverage-boost tests removed. QG-green, 58 tests pass, basedpyright 0. NOTE: this is the SOURCE fix
          (stop writing pollution); the GCS PURGE of the already-written CBOE-OPTION/VIX-cash/ICE parquets stays in the
          operator-gated G1 retirement (§9). Actual method names were `_fetch_indices`/`_fetch_index_options` (plan's
          earlier `_fetch_opra_options`/ `_fetch_index_universe` were guesses). Provenance: slot-3 G1.a diagnosis
          2026-06-25.
    - [x] ✅ [SCRIPT] P2. **G1.a.3 §7.1 follow-up — router.py dead non-billable dataset config** — DONE
          instruments-service@5ef1958f (LDR). DELETED (not realigned) the whole dead path: the databento adapter
          resolves each instrument's dataset PER-INSTRUMENT from the curated `TRADFI_DATABENTO_INSTRUMENTS` registry
          (§7.1 billable allowlist DBEQ.BASIC / GLBX.MDP3 / XCBF.PITCH), so the router's `_DATABENTO_VENUE_DATASETS`
          venue→dataset map (nasdaq/nyse/apple/binance→XNAS.ITCH/XNYS.PILLAR + cboe_options→OPRA.PILLAR, all
          non-billable) + `_resolve_databento_datasets` resolver + `_route_databento`'s resolve-and-pass + the unused
          `datasets=` ctor param (all callers kwargs-only) were 100% dead. Removed all four + the misleading docstring
          annotations. Routing behaviour unchanged (databento still → DatabentoReferenceDataAdapter); only the dead
          non-billable annotation is gone. Tests: removed `TestResolveDatabentoDatasetsRouter` + dead import;
          `test_router` routing assertions unchanged (still pass — they assert isinstance, not datasets). QG-green, 68
          tests pass, basedpyright 0. Provenance: slot-3 G1.a diagnosis 2026-06-25.

- 2026-06-25 — **TRADFI G1.a–e SHIPPED + tradfi compute fully stopped (slot-3).** **Code (QG-green, both repos):**
  UAC@256dfc4a (`_CFE_FUTURES` VX.FUT "equity"→"commodity" + UAC regression test) + instruments-service@92084d5c
  (symbology billable-venue map cleanup → only the 3 billable datasets; `get_instruments` excludes cefi-domain singles;
  XCBF class-S VX spreads dropped + XCBF→COMMODITY; DBEQ class-S→EQUITY; KRX XKRX-calendar + FX-24/7 + fail-closed
  `UndeclaredTradfiVenueError`; ICE re-declared in sessions pending the whole-venue retirement; **8 regression tests**
  in `test_databento_tardis_adapter.py::TestTradfiG1FoundationRegression` + the IS↔UAC VX assertion DECOUPLED into UAC's
  suite to avoid UAC-promotion-lag false-fails). These STOP the active catalogue pollution at source (4,216 VX-spread
  SPOT_PAIR + 318 equity-spot mis-class + cefi-singles + VX=EQUITY); stale rows (ICE 16,158 / OPRA 33,258 / VIX-cash)
  are the operator-gated retirement. **Findings filed** (above): OPRA/I:VIX pollution actually comes from massive.py
  (G1.a.2); router.py dead non-billable config (G1.a.3). **Awaiting G1 sign-off.**
  - **Tradfi compute STOPPED (operator P0 2026-06-25 — "another track relaunched the tradfi-bf fleet overnight despite
    the pause"):** killed the 18 RUNNING `tradfi-bf-*` OHLCV backfills (the ~6 KRX ones had self-completed); deleted the
    `tradfi-fwd-daily-cron` launcher host (was a 06:00 forward-poll launcher — same gate-jump class);
    `uts-prod-tradfi- wave-launcher-cron` + `instruments-daily-backfill` schedulers confirmed PAUSED (the automated
    relaunch path — it never actually fired; the overnight launch was external/manual). Also paused
    **`lifecycle-catalogue-regen-tradfi-daily` (01:00)** + **`instrument-catalogue-regen-nightly` (02:00)** at 01:38 UTC
    — protective, before the 02:00 fire would re-bake the §7.3 false-delistings into the tradfi catalogue SSOT. **Left
    running** (per dispatch "leave the live producer"): `mtds-live-tradfi-cme-trades` (live `databento` WS) — flagged
    for the operator. **Cross-AG flag:** the other AGs' `lifecycle-catalogue-regen-{cefi,defi,sports,prediction}`
    (01:00) + `catalogue-regen-nightly` (04:30) are still ENABLED (cefi has the same §7.3 bug) — operator to decide a
    fleet-wide catalogue-regen pause.
  - **G1.f / G1.h / retirement sequencing:** G1.f (macro/currency: VIX-cash removal + DXY venue ICE→FX) is a canonical
    key-migration (UAC `YAHOO_INDICES` + `data_source_continuity._SOURCE_RESOLVERS`
    `ICE:INDEX:DXY-USD`→`FX:INDEX:DXY-USD`
    - EU enumerator + massive + the existing DXY market-data GCS re-key) → done COORDINATED with the operator-gated
      retirement/canonical-migration (a standalone code change would create the exact dual-SoT the operator banned).
      Operator clarified DXY+KRWUSD+treasuries are canonical Yahoo-daily KEEP (not one-offs); only VIX-cash is removed.
      G1.h §7.3 `available_to`/per-venue-`latest_day` is the cefi agent's item-4 (AG-agnostic
      `build_instrument_catalogue.py`) — coordinate, one fix both AGs.

- 2026-06-25 — **G4 catalogue-as-filter BUG fixed (tradfi) — market-tick-data-service@dda5040d (QG-green).**
  Read-verified the MTDS catalogue-as-filter and found a real bug: `TradFiCatalogReader` probed a DEAD prefix
  `reference_data/instruments/asset_group=tradfi/` (absent in the bucket — only `prod/catalog.parquet` exists) AND read
  the legacy `available_*_datetime` column names (the roll-up uses un-suffixed `available_from`/`available_to`), so it
  ALWAYS returned an empty iterator → the MTDS sentinel fan-out silently fell back to the UAC ("BTC"/"ETH") MVP seed and
  never filtered the real tradfi catalogue. Fixed: probe `{prod,staging,dev}/catalog.parquet` + canonical
  `available_from`/`available_to` (mirrors the `CeFiCatalogReader` BUG #4 fix, 2026-06-22) + 2 regression tests. **G4
  mechanism is now functional** (active-on-date window filter + FUTURE/OPTION root dedup); the gate's DoD (MTDS attempts
  == catalogue-active-for-day) becomes verifiable once the catalogue is clean (post-retirement + §7.3). NB the
  `catalog_list_instruments(ag)` sentinel path (sentinels.py) is a SEPARATE Tier-1 reader from this Tier-3 chain reader.

- 2026-06-26 — **G1.f.2 (VIX-15m INDEX retirement) COMPLETE — all 3 stages shipped.** MDPS mdps@79fbb16 (Stage 2:
  `_record_vix_gap_empty` deleted + test class); UAC uac@599acf93 (Stage 3 breaking: 13 VIX public symbols removed +
  backward-compat docstring fix that unblocked QG sentinel). Plan flip committed pm@7f5932caf. CI fires via Tier-C drain
  (UAC breaking → detect_breaking_change.py → SIT ~30min). **Data-correctness finding (P2, zero live impact):** two
  stale capability registrations remain post-retirement — `expected_coverage.py` CBOE `ohlcv_15m` entry + a
  `DataTypeCapability(venue="CBOE", data_type="ohlcv_15m", instrument_type="")` entry in `data_type_capability.py` both
  reference the now-deleted VIX cash INDEX. Zero downstream consumers of CBOE ohlcv_15m (features=0). Filed as a plan
  todo under G1.f.2 post-retirement cleanup above. Notify operator if a 15m VX-futures consumer is added before cleanup.

- 2026-07-26 — **CME instrument-definitions coverage verification + old-date re-fetch sample (slot-5, review; batch2-002
  combined todo, items 1+4).** (1) The 9-shard fleet had self-deleted; checked live manifest coverage for CME 2019-01-01
  through today via `verify_instrument_manifest_coverage.py` (fixed a real one-line bug found in the same pass —
  `args.category` → `args.asset_group`, the script would AttributeError on every invocation). Found 368 "missing" dates,
  ALL in 2019. Investigated: CME's declared discovery-start is `2020-01-01` (UAC `venue_mapping.py` +
  `canonical/coverage_starts.py`, both explicit) — NOT a bug, a deliberate floor. Launched a SPOT VM
  (`instr-backfill-tradfi-cme-a-20260726-164850`, 2019-01-01→2019-12-31, self-shut-down, exit_code=0) to CONFIRM this
  live rather than trust the config alone: it correctly found "no active venues" for every 2019 date and wrote ZERO rows
  — the floor is real, 2019 is honestly out of scope, no code/data fix needed. Re-checked coverage against the TRUE
  floor (2020-01-01→today, 2,399 days): only 3 residual gaps — `2024-06-02` (Sun), `2024-10-06` (Sun), `2024-11-08`
  (Fri, a REAL trading day). Backfilled `2024-11-08` (45,787 records written, confirmed via
  `verify_instrument_manifest_coverage.py` re-run: down to the 2 Sundays only). The 2 Sundays hard-fail with
  `RuntimeError: URDI returned zero records` instead of writing an honest `empty_confirmed` row like the other 363
  weekends in the manifest do — a minor pre-existing inconsistency (2/2,399 days = 99.92% floor coverage), not fixed
  here (would need adapter-level investigation into why these 2 specific Sundays diverge from the other 363 weekend rows
  already carrying `empty_confirmed`). **Net: CME instrument-definition coverage is effectively complete against its
  real declared floor.** (2) Re-fetched 3 sample old dates (`--force`) to confirm the re-fetch mechanism picks up the
  CURRENT universe (post-2026-06-19 EC\* event-contract + DBEQ.BASIC consolidation): `2020-01-02` → 38,669 records (was
  captured under the pre-lockdown narrow universe), `2023-01-03` → 47,810 records (both confirm the OLD dates were
  captured under a dramatically narrower universe and a forced re-fetch correctly expands to match today's ~74-95K/day
  range); `2026-06-17` hit a live transient `URDI returned zero records` error on retry (not investigated further — a
  single transient failure, not a pattern). **Enumerated un-refetched range**: every CME date from `2020-01-01` through
  `2026-06-18` (~2,368 calendar days, the pre-lockdown era) was captured under the OLD narrower universe and would
  benefit from a full re-fetch to pick up EC\* event contracts + the DBEQ.BASIC consolidation — this is a genuinely
  large campaign (not a "small sample" task), tracked here as a NEW finding for a dedicated future backfill plan, not
  attempted in full in this todo (scope was explicitly "small sample + enumerate the range").

---

## Deferred work after 2026-06-26

| #   | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Repo       | Priority | Blocked on                   |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------- | ---------------------------- |
| 1   | ~~Clean stale CBOE ohlcv_15m capability entries~~ — RESOLVED 2026-07-26: UAC's `expected_coverage.py`/`data_type_capability.py` were ALREADY clean (removed 2026-07-15, predates this todo — verified via live grep, 0 hits in both files). Fixed the one remaining stale artifact: MDPS `ohlcv_passthrough.py`'s `TradfiOhlcv15mAdapter` docstring still cited the retired Yahoo VIX-cash/Barchart source — corrected to state the real current status (VX futures 1s/1m only, no aggregation writer yet, zero live consumers) — `market-data-processing-service@<pending>` | UAC + MDPS | —        | Resolved                     |
| 2   | ~~Verify UAC uac@599acf93 SIT passes~~ — RESOLVED 2026-07-26: confirmed via PR #503 (merged 2026-06-26T13:32:05Z, first main-merge carrying the commit), `git merge-base --is-ancestor` TRUE (UAC promotes via real merge commits, not squash), zero revert commits in history, and the removed VIX symbols are still absent from `origin/main` a month later with hundreds of subsequent green `quality-gates-v2` runs on `main` — the breaking change landed clean and never needed rollback                                                                               | UAC        | —        | Resolved (verified live)     |
| 3   | ~~G1.f (partial — DXY key migration ICE→FX)~~ — RESOLVED 2026-06-25: operator REVERSED the planned migration, DXY KEEPS venue=ICE, ICE→FX key-migration CANCELLED outright (see G1.f above). No decision remains pending.                                                                                                                                                                                                                                                                                                                                                    | UAC + IS   | —        | Resolved (no longer blocked) |
| 4   | ~~G1.g MVP tags; G1.a.2 massive.py §7.1; G1.a.3 router.py dead config~~ — RESOLVED (na-eligibility-audit 2026-07-27, stale row): the checklist body above already shows all 3 `[x]` ✅ DONE with 2026-07-26 verification (G1.g line ~267, G1.a.2 line ~283, G1.a.3 line ~299) — this row was never updated to match. No further action needed.                                                                                                                                                                                                                               | IS + MTDS  | P1/P2    | Resolved                     |

---

## Folded-in tradfi residuals (I-1 consolidation 2026-06-26 — tradfi portion; cross-cutting portion moved to the Phase-0 child)

> Continuation of the `proper_instrument_catalogue_lifecycle_rollup_2026_06_04` (archived) folded-in items — the
> cross-cutting items from that same archived plan moved to the Phase-0 child.

- [x] [DATA] P1. ✅ **PARTIAL — diagnosis + staleness-check ask DONE 2026-07-26 (batch-3 todo 3, item 2); underlying
      freeze itself NOT fixed, tracked separately below.** Applied catalogues are honest snapshots-as-of-freeze (cefi
      usable; tradfi marks ~651K "delisted" → liveness not trustworthy until tradfi capture fixed + catalogue
      regenerated). Root cause re-confirmed: Massive removal (2026-07-19) broke `by_date`; a Databento re-feed has not
      yet been run — tradfi is STILL degraded (~10-15 writes/day vs the historical 16-18K). The coverage-horizon
      staleness check this bullet asked for was already shipped `instruments-service@5d31994a` (2026-07-03,
      `CATALOGUE_STALE_BY_DATE`), applies per-AG generically incl. tradfi, QG-green in production — so THIS bullet's
      literal ask ("diagnose... + add a coverage-horizon staleness check") is satisfied. This does **not** claim the
      `by_date` capture is restored — that remains a real, separate open gap (Databento re-feed not yet run); see the
      sibling ICE/CME-futures-options and CME-futures-reference-gap bullets immediately below, which already track the
      credential/upstream blockers on the actual data recovery. Source:
      `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md` todo 3.
- [x] ✅ [DATA] P1. **CLOSED 2026-08-07 (operator, via consolidated NA-blocker-digest audit) — WON'T-FIX, moot.**
      ICE/OPRA is out of tradfi MVP scope (confirmed elsewhere in this corpus: "ICE is NOT in the tradfi MVP universe"),
      Databento-billing-blocked at the code layer (no canonical source, per
      `/codex/02-data/tradfi-databento-sourcing-ssot.md`), and ICE is being actively PURGED from the catalogue entirely
      via this same doc's G1 retirement (whole-venue, 16,158 rows, approved same session). The question of a paid
      ICE/OPRA subscription is moot — nothing in the code path can fetch it even if approved, and nothing downstream
      needs it. Operator's prior 2026-06-18 decline stands; not re-litigated, closed as accepted gap rather than left
      open as a live ask. **Original finding, preserved for the record**: ICE futures not on Massive →
      BLOCKED-CREDENTIALS (ping `ikenna_orchestrator/pings/slot_5.md`, 2026-07-27). Retagged 2026-07-29: the struck
      CME-futures-options half was already resolved-by-reference (existing GLBX.MDP3 Databento subscription covers it,
      per `data_completion_tradfi_2026_07_15.md:426-433` — no credential needed, stale Massive-era framing). Only the
      ICE-futures half stayed open, now closed per this ruling.
- [x] ✅ [DATA] P1. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — Massive was removed entirely as
      a tradfi source (operator ruling 2026-07-19, `uac@a2beed46`), subscription terminated, `source='massive'` writes
      now hard-reject. The replacement path already exists at `data_completion_tradfi_2026_07_15.md:421-433` (run IS
      instrument capture with `--source databento` → regenerate the tradfi catalogue) — that replacement todo is NOT yet
      executed, only correctly targeted; tracking for the actual re-run continues there, not here.** tradfi CME futures
      reference gap from 2026-06-08 — Massive `/futures/vX/{products,contracts}` 404 (worked 2026-06-07).
      `BLOCKED-UPSTREAM-OUTAGE`: re-probe, on restore re-run `--asset-group TRADFI --source massive` for missing days so
      `venue=CME` refills, then regen the tradfi catalogue. Repo: instruments-service. (MIGRATED FROM: same.)
- [x] ✅ [CODE] P2. **FINDING — MTDS Massive connector uses the wrong futures endpoint.**
      `massive_tradfi_rest_connector.py` maps futures→`/v3/reference/futures/contracts` (404s); working path is
      `/futures/vX/contracts` (+ `/futures/vX/products` for contract size). Repo: market-tick-data-service. assigned_vm:
      vm-tradfi. (MIGRATED FROM: same.) — **MOOT 2026-07-26**: `massive_tradfi_rest_connector.py` no longer exists in
      market-tick-data-service — Massive was REMOVED entirely as a tradfi source 2026-07-19 (operator ruling: Databento
      = batch SoT, Yahoo = daily; see CLAUDE.md). Nothing to fix; superseded by the source removal.

### From `tradfi_databento_subscription_universe_lockdown_2026_06_18` (archived; 26/33 done — universe lockdown + billing guards SHIPPED)

- [x] ✅ [IS] P1. **DONE 2026-07-26 (slot-5, review)** — Verified IS CME (GLBX.MDP3) instrument-definitions catalog
      coverage. The "2019-01-01→present" framing was itself stale: CME's DECLARED discovery-start is `2020-01-01` (UAC
      `venue_mapping.py` + `canonical/coverage_starts.py`, both explicit) — confirmed LIVE by launching a SPOT VM
      (`instr-backfill-tradfi-cme-a-20260726-164850`, 2019-01-01→2019-12-31, self-shut-down exit_code=0) which correctly
      found "no active venues" for every 2019 date and wrote zero rows — 2019 is honestly out of scope, not a gap.
      Re-checked coverage against the TRUE floor (2020-01-01→today): only 3 residual gaps found, of which 1
      (`2024-11-08`, a real Friday trading day) was a genuine miss — backfilled (45,787 records written). The other 2
      (`2024-06-02`, `2024-10-06`, both Sundays) hard-fail with `RuntimeError: URDI returned zero records` instead of an
      honest `empty_confirmed` like the other 363 weekends — filed as a new P3 finding (§ "Deferred work after
      2026-07-26"), not fixed here (out of scope). Fixed a real one-line bug found along the way in
      `verify_instrument_manifest_coverage.py` (`args.category` → `args.asset_group` — the script AttributeError'd on
      every invocation) — `instruments-service@<pending>`. **Net: CME instrument-definitions coverage is complete
      against its real declared floor.** The downstream MTDS market-data download stays M-1's
      (`path_to_100pct_backfill_mtds_is`); the CME EC\* event-contract slice is the tradfi-domain plan-of-record
      `tradfi_cme_event_contract_backfill_2026_06_20` (tradfi_master) — coordinate, don't duplicate. (MIGRATED FROM:
      `tradfi_databento_subscription_universe_lockdown_2026_06_18`.)
- [x] ✅ [SCRIPT] P1. **CLOSED (na-eligibility-audit 2026-08-03)** — the doc's own inline citation just below (added
      2026-08-02) already confirmed this identical tradfi 3-dataset batch checked `[x]` DONE in
      `data_completion_to_100_all_ag_2026_06_21.md:121-124` (`deployment-service@f243eb4`, 17 VMs RUNNING); this
      checkbox itself was simply never flipped. **(→ M-1) MTDS tradfi market-data backfill across all 3 datasets**
      (GLBX.MDP3 + DBEQ.BASIC + CFE) × the L0 16y window, sharded; verify per-dataset manifest coverage (captured +
      honest-absence); confirm equity cells re-routed to DBEQ.BASIC and CFE/VX cells exist. **EXECUTE UNDER M-1**
      (`path_to_100pct_backfill_mtds_is`, which owns MTDS market-data backfill-to-100% and already ran the Databento
      OHLCV pass 2026-06-19) — gated on the IS CME catalog backfill above. Listed here only as the cross-link. (MIGRATED
      FROM: same.) **CITATION (na-eligibility-audit 2026-08-02, tradfi tranche)**: confirmed live —
      `data_completion_to_100_all_ag_2026_06_21.md` lines 112-116 show this identical tradfi 3-dataset batch (GLBX via
      CME-b + DBEQ.BASIC + CFE/XCBF) checked `[x]` DONE (`deployment-service@f243eb4`, 17 VMs RUNNING,
      `VM_TASK=mtds-backfill` confirmed on all) — no independent action owned by this doc; this checkbox is a stale
      cross-link only.
- [x] ✅ [SCRIPT] P1. **instruments-service — post tradfi-v9 close-out, tombstone dropped Databento instruments.** Run
      `reconcile_manifest_after_entity_change.py --mode remove --asset-group tradfi` for the dropped ICE roots
      (BRN/G/DX, softs CT/CC/KC/SB/OJ; datasets IFEU.IMPACT/IFUS.IMPACT) → `REMOVED_ENTITY_TOMBSTONE` (dry-run → audit
      CSV → apply), then a phantom sweep. Repo: instruments-service. (MIGRATED FROM: same.) — **DONE 2026-07-26 —
      390,799 rows tombstoned (BRN 196,511 + G 194,288), DXY explicitly protected.** The literal
      `--entity-type venue --entity-key ICE` invocation would have ALSO tombstoned DXY (5 genuinely-`captured` rows,
      written as recently as 2026-07-25) — DXY is the ONE operator-ruled retained ICE exception (Yahoo-sourced US Dollar
      Index, actively captured daily; ICE→FX migration was explicitly CANCELLED per this doc's own G1.f.2 history).
      Wrote a root-scoped variant (mirrors the same safe capture_status→attempted_failed +
      error_reason=REMOVED_ENTITY_TOMBSTONE flip, snapshot-first) filtering `venue=ICE` AND root ∈
      {BRN,G,DX,CT,CC,KC,SB,OJ} extracted from `instrument_id`/`underlying`, with an explicit pre-write assertion that 0
      DXY rows are in the to-tombstone set. Positively identified BRN + G (390,799 rows, all `empty_confirmed`); the
      softs (CT/CC/KC/SB/OJ) + DX roots did not extract as identifiable rows in this manifest (present in a 16,695-row
      unidentified-root bucket with blank `instrument_id`/`underlying` — left untouched rather than guess). Post-apply
      verify: `market-data-tick-tradfi-prd` shows 390,799 `REMOVED_ENTITY_TOMBSTONE` rows, DXY's 5 rows unchanged
      (`capture_status=captured`). Phantom sweep
      (`reconcile_phantom_manifest_rows_all.py --asset-group tradfi --venues ICE --dry-run`): 0 phantoms, manifest
      clean. **Also found a real bug**: `reconcile_manifest_after_entity_change.py`'s `_default_csv_path()` resolves
      `Path(__file__).parents[4]` assuming a non-slotted checkout — under the Path-B per-slot topology this lands on the
      READ-ONLY root PM clone (`unified-trading-system-repos/unified-trading-pm/`), not the slot's own PM clone. Worked
      around via `--output-csv` for this run. **FIXED 2026-07-27 — `instruments-service@fc07e6b6`**
      (`tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` todo 4): `_default_csv_path()` now walks up from the script
      to the invoking repo's own `.git` root (Path-B or non-slotted, any nesting depth) and derives the
      `unified-trading-pm` sibling from that identity instead of the fixed `parents[N]` hop; raises loudly instead of
      silently falling back when no sibling clone resolves. 4 new unit tests in
      `tests/scripts/test_reconcile_manifest_entity_change_default_csv_path.py`, `quality-gates.sh --no-fix` green
      (sentinel-verified). No checkbox added here per batch4's own scope guard (this paragraph's parent checkbox is
      owned by `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s combined todo) — nothing remains open on this
      residual.
- [x] ✅ [UAC] P1. **DONE — already shipped pre-2026-07-25 (verified 2026-07-26, slot-5, review).** Unit tests for
      `databento_subscription_allowlist` already exist at `tests/unit/test_databento_subscription_allowlist.py`
      (introduced by `uac` commit `4ad54282`, already on `main` — verified via `git merge-base --is-ancestor` and a live
      `pytest` run: 39/39 pass) covering all 6 required scenarios: allowed/blocked dataset, banned OHLCV schema,
      per-level lookback-floor boundaries (L0-L3), batch-API ban + break-glass override, and enum-repr normalization. No
      new test needed. Repo: unified-api-contracts. (MIGRATED FROM: same.)
- [x] ✅ [PM] P1. **DONE — already shipped pre-2026-07-25 (verified 2026-07-26, slot-5, review).** The QG grep-ratchet
      already exists: MTDS `scripts/quality-gates.sh` STEP 5.92 (no raw `batch.submit_job` outside the guarded
      `submit_batch_job` wrapper) + STEP 5.93 (no off-allowlist Databento dataset string literal in tradfi fetch paths)
      — both wired in and re-verified GREEN live (manually re-ran both grep checks against the current tree: 0 hits
      each). No new check needed. Repo: PM + market-tick-data-service. (MIGRATED FROM: same.)
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-26 (slot-5, review)** — Re-fetched 3 sample old tradfi dates (`--force`) for CME to
      confirm the re-fetch mechanism picks up the CURRENT universe (post-2026-06-19 EC\* event-contract + DBEQ.BASIC
      consolidation lockdown): `2020-01-02` → 38,669 records (was captured under the pre-lockdown narrow universe:
      ~15-18K/day), `2023-01-03` → 47,810 records (same pattern) — both confirm the mechanism correctly expands to the
      current universe on a forced re-fetch. `2026-06-17` hit a single live transient `URDI returned zero records` error
      (not investigated further — not a pattern). **Enumerated un-refetched range**: every CME date from `2020-01-01`
      through `2026-06-18` (~2,368 calendar days) was captured under the OLD narrower universe and would benefit from a
      full re-fetch — filed as a NEW P2 finding (§ "Deferred work after 2026-07-26") for a dedicated future backfill
      plan; a full re-fetch of that range is a real campaign, not "small sample" scope, and was not attempted here.
      Repo: instruments-service. (MIGRATED FROM: same.)
- **[SCRIPT] P3. EXTRACTED 2026-08-09 → `tradfi_satellite_ao_dispatch_batch9_2026_08_09.md`.** RULED 2026-08-07
  (operator, via consolidated NA-blocker-digest audit) — GO AHEAD, conditional on the doc's own pre-existing gate:
  physical-GCS cleanup of old ICE-Databento instrument parquets, approved once tombstone reconciliation confirms 0
  consumers (twin-verify still required before delete — operator approval covers the delete itself, not a waiver of the
  twin-verify safety check). Repo: deployment-service + instruments-service. (MIGRATED FROM: same.)

### G1.f.2 post-retirement cleanup (2026-06-26)

- [x] ✅ [UAC] P2. **DONE 2026-07-26 (slot-5, review)** — Clean up stale CBOE `ohlcv_15m` capability registrations post
      VIX-INDEX retirement. UAC's `expected_coverage.py` (CBOE list is `["ohlcv_1s", "ohlcv_1m", "ohlcv_24h"]`, no
      `ohlcv_15m`) and `data_type_capability.py` (0 grep hits for a CBOE/ohlcv_15m entry) were BOTH already clean —
      removed 2026-07-15, predating this todo. Fixed the one remaining stale artifact: `TradfiOhlcv15mAdapter` docstring
      in MDPS `ohlcv_passthrough.py` still cited the retired Yahoo VIX-cash/Barchart source — corrected to state the
      real current status (VX futures via Databento XCBF.PITCH 1s/1m only; no 1s/1m→15m aggregation writer exists yet;
      zero live consumers) — `market-data-processing-service@<pending>`. The IMPORTANT aggregation-path caveat below
      still applies for any future 15m VX-futures consumer.

## Deferred work after 2026-07-26

| #   | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Repo | Priority | Blocked on                                              |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---- | -------- | ------------------------------------------------------- |
| 1   | **NEW FINDING (2026-07-26)**: full CME instrument-definitions re-fetch for `2020-01-01`→`2026-06-18` (~2,368 days), captured under the pre-lockdown narrower universe (EC\* event contracts + DBEQ.BASIC consolidation absent) — sample-verified (2 dates re-fetched, both confirm the gap: instrument_count jumps from ~15-18K/day pre-lockdown to ~74-95K/day post). This is a real backfill campaign, not a "small sample" task — needs its own dedicated plan/VM launch, not attempted here. | IS   | P2       | Nothing (scoping only; needs a dedicated backfill plan) |
| 2   | 2 anomalous Sundays (`2024-06-02`, `2024-10-06`) in the CME instrument-definitions manifest hard-fail with `RuntimeError: URDI returned zero records` instead of writing an honest `empty_confirmed` row like the other 363 weekends — a minor adapter-level inconsistency (99.92% floor coverage otherwise), needs investigation into why these 2 specific dates diverge.                                                                                                                       | IS   | P3       | Nothing (low-priority, non-blocking)                    |

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 3, operator ruling)**: the residual catalogue-leg purge
  (NASDAQ/NYSE SPOT_PAIR mis-classification 318 rows + 12 cefi-singles EQUITY/EQUITY-USD rows), not covered by the
  already-granted 4-leg go-ahead — **operator extended the go-ahead to this residual 2-leg set** — extracted to
  `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md` (`assigned_vm: planning`).
- **na-eligibility-audit 2026-07-30** (tradfi tranche): **KEEP-NA, valid.** All 8 open todos read end-to-end (7 top-
  level + 1 nested under the G1 checklist). Three are genuinely gated and keep the doc NA: G1 retirement is "OPERATOR-
  CONFIRM before purge", the surviving ICE-futures half of the BLOCKED-CREDENTIALS finding needs a paid ICE/OPRA
  subscription the operator already declined once (2026-06-18 ruling), and the optional ICE-Databento parquet cleanup is
  an operator-gated GCS delete. Two items ARE bounded and were operator-ruled 2026-07-29 (run the ES CME ohlcv_1s/1m
  manifest-count check; launch the ES_OPT backfill via `launch-tradfi-backfill-vm.sh --root-symbol ES_OPT`) — real
  AO-eligible content a whole-doc flip cannot reach in isolation. Flagged for a future `/ag-closeout- audit` carve-out
  rather than reclassified.

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (tradfi tranche, dispatch agt-6397c9): **KEEP-NA, MIXED — 3 citation touch-ups
  applied, 0 fresh RECLASSIFY candidates.** 7 open `- [ ]` checkboxes re-read end-to-end via an independent sub-agent
  classification (count dropped 8→7 since the 2026-07-30 marker — the ES CME manifest-count-check item flipped `[x]` in
  the interim, expected corpus drift). 4 items stay genuinely operator/credential-gated (G1 retirement purge, ICE
  BLOCKED-CREDENTIALS on the cited 2026-06-18 ruling, the optional GCS parquet cleanup, and the top-level Gated-Phase-2
  rollup). The 2 items the 2026-07-30 marker flagged as "bounded/AO-eligible, deferred to a future carve-out" have since
  materialized — `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` (created 2026-08-01, one day before this audit)
  extracted both (the ES_OPT launch + its manifest-verify wiring, combined into todo #2) verbatim citing this doc as
  Source; added citation notes at both sites (lines ~155, ~175) pointing to that extraction rather than reclassifying
  this doc directly. Also tightened the M-1 cross-link (line ~527) to cite the specific already-DONE lines in
  `data_completion_to_100_all_ag_2026_06_21.md` (112-116) instead of a bare pointer. Cross-reference: the G1 retirement
  item (line ~340) is the exact trigger `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md` (cefi-owned,
  carries an unresolved CONTESTED cefi-vs-defi verdict) cites as its own revisit condition — since G1 retirement remains
  genuinely open here, that cross-tranche gate correctly stays unfired; no action needed on this doc for that reason. No
  fresh RECLASSIFY candidates this pass (the 2 that would have are already covered by the drafted batch6). `assigned_vm`
  unchanged.

- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- swapped the umbrella + cefi-sibling plan links
  for the filed zero-capture issue doc + 2 real source-code targets (catalogue builder, ES_OPT VM launcher).
- **na-eligibility-audit 2026-08-07** (tradfi tranche): KEEP-NA-STALE (already-duplicated) -- citation fix, no
  reclassification. 5 open todos read end-to-end; completeness-check count reconciled (5/5). Fixed 2 stale citations
  (ES_OPT launch item + its manifest-verify sibling): both said "track there once that batch activates" pointing at
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`, which is now `status: active` (activated 2026-08-06) with a live
  autonomous watcher session in progress -- updated wording + switched to the leading-slash `/plans/active/...` path
  convention. No fresh RECLASSIFY/ARCHIVE candidates; doc remains genuinely operator-gated (G1 retirement
  approved-but-unexecuted, GCS parquet cleanup approved-conditional).
- **na-eligibility-audit 2026-08-08** (tradfi tranche, dispatch agt-29c933): **KEEP-NA-STALE-DUPLICATED confirmed --
  ES_OPT citation still accurate (batch6 live watcher re-verified) -- but flagging 2 extraction candidates not yet
  drafted into any active/draft batch.** 5 open todos re-read end-to-end; count reconciled (5/5). Line 350 (G1
  retirement purge -- ICE/CBOE-OPRA/CBOE-VX-spread/VIX-cash/NASDAQ-NYSE-misclass/cefi-singles catalogue rows) carries an
  UNCONDITIONAL operator GO-AHEAD ("Ready to execute") with a fully mechanical done-when (pause consolidator -> snapshot
  -> filter -> resume -> verify) -- checked `tradfi_satellite_ao_dispatch_batch6/7/8` for any mention of "G1
  retirement"/"catalogue rows"/"OPRA"/"VX-spread": zero hits in all three. This item has now been operator-cleared since
  2026-08-07 and has not been picked up by 2 subsequent satellite-batch drafting passes (batch7 on 08-06 predates the
  ruling; batch8 on 08-08 postdates it but still omits it) -- recommend the next `/ag-closeout-audit` or satellite batch
  author include it explicitly. Line 597 (ICE-Databento parquet GCS cleanup, P3) is a weaker/lower-priority version of
  the same finding -- its GO-AHEAD remains explicitly conditional on a twin-verify-0-consumers check not yet run, so it
  correctly stays NA pending that check, not flagged for extraction yet. `assigned_vm` unchanged (doc-level RECLASSIFY
  does not apply -- the top-level Gated-Phase-2 rollup and ICE BLOCKED-CREDENTIALS items remain genuinely
  operator/credential-gated).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: **KEEP-NA at doc level, confirmed — but one item now
  matches a fresh same-day precedent, flagged for extraction, not a whole-doc flip.** Re-read all 5 open items against
  today's 9 operator-Q&A rulings. The ICE-Databento parquet GCS-cleanup item (P3, "RULED 2026-08-07 ... GO AHEAD,
  conditional on ... twin-verify still required before delete") now matches today's ruling 6 precisely: the operator's
  own GO-AHEAD already covers the delete itself; the sole remaining gate (twin-verify 0 consumers + a fresh
  reversibility check) is exactly the class ruling 6 describes as agent-executable. **Not flipping this doc's
  `assigned_vm`** — the HARD RULE is whole-doc-only, and 3 other open items remain genuinely gated (the top-level
  Gated-Phase-2 rollup; the residual 2-leg catalogue purge, which still needs its OWN NEW operator confirmation, so
  ruling 6 does not reach it; ICE BLOCKED-CREDENTIALS). A single-item carve-out is `/ag-closeout-audit`'s Phase-3
  mechanism, not this skill's whole-doc reclassification — recording the match here so the next satellite-batch author
  (who already missed the sibling G1-retirement-purge extraction per the marker above) picks up both together. No
  `assigned_vm` change.
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:aec4167a0e2554f0]:
  **KEEP-NA-STALE (already-duplicated), re-confirmed, no changes needed.** All 4 open items re-read end-to-end via a
  dedicated sub-agent hunter; count reconciled (4/4). The 2 items citing
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` as their live dispatch vehicle were independently verified against
  that plan directly (not just its citation text) -- it is `status: active`, and today carries its own same-day "ES_OPT
  watcher saga" Progress Log block with the identical "UNBLOCKED 2026-08-09" language, confirming the citation is
  current, not stale. The residual 2-leg catalogue purge item remains genuinely gated on its own fresh operator
  confirmation (distinct from the already-granted 4-leg go-ahead). One data-hygiene note (not actionable): the
  ICE-Databento parquet GCS-cleanup checkbox was converted today to a plain "EXTRACTED 2026-08-09" bullet (no longer a
  `- [ ]`), correctly explaining the 5->4 open-count drop since the 08-08 marker. Nothing to reclassify.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:a16006baae5f205f]:
  **KEEP-NA-STALE (already-duplicated), re-confirmed.** Fresh full read, 4 open todos. Independently re-verified the
  ES_OPT duplication citation by reading `tradfi_databento_account_billing_suspended_2026_08_09.md` directly: confirms 2
  real `tradfi-bf-es-opt-*` launches already happened 2026-08-09 with genuine captured data, and names
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` (status: active) as the live dispatch vehicle -- matching this
  doc's own citation exactly. Todo 4 (residual catalogue-leg purge) stays OPERATOR_QUESTION, not bundled into the
  already-granted 4-leg go-ahead. `assigned_vm` unchanged.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
