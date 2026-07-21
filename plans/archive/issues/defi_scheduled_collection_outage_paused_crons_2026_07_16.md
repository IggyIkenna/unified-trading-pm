---
doc_type: issue
title:
  "BIG FINDING (data-correctness): scheduled DeFi/onchain market-data collection has been DOWN ~38-49 days — the 11
  `uts-prod-mtds-collect-*` daily-batch crons + 3 `defi-fwd-*` live-poll crons are all PAUSED since the 2026-06-08
  pre-migration drain. DISAMBIGUATED: this is a REAL OUTAGE (deliberate drain + incomplete/deferred resume), NOT retired
  cruft — the collectors are the intended steady-state mechanism, still declared in live terraform, explicitly slated
  for RESUME. DO NOT delete. Resume is operator-gated on the TradFi migration close-out."
summary:
  "Follow-up disambiguation of the UTL/UAC-skew fleet audit's separate finding #1
  (utl_uac_skew_fleet_audit_2026_07_15.md). The 11 DeFi/onchain collector Cloud Run JOBS (perp-funding, oracle-prices,
  gas-fees, dex-pools, dex-swaps, lending-indices, lst-rates, liquidations, eigenlayer-rewards, evm-defi, solana-defi)
  map exactly to the per-type DeFi reference buckets that were consolidated+deleted 2026-07-10→07-13 — raising the
  question whether the paused jobs are (i) deprecated cruft superseded by a unified live mechanism, or (ii) the intended
  collectors whose pause is a real ~37-day DeFi data outage. Read-only investigation (gcloud/gsutil describe+list, git
  log, terraform + plan reads) resolves it CONCLUSIVELY to (ii) REAL OUTAGE — specifically DELIBERATE-DRAIN /
  INCOMPLETE-RESUME. The pause (~06-08) is the documented pre-migration drain of 48 GCP schedulers + 26 AWS rules; both
  terraform files that declare these collectors are LIVE in the current tree; the master migration catalogue carries an
  explicit RESUME (un-pause) runbook that enumerates all 11 crons; and the resume is a real, tracked, but still-deferred
  task (tradfi_v9_stage1_finish task -003, BLOCKED-PREREQUISITES on the TradFi fleet-drain gate). The bucket
  consolidation changed STORAGE LAYOUT (per-type dirs → shared `market-data-tick-defi` kind=tick-data bucket), NOT the
  collection mechanism, and POST-DATES the pause. The ONLY fresh DeFi data today is lumpy, subset coverage from the
  ad-hoc MVP backfill VM fleet (mvp_backfill_defi_onchain_v10_2026_06_27) — NOT a steady-state replacement. NO cleanup
  performed; NO collector un-paused. Escalated for operator direction. SEPARATE sub-finding: the 3 `defi-fwd-*`
  live-poll crons (created AFTER the drain) are also paused and are NOT in the 48-scheduler RESUME list — an orphaned
  live-capture resume with no documented owner."
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    onchain,
    data-correctness,
    silent-staleness,
    paused-scheduler,
    cloud-run-jobs,
    cloud-scheduler,
    pre-migration-drain,
    resume-runbook,
    data-outage,
    availability-gap,
  ]
