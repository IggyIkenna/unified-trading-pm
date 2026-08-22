---
doc_type: issue
title: 3 defi MTDS collect-* Cloud Scheduler jobs silently paused since 2026-07-18
summary: >-
  uts-prod-mtds-collect-{dex-pools,evm-defi,solana-defi}-cron are all in Cloud Scheduler
  state PAUSED. Each job's most recent real Cloud Run Job execution is 2026-07-18 (all
  three ended NonZeroExitCode, all on the SAME day) -- a ~29-day silent capture gap across 3
  major defi data_types, with no maintenance-window marker or tracked issue/plan found
  justifying the pause. Discovered as a side-finding while investigating DP-FETCH-009
  escalation agt-95ede4 (defi/oracle_prices) -- see
  /plans/active/issues/defi_oracle_prices_onchain_branch_retry_starvation_2026_08_16.md,
  which found + fixed the identical pattern for the 4th sibling job
  (uts-prod-mtds-collect-oracle-prices-cron) by simply resuming it. NOT yet actioned for
  these 3 -- unlike oracle_prices, no "is there a concurrent backfill VM I'd race" check has
  been done for dex-pools/evm-defi/solana-defi specifically.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [defi, dp-fetch-009, scheduler, cloud-scheduler, data-gap, dex-pools, evm-defi, solana-defi]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /plans/active/issues/defi_oracle_prices_onchain_branch_retry_starvation_2026_08_16.md,
  ]
created: "2026-08-16"
author: slot-1
last_updated: "2026-08-17"
source: data_pipeline_failure escalation agt-95ede4 (DP-FETCH-009, side-finding, not the
  escalation's own asset_group/data_type)
resolved_by:
locked_by:
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/defi_oracle_prices_onchain_branch_retry_starvation_2026_08_16.md,
    deployment-service/terraform/gcp/defi_collection_scheduler.tf,
  ]
---

# 3 defi MTDS collect-* Cloud Scheduler jobs silently paused since 2026-07-18

## What I found

While diagnosing DP-FETCH-009 escalation `agt-95ede4` (asset_group=defi,
data_type=oracle_prices — see the companion doc linked above), found that
`uts-prod-mtds-collect-oracle-prices-cron` was `PAUSED` with no tracked justification.
Checking its 18 sibling defi `collect-*` schedulers
(`gcloud scheduler jobs list --project=central-element-323112 --location=asia-northeast1
--filter="name~mtds-collect"`) found **3 more in the identical state**:

| Scheduler                                | State  | Last real execution           | Result          |
| ----------------------------------------- | ------ | ------------------------------ | ---------------- |
| `uts-prod-mtds-collect-dex-pools-cron`    | PAUSED | 2026-07-18T00:15:04Z            | NonZeroExitCode |
| `uts-prod-mtds-collect-evm-defi-cron`     | PAUSED | 2026-07-18T01:55:02Z            | NonZeroExitCode |
| `uts-prod-mtds-collect-solana-defi-cron`  | PAUSED | 2026-07-18T02:05:02Z            | NonZeroExitCode |
| (sibling `oracle-prices` — already fixed) | was PAUSED, now ENABLED | 2026-07-18T00:05:03Z | NonZeroExitCode |

