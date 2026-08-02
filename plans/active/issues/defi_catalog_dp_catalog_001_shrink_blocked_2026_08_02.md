---
doc_type: issue
title: >-
  CRITICAL DP_CATALOG_NOT_RUNNING (DP-CATALOG-001) — defi instrument catalogue stale >24h, traced to the already-known
  R3 per-instrument migration VM stall (dead 9+ days) that gates 4 paused DeFi collector crons
summary: >-
  data_pipeline_failure escalation agt-0e35ed responded to a CRITICAL page: gs://instruments-store-defi-prd-central-
  element-323112/prod/catalog.parquet age 2234min (37.2h) > 24h budget. Root cause traced through gcloud Cloud Run Job
  execution logs (not a guess): the lifecycle-catalogue-regen-defi Cloud Run Job IS firing on its 01:00 UTC schedule,
  but its 3 most recent executions (2026-08-01 incremental, 2026-08-01 full-weekly, 2026-08-02 incremental) all exit 1
  on CATALOGUE_SHRINK_BLOCKED — the monotonic-guard in build_instrument_catalogue.py refuses to promote a rollup that
  has fewer rows than the last-good catalogue. Direct inspection of the current (last-good, 71544-row) catalog.parquet
  confirms 807 pool rows across 9 EVM DEX venues (UNISWAP_V3/V4, CURVE, PANCAKESWAP_V3, VELODROME_V2, AERODROME_V3,
  SUSHISWAP_V3, UNISWAP_V2, CAMELOT_V3) were captured every day through 2026-07-30 and then went completely silent —
  zero pool rows with available_to=2026-07-31 or 2026-08-01 anywhere in the catalogue. This is NOT a new regression: it
  traces to the ALREADY-TRACKED gated pause of collect-{dex-pools,oracle-prices,evm-defi,solana-defi} (paused 2026-07-18
  per defi_consolidated_closeout_2026_07_18.md Track 8, gated on defi_track01's R3 per-instrument migration completing
  so capture doesn't race live migration writes). Re-verified today via gcloud compute instances/operations list: the R3
  migration VM (canonical-migration-defi-per-instrument-20260719-053435) is CONFIRMED DEAD — zero instances, zero
  operation history — R3 has silently stalled 9+ days (last activity 2026-07-24T07:26 UTC-7), stuck mid-2022 with
  2023-2026 + rebuild_defi_manifest never run. The gate that's blocking cron resume will never clear on its own because
  the thing it's waiting on is dead. This CRITICAL page is the first automated signal that made this stall costly enough
  to notice since the 2026-07-30 oracle_prices issue doc flagged the same VM as "idle."
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    dp-catalog-001,
    dp-alerts,
    catalogue,
    shrink-blocked,
    dex-pools,
    paused-scheduler,
    r3-migration-stall,
    data-correctness,
    critical-page,
  ]