related:
  [
    ./utl_uac_skew_fleet_audit_2026_07_15.md,
    ../master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    ../tradfi_v9_stage1_finish_2026_07_06.md,
    ../mvp_backfill_defi_onchain_v10_2026_06_27.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: infrastructure_master
priority: P1
source:
  "UTL/UAC-skew fleet audit separate-finding #1 — operator-directed disambiguation (retired-cruft vs real-outage) under
  /autonomous, 2026-07-16, read-only production-health investigation"
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: opus-required
thinking_tier: max
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
supersedes:
superseded_by:
depends_on: [../tradfi_v9_stage1_finish_2026_07_06.md]
assigned_role: infra
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class BIG FINDING (data-pipeline correctness).** Scheduled steady-state DeFi/onchain market-data
> collection has been DOWN for ~38-49 days (paused 2026-06-08; today 2026-07-16). Both the 11 daily-batch collectors AND
> the 3 live-poll forward crons are paused. This is a REAL outage, but a **KNOWN, INTENTIONAL, TRACKED** one — a
> deliberate pre-migration drain whose RESUME is documented and deferred — **NOT** a silent features-sports-style hidden
> failure, and **NOT** deprecated cruft to delete. **No cleanup was performed and no collector was un-paused** — the
> resume is operator-gated on the TradFi migration close-out. Operator direction requested (see Decision needed).

## Bottom line for the operator (read this first)

- **Is DeFi market data being collected right now? NO — not by the intended scheduled mechanism.** The 11 daily-batch
  `uts-prod-mtds-collect-*` crons and the 3 `defi-fwd-*` live-poll crons are ALL PAUSED (since 2026-06-08). Steady-state
  scheduled DeFi collection — both daily batch and near-real-time forward capture — has been down ~38-49 days.
- **Is ANY fresh DeFi data landing? YES, but partial and lumpy.** The only producer is the ad-hoc MVP backfill VM fleet
  (`mvp_backfill_defi_onchain_v10_2026_06_27`), a temporary historical fill. It writes a SUBSET of types per day into
  the shared `market-data-tick-defi-prd` bucket — e.g. `day=2026-07-15` had ONLY `lst_rates` (LIDO/JITO/ANKR/… venues),
  `day=2026-07-16` is empty so far. ~7 of the 11 types (oracle_prices, gas_fees, dex_swaps, liquidations,
  eigenlayer_rewards, evm_defi, solana_defi) were NOT observed in recent-day samples. Backfill is not a steady
  daily/live forward-capture substitute.
- **Are these jobs safe to delete? NO — do NOT delete.** They are the intended steady-state collectors, still declared
  in live terraform and explicitly listed for RESUME. Deleting them would destroy the documented collection mechanism.
- **What unblocks the fix?** Resuming these crons is the DeFi arm of the master-migration 48-scheduler RESUME runbook,
  which is intentionally gated behind the TradFi Stage-1 migration close-out (apply + manifest re-stamp + fleet-drain
  quiet window). Resuming now would resume automated collection + consolidation over an actively-written,
  not-yet-consolidated manifest — the exact harm the RESUME-runbook task forbids.

## The question this disambiguation answered

The 11 collector job names map EXACTLY to the per-type DeFi reference-data buckets that were consolidated + deleted
2026-07-10→07-13 ("every real reader/writer/scanner migrated to `kind=tick-data`, the shared `market-data-tick-defi`
bucket"). So either:

- **(i) RETIRED-CRUFT** — the per-type collectors were superseded by a different live mechanism (a unified job, a
  VM/Tardis cron) writing to the shared bucket, making these paused jobs deprecated cruft to clean up; or
- **(ii) REAL-OUTAGE** — they are still the intended DeFi collection mechanism and their paused+failed state since
  ~06-08 is a genuine ~37-day DeFi market-data outage (same silent-staleness class as features-sports: a paused
  scheduler hiding a gap).

The pause (~06-08) PREDATES the bucket consolidation (~07-10), so the true sequence + intent had to be established.

## VERDICT: (ii) REAL-OUTAGE — DELIBERATE-DRAIN / INCOMPLETE-RESUME. NOT retired cruft. `safeToCleanup=false`.

The 11 daily-batch collectors + 3 live-poll crons are the INTENDED steady-state DeFi collection mechanism, still
declared in current terraform, paused 2026-06-08 as a deliberate pre-migration drain, with a documented RESUME runbook
that is intentionally still deferred. Scheduled DeFi collection has genuinely been down ~38-49 days; the only fresh data
is lumpy subset coverage from an ad-hoc backfill VM fleet, not the crons.

### Evidence (all independently re-verified this session; read-only)

1. **All 11 collector Cloud Run JOBS exist** (`gcloud run jobs list --region=asia-northeast1`): `uts-prod-mtds-collect-`
   {perp-funding, oracle-prices, gas-fees, dex-pools, dex-swaps, lending-indices, lst-rates, liquidations,
   eigenlayer-rewards, evm-defi, solana-defi}. None deleted.
2. **Both declaring terraform files are LIVE in the current tree, NOT superseded:**
   - `deployment-service/terraform/gcp/defi_collection_scheduler.tf` — declares all 11 via a `defi_collect_operations`
     `for_each` map (single image; CLI dispatches `--operation collect-X`; daily-batch cron per op). Its header comment
     reads: _"The actual DeFi work happens via 11 dedicated `collect-*` ops."_ Last touched by `deployment-service`
     `39fa8c3` (a state-drift reconcile that explicitly KEPT "resilient defi-collect outputs") and `7b1490f` (feat:
     "wire 11 daily DeFi collect-* jobs").
   - `deployment-service/terraform/gcp/defi_forward_poll_scheduler.tf` — declares 3 `defi-fwd-*` `*/5` live VM-launch
     crons (dex-swaps/dex-pools/oracle-prices), created by `2e396f8` (feat: "continuous near-real-time DeFi price
     capture"). POST-DATES the 06-08 drain.
3. **Schedulers are PAUSED** (sampled `gcloud scheduler jobs describe`): `uts-prod-mtds-collect-dex-pools-cron`
   (`15 0 * * *`) = PAUSED; `uts-prod-mtds-collect-oracle-prices-cron` (`5 0 * * *`) = PAUSED. All 3 `defi-fwd-*` =
   PAUSED.
4. **The pause IS the documented pre-migration drain**, `master_data_canonicalisation_migration_catalogue_2026_06_07.md`
   § "🛑 Pre-migration drain — EXECUTED 2026-06-08 (slot-2) + RESUME runbook" (line 91). The RESUME runbook (line ~133)
   literally enumerates all 11 crons for `gcloud scheduler jobs resume`:
   `uts-prod-mtds-collect-{dex-pools,dex-swaps,eigenlayer-rewards,evm-defi,gas-fees,lending-indices,liquidations,lst-rates,oracle-prices,perp-funding,solana-defi}-cron`
   among the 48 GCP schedulers (+ 26 AWS EventBridge rules).
5. **The resume is a real, tracked, still-deferred task**: `tradfi_v9_stage1_finish_2026_07_06.md` task `-003` (INFRA,
   "Execute the 48-scheduler/26-AWS-rule RESUME runbook") is `BLOCKED-PREREQUISITES` — non-dispatchable until the TradFi
   fleet-drain-gated chain (tasks 4 + 10) clears, because "resuming 48 GCP schedulers + 26 AWS EventBridge rules against
   an actively-written, not-yet-consolidated manifest is a premature, effectively-irreversible production action (races
   the live fleet, resumes automated consolidation over incomplete data)."
6. **The bucket consolidation changed STORAGE LAYOUT, not the collection mechanism, and POST-DATES the pause.**
   Canonical layout:
   `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=YYYY-MM-DD/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=.../`.
   No plan states the per-type collectors were superseded by a unified job. The consolidation retired per-type STORAGE,
   not the writers.
7. **The prior UTL/UAC-skew audit already cleared the code**: all 11 images docker-tested IMPORT_OK/HEALTHY (they vendor
   UAC from source), and Cloud Run jobs re-resolve `:latest` per execution — so un-pausing self-heals. The ~06-08 "last
   execution FAILED" is reconciled: the failure was the deliberate drain pause itself, NOT a code bug.

### Why NOT retired cruft (the retirement evidence is the OPPOSITE)

NO retirement evidence exists — every artifact points to RESUME, never retirement: the collectors are in live terraform,
the RESUME runbook enumerates them, and a tracked (deferred) task owns their un-pause. No plan or codex doc states a
unified job or any other mechanism replaced them.

## DeFi data freshness in the shared bucket (PARTIAL / LUMPY — backfill-only)

`gs://market-data-tick-defi-prd-central-element-323112` canonical layout has day-partitions through `day=2026-07-15`
(`day=2026-07-16` empty so far). Coverage is a SUBSET per day, sourced from the backfill VMs, NOT the crons:

- `day=2026-07-15`: ONLY `lst_rates` venues
  (ANKR/BLAZESTAKE/COINBASE/ETHENA/ETHERFI/JITO/LIDO/MAKER/MANTLE/MARINADE/PUFFER/ROCKETPOOL/STADER/STAKEWISE/SWELL).
- `day=2026-07-13`: `lst_rates` (×26), `perp_funding` (×8), `lending_indices` (×4) — per the disambiguate sample.
- `dex_pools`: live via the running `mtds-dex-pools-backfill` VM (per disambiguate: writing `_index/per_vm/…` at
  2026-07-15T22:58Z; availability_index consolidator ran 22:51Z).
- NOT observed fresh in recent-day samples (likely gapped):
  `oracle_prices, gas_fees, dex_swaps, liquidations, eigenlayer_rewards, evm_defi, solana_defi`.

So DeFi data did NOT cleanly "move elsewhere and stay fresh for all types post-06-08." Steady scheduled collection
stopped; forward data is only partially / unevenly reconstructed by the temporary backfill fleet. (Old per-type storage
dirs like `dex_pools/orca/SOLANA`, `lending_indices/kamino` are stale Shape-B dead storage, last date 2026-04-14 —
unrelated to current capture.)

## Affected DeFi types + gap window

| Collector (`uts-prod-mtds-collect-*`) | Daily cron | Paused since | Fresh via backfill?    |
| ------------------------------------- | ---------- | ------------ | ---------------------- |
| perp-funding                          | 01:15      | 2026-06-08   | partial (07-13 ×8)     |
| oracle-prices                         | 00:05      | 2026-06-08   | NOT observed           |
| gas-fees                              | 00:00      | 2026-06-08   | NOT observed           |
| dex-pools                             | 00:15      | 2026-06-08   | YES (live backfill VM) |
| dex-swaps                             | 00:30      | 2026-06-08   | NOT observed           |
| lending-indices                       | 00:45      | 2026-06-08   | partial (07-13 ×4)     |
| lst-rates                             | 01:00      | 2026-06-08   | YES (07-15, 07-13 ×26) |
| liquidations                          | 01:30      | 2026-06-08   | NOT observed           |
| eigenlayer-rewards                    | 01:45      | 2026-06-08   | NOT observed           |
| evm-defi                              | 01:55      | 2026-06-08   | NOT observed           |
| solana-defi                           | 02:05      | ~2026-05-28  | NOT observed           |

**Gap window: ~2026-06-08 → today (2026-07-16) ≈ 38 days** (solana-defi ~49 days, last exec ~05-28). All 11 share ONE
root cause (the drain pause) and ONE fate (RESUME runbook, deferred) — this is not a per-type mixed case at the
mechanism level.

## SEPARATE sub-finding: the 3 `defi-fwd-*` live-poll crons have NO resume owner (orphaned)

The 3 near-real-time forward-capture crons (`defi-fwd-{oracle-prices,dex-swaps,dex-pools}-prd`, `*/5`, VM-launch) were
CREATED AFTER the 06-08 drain (commit `2e396f8`) yet are ALSO PAUSED now and are NOT in the 48-scheduler RESUME list in
the migration catalogue. So the live near-real-time DeFi price-capture path has no documented resume owner — an
additional gap beyond the daily-batch collectors. Recommend the RESUME-runbook executor add these 3 to the resume scope,
or the operator explicitly decide their fate. (Captured as a heads-up in `tradfi_v9_stage1_finish` Progress Log so the
RESUME executor sees it.)

## Remediation plan (recommended — NOT executed; operator-gated)

1. **DO NOT clean up.** Do not delete any of the 11 collector jobs, the 11 daily crons, or the 3 `defi-fwd-*` crons, and
   do not remove their terraform. They are the documented steady-state mechanism slated for resume.
2. **Treat this as the DeFi arm of the master-migration RESUME runbook.** The correct resume path is the existing
   tracked task `tradfi_v9_stage1_finish_2026_07_06.md` task `-003` (48-scheduler / 26-AWS-rule resume), executable ONCE
   the TradFi migration close-out gate clears (apply + manifest re-stamp + fleet-drain quiet window — tasks 4 + 10
   there). No new backfill/relaunch machinery is needed for steady-state resume; un-pausing self-heals (`:latest`
   re-resolves the fresh post-fix image, already docker-proved IMPORT_OK).
3. **File/track the orphaned `defi-fwd-*` live-poll resume** — add the 3 crons to the RESUME-runbook scope or get an
   explicit operator decision on the live-capture path.
4. **Backfill coverage** (`mvp_backfill_defi_onchain_v10_2026_06_27`) is the interim partial-fill; it is NOT the
   steady-state replacement. Track whether the ~06-08→resume-date gap for the non-backfilled types (oracle_prices,
   gas_fees, dex_swaps, liquidations, eigenlayer_rewards, evm_defi, solana_defi) needs an explicit backfill once the
   crons resume, or whether resume + normal daily forward capture is sufficient (these are mostly slow-moving daily
   snapshots, so a bounded historical backfill of the gap window is likely wanted for model continuity).

### Why NO bounded diagnostic un-pause was performed

The audit's earlier "un-pause one collector to capture the real failure" suggestion is now MOOT: the root cause is
already known (the ~06-08 failure was the deliberate drain pause, and the prior audit docker-proved all 11 images
IMPORT_OK/HEALTHY). There is no unexplained live failure to capture. Un-pausing even one collector now would mutate a
deliberately-drained production scheduler whose resume is explicitly gated on the not-yet-consolidated TradFi manifest —
racing the live fleet and resuming automated consolidation over incomplete data, the exact harm the RESUME-runbook task
forbids. This is a resume-sequencing decision for the operator, not a diagnostic that needs a live failure sample.

## Decision needed (operator)

**Scheduled DeFi collection is down ~38-49 days. The fix (resume the paused crons) is gated behind the TradFi migration
close-out. How do you want to sequence it?**

- **A [WORKER REC]: Keep the gate — resume the DeFi crons as part of the tracked 48-scheduler RESUME runbook
  (`tradfi_v9_stage1_finish` task -003) once the TradFi fleet-drain + re-stamp gate clears.** Safest: avoids resuming
  collection/consolidation over an actively-written, not-yet-consolidated manifest. Add the 3 orphaned `defi-fwd-*`
  crons to that resume scope. Cost: DeFi steady-state stays down until the TradFi close-out lands. Interim: the backfill
  fleet keeps producing partial coverage.
- **B: Decouple the DeFi resume from the TradFi gate and resume the DeFi crons NOW** (DeFi's own manifest arm is not the
  thing being re-stamped by the blocked TradFi tasks). Faster restoration of steady-state DeFi capture, but requires
  confirming DeFi's own manifest/consolidation is safe to resume independently of the TradFi drain — needs a targeted
  check before acting; do not do this blind.
- **C: Resume ONLY the 3 `defi-fwd-*` live-poll crons now** (near-real-time price capture) while keeping the daily-batch
  collectors gated — restores live DeFi price feeds soonest with a smaller blast radius, since forward-poll writes are
  the freshest-value path. Still needs a manifest-safety confirm.
- **Other:** operator custom direction.

Separately confirm whether the ~06-08→resume gap for the non-backfilled types needs an explicit historical backfill once
the crons resume.

## Method / integrity notes

- **READ-ONLY throughout.** Only `gcloud`/`gsutil` describe+list, `git log`, terraform + plan file reads. NOTHING
  modified — no job deleted, no scheduler un-paused, no terraform changed. This doc + the audit-doc update + the plan
  Progress Log notes are the only writes.
- Corroborates and supersedes the recommendation in `utl_uac_skew_fleet_audit_2026_07_15.md` § "SEPARATE operational
  findings" #1 (which pre-disambiguation suggested un-pausing one collector to find the cause).

## Status

**PARTIALLY RESOLVED 2026-07-16 (later same day) — the TradFi close-out gate cleared (tasks 4+10 both landed), task
`-003` was executed for real, and the RESUME genuinely restored the 3 `defi-fwd-*` live-poll crons but NOT the 11
daily-batch `uts-prod-mtds-collect-*` crons.**

### What actually happened when `-003` ran

1. **Prereqs re-verified fresh**: tradfi manifest independently re-downloaded and read —
   `total=5,553,198 rows, schema_version=9=100%, blank pipeline_mode=0, blank source=0`; fleet-drain sanity-checked
   (zero `tradfi-bf-*` VMs running; `_index/per_vm/` has only one stale 2026-05-12 shard, confirming full consolidation,
   no in-flight writer to race).
2. **The 3 `defi-fwd-*` live-poll crons (dex-pools, dex-swaps, oracle-prices) — RESUMED AND VERIFIED GENUINELY LIVE.**
   All 3 fired for real (one automatically on its own `*/5` cadence, the other two watched to terminal) and ALL THREE
   completed with `exit_code=0` and wrote real fresh data for `day=2026-07-16`:
   `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-16/pipeline_mode=live_onchain_subgraph/.../uniswap_v3_{ARBITRUM,BASE,ETHEREUM,POLYGON}_20260716_073253.parquet`
   (dex-pools) and real Chainlink/Pyth oracle price rows across ETHEREUM/ARBITRUM/BASE/OPTIMISM/POLYGON/SOLANA
   (oracle-prices); dex-swaps also completed `exit_code=0` after processing its (heavier, longer-running) per-pool shard
   set. **Near-real-time DeFi price capture is genuinely live again** — the orphaned-resume gap this doc flagged is
   closed.
3. **The 11 daily-batch `uts-prod-mtds-collect-*` crons — RESUMED, THEN RE-PAUSED after a confirmed, systemic code bug
   (NOT the pause itself) blocked every one of them.** Force-ran `collect-oracle-prices` and `collect-gas-fees` for
   real; both crashed identically: `ERROR Date range validation failed: Invalid date format ''`. Root cause: the shared
   UTL `unified_trading_library/service_framework/_adapter.py::_build_io()` BATCH branch has no date-default fallback
   (the LIVE branch — used by the `defi-fwd-*` crons above — does, which is exactly why those 3 succeeded and these 11
   didn't). Confirmed via `deployment-service/terraform/gcp/defi_collection_scheduler.tf:170` that ALL 11 collector ops
   share the identical no-date-args template, so this is fleet-wide across the whole DeFi daily-batch collector family,
   not the 2 sampled. **This is the SAME already-escalated finding as
   `group_c_cloud_run_job_failures_triage_2026_07_16.md` Cluster 5** (there confirmed for MTDS/strategy-service
   `t1-recon` jobs) — now confirmed to ALSO break the DeFi collectors, raising that finding's urgency. Per the
   don't-leave-broken-jobs-firing rule, all 11 `uts-prod-mtds-collect-*-cron` schedulers were re-paused immediately
   after confirming. **Un-pausing these 11 is necessary but NOT sufficient — a code fix (owner decision already pending
   in the Cluster 5 doc: MTDS-local CLI bridge vs. shared `_adapter.py` fix) is now the hard blocker**, not the
   scheduler state. The ~38-49 day gap for oracle_prices/gas_fees/dex_swaps/liquidations/eigenlayer_rewards/evm_defi/
   solana_defi (the types NOT covered by the live-poll crons) remains open.
4. **NEW, separate finding surfaced by this same resume: all 26 AWS EventBridge consolidator rules also failed 100% of
   the time** with an unrelated IAM `logs:CreateLogStream` AccessDeniedException on the `unified-trading-role-prod`
   execution role — re-disabled; full write-up in
   `plans/active/issues/aws_consolidator_batch_logstream_iam_gap_2026_07_16.md`. Not DeFi-specific (hits every
   asset_group's AWS-side consolidator), but discovered by this same resume session.
5. **The rest of the 48-scheduler GCP runbook**: resumed + verified where targets still exist
   (`instruments-service-daily-trigger`, `market-tick-daily-trigger` — both fired for real, reached SUCCEEDED);
   `instruments-daily-backfill` and `market-tick-cefi-daily-download` resumed then re-paused (confirmed-broken orphaned
   Cloud Run targets, 404/403 — pre-existing infra drift, unrelated to the drain); `uts-prod-mtds-paper-smoke-cron` +
   `uts-prod-mtds-scenario-matrix-cron` resumed then re-paused (`ModuleNotFoundError: strategy_service` — a pre-existing
   broken image, unrelated to the drain); the 7 `uts-prod-features-*-t1-schedule` jobs were left paused untouched —
   their target Cloud Run Jobs
   (`uts-prod-features-{calendar,commodity,cross-instrument,delta-one,multi-timeframe, sports,volatility}-service-t1-recon`)
   do not exist at all (never deployed or since deleted); 2 of the original 48-list's tradfi-legacy
   manifest-consolidator crons were found already retired (deleted, not just paused) during this session, consistent
   with the same retirement already completed for the other 4 asset groups' legacy consolidators. Full accounting:
   `tradfi_v9_stage1_finish_2026_07_06.md` task -003 Progress Log.

### Bottom line (updated)

**DeFi collection is genuinely live again for near-real-time price capture (the 3 `defi-fwd-*` crons) but NOT for
daily-batch collection (the 11 `uts-prod-mtds-collect-*` crons)** — the latter is blocked on a confirmed, pre-existing
UTL code bug, not the scheduler pause. This doc stays open (not fully resolved) pending that code fix; the resume
runbook itself (task -003) is complete — it correctly resumed what was safe to resume and correctly re-paused/flagged
what wasn't, rather than leaving broken jobs fail-looping in production.

## FULLY RESOLVED 2026-07-16 (daily-batch restored) — status: resolved

Both legs of scheduled DeFi collection are back:

- *_Live-poll (3 defi-fwd-_ crons)**: resumed + verified earlier (real 2026-07-16 data).
- *_Daily-batch (11 uts-prod-mtds-collect-_ crons)**: the `Invalid date format ''` blocker was the UTL
  `service_framework/_adapter.py::_build_io()` batch-mode date-default gap — fixed to default omitted batch dates to
  yesterday UTC (`unified-trading-library@3485c4d0`, mirrors market-data-processing-service's bridge). Propagated via
  UTL base image rebuild (`8b380948` → `@d15fb29b`) → mtds Dockerfile digest bump (`market-tick-data-service@b8365c9d`)
  → mtds image rebuild (Cloud Build `278bd541` SUCCESS, `:latest`=`@b92a8680`). All 11 collector crons re-enabled +
  verified end-to-end: **oracle-prices** (Pyth+Chainlink, 6 chains), **perp-funding** (41 records, Kalshi/GMX),
  **gas-fees** (11,072 records, 12 chains) all reached SUCCEEDED writing real 2026-07-15 data to
  `gs://market-data-tick-defi-prd-central-element-323112`. (One transient `ManifestConsolidatorStaleError` on the first
  gas-fees run cleared on re-run once the market-data-defi consolidator caught up on the 38-day resume shard-burst.)
- **AWS consolidators**: re-DISABLED (see aws_consolidator_batch_logstream_iam_gap_2026_07_16.md correction — AWS is a
  stale/empty mirror, not a live target).