All 4 last-ran on the SAME calendar day (2026-07-18) and all 4 ended in failure the same
day — strongly suggesting a single shared incident on/around 2026-07-18 triggered someone
to pause all 4 jobs (a reasonable stop-the-bleeding move), which then never got followed up
with a root-cause fix + re-enable. Checked `plans/active/` + `plans/active/issues/` for any
doc referencing these job names, this date, or a "defi scheduler pause" incident — no hit
(grepped `collect-oracle-prices|collect-dex-pools|collect-evm-defi|collect-solana-defi`
across the whole corpus; nothing matches a pause/incident narrative for this date). Also
**⚠️ CORRECTED 2026-08-17 (plan_reconciler, defi tranche)**: the "no hit" claim above is FALSE — re-running the
identical grep against the live corpus DOES hit `plans/active/defi_consolidated_closeout_2026_07_18.md` Track 8
(§"INFRA / forward-data: resume steady-state", dated 2026-07-22), which tracks this EXACT same-day 4-scheduler
pause and names the real gating condition this doc's VM-race check below doesn't account for: resume is gated on
**Track-1/2 landing (so the crons write the canonical shape) AND the in-flight
`canonical-migration-defi-rebuild-*` VM finishing** — not merely "no concurrently-running backfill VM." The
original grep missed it on vocabulary (Track 8 discusses the same incident without repeating the literal
`collect-oracle-prices`-style CLI-operation-name strings). Re-check Track 8's current gate state before resuming
any of these 3 schedulers — do not resume on the narrower VM-race check alone.

Also
checked the `alert_driven_dependency_revocation` `FLEET_HALT` mechanism
(`RevocationActuator._pause_schedulers` — `/codex/05-infrastructure/data-pipeline-alerts.md`
§ "Alert-driven dependency revocation") as a possible deliberate-pause explanation: that
mechanism pauses EVERY scheduler sharing an asset_group via `SCHEDULER_REGISTRY`, which
would mean ALL 19 defi `collect-*` jobs, not a hand-picked 4 — the actual state (15
`ENABLED`, exactly these 4 `PAUSED`) doesn't match that shape, so this looks like a manual
`gcloud scheduler jobs pause` on each of the 4 individually, not the automated FLEET_HALT
actuator.

**Net effect**: `dex_pools`, `evm_defi`, and `solana_defi` (3 of DeFi's highest-volume
data_types per the scheduler.tf comments — dex-pools "writes 64k+ rows/day", evm-defi is
the multi-source aggregate fallback for any chain without an op-specific job) have received
ZERO fresh daily capture for ~29 days as of 2026-08-16. This is exactly the class of gap the
"data pipeline correctness is the heartbeat" HARD RULE exists for.

## Why I didn't just resume all 3 myself

For `oracle-prices` (the companion doc), I confirmed via `gcloud compute instances list`
that no OTHER currently-running backfill VM targets that same operation before resuming its
cron — the only VM found (`mtds-oracle-prices-backfill`) writes via
`MANIFEST_PER_VM_SHARDS=true` per-VM shards, so a concurrent daily cron run doesn't corrupt
anything, just adds modest RPC load. I have NOT done the equivalent check for dex-pools/
evm-defi/solana-defi (no VM currently running with those names, per the same
`gcloud compute instances list` sweep — but I did not check GCS `vm-census/` for a very
recently COMPLETED backfill that might explain a deliberate pause for one of these
specifically, and did not check whether re-enabling risks colliding with any in-flight
manual work another agent/operator might be doing on these three data_types). Given this is
outside my assigned oracle_prices scope for the dispatching escalation, filing this as its
own tracked item rather than acting unilaterally on three unfamiliar data_types in the same
one-shot dispatch.

## Recommended decision