related:
  [
    /plans/active/issues/defi_oracle_prices_capture_stalled_since_2026_07_22.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-02
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [defi_track01_per_instrument_and_canon_id_2026_07_24]
source:
  "data_pipeline_failure one-shot escalation agt-0e35ed, slot-7, 2026-08-02, responding to a CRITICAL DP-CATALOG-001
  page"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/defi_oracle_prices_capture_stalled_since_2026_07_22.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
---

# DP-CATALOG-001: defi catalogue stale — traced to the dead R3 migration VM gating 4 paused collectors

## Evidence trail (all verified live, this session — `gcloud` as `unified-trading-sa`)

1. **The catalogue cron IS firing** —
   `gcloud run jobs executions list --job=lifecycle-catalogue-regen-defi --region=asia-northeast1`: fired daily at 01:00
   UTC every day through 2026-07-31 (success), then FAILED 2026-08-01 and 2026-08-02 (exit 1). The weekly full-rebuild
   (`lifecycle-catalogue-full-defi`, Sat 04:00 UTC) also failed on 2026-08-01.
2. **Failure mode: `CATALOGUE_SHRINK_BLOCKED`** — Cloud Logging on the failed executions shows
   `Monotonic guard: new=71537 current=71544 decision=REJECT (shrink_blocked)` and
   `CATALOGUE_SHRINK_BLOCKED drop-list: {'dropped_delisted': 2884, 'dropped_by_venue': {'UNISWAP_V3': 1298, 'PANCAKESWAP_V3': 381, 'UNISWAP_V4': 324, 'TRADER_JOE_V2': 304, 'CURVE': 139, 'ORCA': 131, 'VELODROME_V2': 96, 'SUSHISWAP_V3': 71, 'AERODROME_V3': 58, 'CAMELOT_V3': 47, ...}}`
   — same shape (same venues, overlapping sample IDs) across all 3 failed runs, including the FULL rebuild (rules out an
   incremental-window artifact).
3. **Direct catalog.parquet inspection** (downloaded + read via pandas, 71544 rows, kept-good copy since promote is
   blocked): of the `instrument_type=pool` rows, exactly **807 rows across 9 EVM DEX venues (UNISWAP_V3/V4/V2, CURVE,
   PANCAKESWAP_V3, VELODROME_V2, AERODROME_V3, SUSHISWAP_V3, CAMELOT_V3) have `available_to == 2026-07-30`** (i.e.
   captured every day up to that date) and **zero rows anywhere in the catalogue have `available_to` of 2026-07-31 or
   2026-08-01** — a clean, sudden stop, not gradual pool death.
4. **Traced to the known gated pause, not a new bug.** `gcloud scheduler jobs describe` on the 14
   `defi_collection_ scheduler.tf` crons: exactly 4 are `state: PAUSED` — `oracle-prices`, `dex-pools`, `evm-defi`,
   `solana-defi`. Audit log (`protoPayload.serviceName="cloudscheduler.googleapis.com"`) confirms
   `ikenna@odum-research.com` paused all 4 on **2026-07-18T19:15 UTC** and never resumed them. This exact pause is
   already fully documented: `/plans/active/defi_consolidated_closeout_2026_07_18.md` Track 8 (`gate_on_depends: true`,
   depends_on `defi_track01_per_instrument_and_canon_id_2026_07_24` +
   `defi_lending_writer_retire_prerequisite_2026_07_20`) and independently re-confirmed by
   `/plans/active/issues/defi_oracle_prices_capture_stalled_since_2026_07_22.md` (slot-16, 2026-07-30) for the
   oracle_prices leg specifically — that agent correctly declined to un-pause, citing the same gate, and flagged the
   migration VM as idle 6 days as a heads-up for Track 1's owner.
5. **NEW as of today: the gate's prerequisite is confirmed DEAD, not just idle.**
   `gcloud compute instances list --filter="name~'canonical-migration-defi-per-instrument'"` and
   `gcloud compute operations list --filter="targetLink~'canonical-migration-defi-per-instrument'"` both return **zero
   results** — no running instance, no operation history at all for
   `canonical-migration-defi-per-instrument-20260719-053435`. Per
   `defi_track01_per_instrument_and_canon_id_2026_07_24.md` R3, last confirmed progress was 2022 applying (2023-2026 +
   `rebuild_defi_manifest` never ran), last activity 2026-07-24T07:26 UTC-7 — **9+ days dead**. R3's own todo checkbox
   still read `[~] RUNNING, partial` until this doc corrected it (same file, same edit as this issue).

## Why this matters now (vs. the existing P1 oracle_prices issue)

The oracle_prices gap has sat as an open P1 staleness issue since 2026-07-30 with no urgency forcing action. Today it
produced a **CRITICAL PagerDuty/Slack page** (`DP_CATALOG_NOT_RUNNING`, `DP-CATALOG-001`) because the defi instrument
catalogue's own shrink-safety guard is now rejecting every rollup attempt — the catalogue has been silently frozen at
its 2026-07-31 22:47 UTC snapshot for 37+ hours and will stay frozen indefinitely (every future rollup will hit the same
guard) until either (a) `dex-pools` capture resumes so the by_date walk can see those pools again, or (b) an operator
explicitly accepts the shrink via `--allow-catalogue-shrink` (NOT recommended blind — see below), or (c) R3 finishes and
the whole gate clears per the documented plan.

**`--allow-catalogue-shrink` is NOT a safe unilateral fix here** — some of the dropped rows are genuinely long-dead
pools (`available_to` months in the past), but the 807-row EVM-DEX-venue subset with `available_to=2026-07-30` are pools
that were being actively captured until capture itself stopped; forcing the shrink would permanently drop real,
recently-live instruments from the catalogue rather than fixing the actual gap (resume capture).

## Decision needed (operator / Track-1 owner)

This is the same decision point `defi_oracle_prices_capture_stalled_since_2026_07_22.md` already surfaced, now with
higher urgency (a CRITICAL page, not just a quiet P1) and confirmation that the blocking migration is dead, not merely
slow:

- **A [WORKER REC]: Assign an owner to relaunch/restart R3** (`canonical-migration-defi-per-instrument`, resume from the
  2022 checkpoint if the SPOT VM's chunked state is recoverable, else restart 2022-2026 + `rebuild_defi_manifest` from
  scratch) so the documented gate can clear normally and the 4 collectors + catalogue resume on the sanctioned path.
  Safest for data consistency; cost is the R3 re-run time (originally estimated ~8-12h before the earlier stall) plus
  whatever caused the VM to disappear needs diagnosing (preemption without recovery? manual delete? crash with no exit
  marker? — not investigated here, out of this issue's read-only scope).
- **B: Decouple `dex-pools` specifically and resume it now.** Since the R3 migration VM is confirmed dead (no live
  writer to race), the specific "resuming now races live migration writes" risk that justified the original pause no
  longer applies literally — though R3 is also _incomplete_ (not finished, not merely paused), so resuming batch writes
  into a manifest whose per-instrument migration never finished 2023-2026 may still create a different kind of
  inconsistency that needs a targeted safety check before doing this blind. Restores catalogue freshness fastest.
- **C: Leave paused, accept the catalogue stays frozen/CRITICAL until R3 relaunches.** No new risk, but the page will
  keep re-firing (or needs a documented suppression) with no ETA since nothing is currently driving R3 to completion.
- **Other:** operator custom direction.

## Todos

- [ ] [OPERATOR] P0. Decide + assign an owner for one of A/B/C above — this is a judgment call spanning the R3
      migration's own risk profile, not something determinable by a worker alone. (repo: unified-trading-pm)
- [ ] [DATA] P1. Once decided: either (a) relaunch/restart R3 per option A, or (b) resume `collect-dex-pools` (and the
      other 3 gated crons as applicable) per option B, then re-run
      `lifecycle-catalogue-regen-defi --mode     incremental` and confirm `CATALOGUE_SHRINK_BLOCKED` clears /
      catalog.parquet mtime advances. (repo: instruments-service, deployment-service)
- [ ] [DATA] P2. Investigate WHY `canonical-migration-defi-per-instrument-20260719-053435` disappeared with zero
      operation history (preemption without a recovery relaunch? manual delete? crashed with no durable exit marker?) —
      this read-only escalation did not dig into that, and the same silent-death mode could recur on whatever VM
      eventually restarts R3. (repo: deployment-service)

## Progress Log

- **slot-7 (data_pipeline_failure escalation agt-0e35ed) 2026-08-02**: Filed while responding to a CRITICAL
  `DP_CATALOG_NOT_RUNNING` page. Traced root cause via live `gcloud` evidence (Cloud Run Job execution logs, direct
  catalog.parquet inspection, Cloud Scheduler state, Cloud Scheduler audit log, Compute Engine instance/operations list)
  rather than guessing. Corrected the stale `[~] RUNNING` status on
  `defi_track01_per_instrument_and_canon_id_ 2026_07_24.md`'s R3 todo with today's dead-VM confirmation. Did NOT resume
  any paused scheduler or pass `--allow-catalogue-shrink` — both are judgment calls belonging to the operator/Track-1
  owner per the existing documented gate, consistent with the prior agent's restraint on
  `defi_oracle_prices_capture_stalled_since_2026_07_ 22.md`. Escalated via `/blocked` to the main agent for a bounded
  wait; this issue doc is the durable record regardless of whether that wait produces an answer in time.
- **slot-5 (data_pipeline_failure escalation agt-0bd299) 2026-08-02, ~1h later**: Re-dispatched by a SECOND CRITICAL
  `DP_CATALOG_NOT_RUNNING` page (age now 2294min/38.2h, up from 2234min/37.2h — monotonically worse, confirming the
  condition is still live, not a stale/duplicate alert). Independently re-verified every load-bearing fact via fresh
  `gcloud`/`gsutil` calls (as `unified-trading-sa`, not from the issue doc's prose) before touching anything: (1)
  `gsutil stat` on `catalog.parquet` — unchanged `Creation/Update time: Fri, 31 Jul 2026 22:47:16 GMT`, byte-identical
  generation `1785538036682790`, i.e. genuinely zero writes since slot-7's check, not a monitor-lag artifact; (2)
  `gcloud run jobs executions list --job=lifecycle-catalogue-regen-defi` — 2026-08-01 and 2026-08-02 01:00 UTC runs both
  still `Completed/False` (failed), no new/retried execution since; (3)
  `gcloud scheduler jobs list --location=asia-northeast1` —
  `uts-prod-mtds-collect-{dex-pools,oracle-prices,evm-defi,solana-defi}-cron` AND their
  `defi-fwd-{dex-pools,oracle-prices}-prd` counterparts (6 jobs total, a superset of the "4" in the original trail) all
  still `PAUSED`; (4) `gcloud compute instances list --filter="name~'canonical-migration-defi-per-instrument'"` — zero
  results, R3 still confirmed dead (the only `canonical-migration-*` instance found anywhere is the unrelated, already
  `TERMINATED` `canonical-migration-defi-gluedcheck-final-233636`). Checked `GET /api/slots/{5,7}/messages` — both
  empty, no operator/main answer has landed on the original `/blocked` question; issue doc `resolved_by:` still blank
  and the `[OPERATOR] P0` todo still unchecked, so the decision is confirmed STILL PENDING, not merely undelivered.
  **Did not re-diagnose from scratch, did not apply any of options A/B/C, and did not file a duplicate issue** — this
  entry exists precisely so a second independent read-only confirmation is on record without duplicating the trail.
  Re-raised via a fresh bounded `/blocked` referencing this doc directly (this is a distinct escalation instance,
  agt-0bd299, not a resend of agt-0e35ed's) so main sees a second, worsening page tied to the same open decision. Pinged
  `dp-fleet-monitor` (authoring slot) with the outcome. No code changes, no scheduler/VM state changes.
- **main, same window (answering `/blocked` BLK-a71a8157)**: INTERIM guidance — direction is **A** (relaunch R3),
  endorsing slot-7's `[WORKER REC]` and matching the root-cause trail, but the relaunch itself
  (`canonical-migration-defi-per-instrument`) is a **destructive canonical migration = operator-sign-off-gated**; main
  cannot self-authorize it. Explicitly **rejected C** (a passively frozen catalogue with a re-firing CRITICAL and no ETA
  is not a resolution — an issue resolves to a path, never passive) and said **do NOT do B yet** (resuming `dex-pools`
  while R3 is incomplete for 2023-2026 risks trading one inconsistency for another; needs a targeted safety proof first)
  — all 6 defi collectors stay PAUSED. Main is escalating the R3 relaunch + owner assignment to the **operator** as
  **standing escalation #1** (age 38.2h, second CRITICAL page). Net instruction to the worker: **hold, apply nothing,
  await operator go on R3**.
- **slot-5 (agt-0bd299), closing this window**: Received + recorded main's interim guidance above. Applied nothing — no
  scheduler change, no VM relaunch, no `--allow-catalogue-shrink` — per the explicit hold instruction. Pinging
  `dp-fleet-monitor` with the outcome and completing this one-shot escalation. The `[OPERATOR] P0` todo below remains
  the correct open item (now additionally tracked as main's "standing escalation #1" to the operator); a future worker
  picking this up should check for an operator go-ahead on R3 before re-deriving anything in this doc.
- **slot-9 (data_pipeline_failure escalation agt-fb2d43) 2026-08-02, THIRD dispatch (age now 2309min/38.5h)**: Read this
  doc in full before touching anything, per its own instruction to prior workers. Did not re-derive the diagnosis from
  scratch. Independently re-verified the two facts that determine whether anything has changed, via fresh `gcloud` calls
  (as `github-actions-deploy@central-element-323112.iam.gserviceaccount.com` — no `unified-trading-sa` creds available
  this session, so `gsutil stat`/`scheduler jobs list` came back auth-denied; used the two calls this identity COULD
  make instead): (1) `gcloud run jobs executions list --job=lifecycle-catalogue-regen-defi` — the 2026-08-01 and
  2026-08-02 01:00 UTC executions are still `0/1` (failed), no new/retried execution since slot-5's check, and
  2026-07-31 remains the last `1/1` success; (2)
  `gcloud compute instances list --filter="name~'canonical-migration-defi-per-instrument'"` — still zero results, R3
  confirmed still dead. Both facts match slot-5's last snapshot exactly — **nothing has changed**, no operator go-ahead
  has landed, no scheduler/VM state has moved. Per main's already-given generic guidance in this same doc ("hold, apply
  nothing, await operator go on R3" — not scoped to just the agt-0bd299 instance), did **not** file a third duplicate
  `/blocked` for the same standing decision; the `[OPERATOR] P0` todo and main's "standing escalation #1" remain the
  live, correct tracking. Applied nothing — no scheduler change, no VM relaunch, no `--allow-catalogue-shrink`. Pinging
  `dp-fleet-monitor` with the outcome and completing this one-shot escalation.