- [ ] [OPERATOR] P1. **INVESTIGATED 2026-08-17 (blocked-questions backlog live check,
      BLK-op-…-06e066fa990d answered FINAL) — NOT resumed, gate still unmet.** (a) Confirmed
      all 3 STILL `state: PAUSED` right now (live `gcloud scheduler jobs describe`) — not
      stale. (b) `gcloud compute instances list` (live, full fleet) shows no VM currently
      targeting dex-pools/evm-defi/solana-defi and no `canonical-migration-defi-*` VM at all
      — the migration-VM race this todo asked about is clear. (c) Going further than the
      narrow VM check, per this doc's own 2026-08-17 correction above: Track 8's REAL gate
      is "Track-1/2 landing AND the migration VM finishing" — checked live, and
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md` (Track 1) is still
      `status: active` with 2 open todos today (P1 "Score coverage per-instrument", P0
      "Residual canon walk C2-C12"). **Track 1 has NOT landed** — resuming now would race
      these 3 collectors' writes against the still-in-flight canonicalization work, exactly
      what the gate exists to prevent. Not ambiguous — a clear NOT-YET. Did not smoke-test or
      resume. Re-attempt once Track 1's 2 remaining todos close (then re-check Track 2/bucket
      hygiene too).
- [ ] [SCRIPT] P2. **Root-cause the shared 2026-07-18 `NonZeroExitCode` failure** that
      preceded all 4 pauses — pull each job's 2026-07-18 execution logs
      (`gcloud logging read` or the Cloud Run execution's own stderr) to confirm whether it
      was a single shared cause (e.g. a bad deploy, a shared credential/RPC-provider outage,
      a UAC/UTL breaking change that landed that day) so the SAME thing doesn't silently
      re-pause these jobs again after they're resumed.
- [ ] [SCRIPT] P2. **After resuming, verify each job's next scheduled fire actually succeeds**
      (`gcloud run jobs executions list --job=uts-prod-mtds-collect-<op> ...` the day after
      resume) — don't just resume-and-walk-away; a job paused for 29 days may have drifted
      dependencies (stale image tag, expired credential, changed upstream schema) that make
      the very next run fail again.

## Codex SSOTs

- `/codex/05-infrastructure/data-pipeline-alerts.md` (DP-WATCHER-004 "scheduler paused with
  no maintenance window" is the closest registered failure mode for this shape, though this
  finding was surfaced by manual investigation, not that watcher — worth checking why
  DP-WATCHER-004 never caught this 29-day gap itself as a follow-up).
- `/codex/02-data/data-pipeline-correctness-hard-rule.md` (no deadline deferrals; this is
  exactly the kind of gap that rule exists to prevent from going unnoticed).

## Progress Log

- **2026-08-16, slot-1 (side-finding from data_pipeline_failure escalation agt-95ede4)**:
  filed this doc after discovering the pattern while diagnosing the oracle_prices sibling.
  Resumed oracle-prices myself (see companion doc); left these 3 for operator/next-dispatch
  triage since I hadn't done the equivalent "is it safe" check for them.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **2026-08-17 (blocked-questions backlog live check)**: answered `BLK-op-defi_collect_schedulers_paused_since_2026_07_18-06e066fa990d`
  FINAL via `POST /api/blocked/{id}/answer` (HTTP 200). Live-reverified all 3 schedulers still PAUSED (not stale),
  confirmed no conflicting VM, then checked the doc's own Track 8 correction's broader gate (Track-1/2 landing) —
  Track 1 still active with 2 open todos, so did NOT resume. See the `[OPERATOR]` todo above for full findings.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries) — added the data-pipeline-correctness-hard-rule codex SSOT (cited in the body's own Codex SSOTs section) + the oracle_prices sibling issue
- **2026-08-22 (slot-19, data_engineering)**: independent corroboration with fresh raw-data evidence (side-finding
  while closing `mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md`'s own
  P1 todo 1). A bounded, filtered live query of the DEFI bucket's raw `_index/per_vm/` shards
  (`service_name=market-tick-data-service`, `data_type=dex_pool_swaps`, `date>=2025-05-31`) returns **ZERO rows** as
  of today — this doc's Cloud Scheduler-state finding (3 collect-* jobs PAUSED since 2026-07-18) is now confirmed at
  the raw-capture-content level too, not just the scheduler-state level: there is genuinely nothing unmerged for this
  exact `(service, data_type)` pair sitting in per-VM shards. A broader unfiltered query of the same bucket/date-range
  DOES find 2,485 rows through 2026-08-22 across other service/data_type pairs, confirming the per-VM shard directory
  itself is healthy/active — the gap is specific to the paused collectors, not a general capture-pipeline outage. No
  action taken on the still-open `[OPERATOR]` resume todo above (outside this session's scope — data-correctness
  investigation only). Doc-only, shipped via `safe-doc-push.sh`.
