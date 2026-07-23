---
doc_type: issue
title: >-
  5 broken DeFi capture paths (FLASHBOTS/ACROSS/STARGATE/FRAX/ALCHEMY) -- all 5 shipped, applied, and manually-verified
  with real production data
summary: >-
  RESOLVED 2026-07-22. Closes out the "5 broken venues" deferral called out in
  `defi_venue_phase_live_definition_contradiction_2026_07_22.md`'s RESOLVED-partial section and
  `distinct_values_noncanonical_audit_2026_07_20.md`'s DeFi honest-coverage row. All 4 independent sub-fixes (gas_fees
  crash-loop + venue rename, SchemaContract test coverage, Terraform scheduling for 3 new Cloud Run Jobs) were
  adversarially verified SAFE/SAFE-WITH-CAVEATS, then shipped, applied, and each of the 3 newly created jobs plus the
  gas_fees job's new code path was manually triggered end-to-end against real production infra and confirmed to write
  real GCS objects + manifest rows for a real date -- not a smoke-test, not "scheduled and assumed to work." All 5
  venues (FLASHBOTS, ACROSS, STARGATE, FRAX, ALCHEMY) are now genuinely capturing live.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-service]
scope: [engineer]
tags:
  [
    defi,
    mev-events,
    bridge-events,
    vault-share-price,
    gas-fees,
    flashbots,
    across,
    stargate,
    frax,
    alchemy,
    terraform,
    cloud-run,
    cloud-scheduler,
  ]
related:
  - defi_venue_phase_live_definition_contradiction_2026_07_22.md
  - vault_share_price_handler_capture_gap_since_2026_06_22.md
  - plans/active/distinct_values_noncanonical_audit_2026_07_20.md
created: "2026-07-22"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data
drift_direction: advance-code
depends_on: []
resolved_by: this doc
locked_by:
source: >-
  Consolidated design + 3 parallel implementation sub-agents + an adversarial-verify pass earlier the same day; this doc
  records the shipping session that acted on that verdict.
---

# Per-venue outcome

| Venue                        | Sub-fix                                                                                                                                                                                                                                                                                                                                                                                                          | Shipped SHA                                                                                                                        | Terraform / deploy                                                                                                                                                                                                                                                                                                                   | Manual-trigger verification                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Status                                                                                                                                                                                                                                                                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FLASHBOTS** (mev_events)   | Terraform: new Cloud Run Job + Scheduler cron for `collect-mev-events`. SchemaContract `(defi, spot_asset, mev_events)` already registered (test-only diff).                                                                                                                                                                                                                                                     | `unified-api-contracts@0b0442a6` (schema test coverage, pre-existing ancestor confirmed); `deployment-service@600d31c` (Terraform) | Applied via `ENV=prod ./tofu.sh apply -target=...` -- `google_cloud_run_v2_job.job["mev-events"]` + `google_cloud_scheduler_job.defi_collect_cron["mev-events"]` created (targeted plan showed exactly 6 adds / 0 change / 0 destroy before apply; apply completed clean)                                                            | `gcloud run jobs execute uts-prod-mtds-collect-mev-events` -> execution `uts-prod-mtds-collect-mev-events-w6q8m`, **SUCCEEDED in 48.41s**, `succeededCount=1`. Log: `mev_events for 2026-07-21: 100 rows total`. Real GCS object confirmed: `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-21/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=FLASHBOTS/chain=ETHEREUM/instrument_type=spot_asset/data_type=mev_events/FLASHBOTS.parquet`. Manifest per-VM shard updated (`process_final=True`). No `SchemaContractNotFoundError`.                                                                                                                                                                                                                                                                                                                                 | **FIXED, verified live**                                                                                                                                                                                                                                                                                                      |
| **ACROSS** (bridge_events)   | Terraform: new Cloud Run Job + cron for `collect-bridge-events` (handler already rewritten to Alchemy `eth_getLogs`, not The Graph -- stale task-brief premise). SchemaContract `(defi, spot_asset, bridge_events)` already registered.                                                                                                                                                                          | same as above: `unified-api-contracts@0b0442a6`, `deployment-service@600d31c`                                                      | same apply as bridge-events job (see below)                                                                                                                                                                                                                                                                                          | `gcloud run jobs execute uts-prod-mtds-collect-bridge-events` -> execution `uts-prod-mtds-collect-bridge-events-xpssb`, **SUCCEEDED**, `succeededCount=1`. Log: `bridge_events for 2026-07-21: 6767 rows total`. Real GCS objects confirmed for venue=ACROSS (7 token-shard parquets, e.g. `.../venue=ACROSS/chain=ETHEREUM/instrument_type=spot_asset/data_type=bridge_events/USDC.parquet`). Two benign 404-fallback warnings (`_defi_instruments`: no per-day instrument-availability manifest for ACROSS/STARGATE yet) -- non-fatal, handler fell back correctly, not a blocker.                                                                                                                                                                                                                                                                                                                                | **FIXED, verified live**                                                                                                                                                                                                                                                                                                      |
| **STARGATE** (bridge_events) | Same handler/job as ACROSS (`collect-bridge-events` covers both protocols in one run).                                                                                                                                                                                                                                                                                                                           | same                                                                                                                               | same                                                                                                                                                                                                                                                                                                                                 | Same execution (`...-xpssb`) as ACROSS above. Real GCS object confirmed: `.../venue=STARGATE/chain=ETHEREUM/instrument_type=spot_asset/data_type=bridge_events/USDT.parquet`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **FIXED, verified live**                                                                                                                                                                                                                                                                                                      |
| **FRAX** (vault_share_price) | Terraform: new Cloud Run Job + cron for `collect-vault-share-price` (never scheduled before today -- this is why FRAX's data was frozen at `day=2026-06-21`, per `vault_share_price_handler_capture_gap_since_2026_06_22.md`). SchemaContract `(defi, yield_bearing, vault_share_price)` -- confirmed live via `lookup_contract()` for all 5 real venues during adversarial verify (was previously unconfirmed). | `deployment-service@600d31c`                                                                                                       | `google_cloud_run_v2_job.job["vault-share-price"]` + `google_cloud_scheduler_job.defi_collect_cron["vault-share-price"]` created in the same targeted apply                                                                                                                                                                          | `gcloud run jobs execute uts-prod-mtds-collect-vault-share-price` -> execution `uts-prod-mtds-collect-vault-share-price-n4kzf`, **SUCCEEDED**. Log shows all 8 vaults queried at block 25580957 (noon UTC 2026-07-21), including `FRAX/ETHEREUM sFRAX = 1.15959951 FRAX`. Real GCS object confirmed: `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-21/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=FRAX/chain=ETHEREUM/instrument_type=yield_bearing/data_type=vault_share_price/sFRAX.parquet`. Manifest per-VM shard updated (5 entries, 4 new, `process_final=True`). Side effect: MAKER/ETHENA/YEARN_V3/MORPHO_VAULTS also resumed capturing in the same run (all were part of the same ~1-month capture gap documented in `vault_share_price_handler_capture_gap_since_2026_06_22.md`).                                                              | **FIXED, verified live** -- also closes the root cause of `vault_share_price_handler_capture_gap_since_2026_06_22.md` (the capture path was never crash-looping; it was simply never scheduled by any cron -- confirmed by the fact the manual invocation ran clean on the first try, no exception, no partial-vault failure) |
| **ALCHEMY** (gas_fees)       | Code fix in existing job, not new Terraform: bounded 90s freshness-cache warmup (fail-open) breaks the crash-loop caused by `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["defi"]=4200s` > this job's own `timeout=1800s`; separately, venue renamed from per-chain (`SOLANA`/`BITCOIN`/EVM chain name) to `_GAS_FEE_VENUE="ALCHEMY"` at all 4 real `write_defi_rows()` call sites.                                      | `market-tick-data-service@522185a6` (confirmed ancestor of `origin/live-defi-rollout`)                                             | No Terraform change -- existing `uts-prod-mtds-collect-gas-fees` job/cron, only the container image changed. Artifact Registry `:latest` confirmed rebuilt from commit `6ab0359` (which contains `522185a6`) at `2026-07-22T18:21:26Z`, closing the adversarial-verify caveat ("no new container image built from this commit yet"). | `gcloud run jobs execute uts-prod-mtds-collect-gas-fees` -> execution `uts-prod-mtds-collect-gas-fees-rhfzd`. The decisive log line absent in all 4 prior crash-loop attempts (`Fetching <chain> <date>: blocks X-Y`) appeared within ~90s for ETHEREUM, then again for OPTIMISM/BSC/POLYGON/... in sequence, each followed by a real `Wrote N gas fee records for <chain> ... to gs://market-data-tick-defi-prd-central-element-323112` line. Execution reached terminal state **SUCCEEDED in 8m2.55s** (well inside the 1800s timeout), `11004 records across 12 chains (skipped_freshness=0)`. 10/12 chains wrote real rows under the corrected `venue=ALCHEMY/chain=<X>` path; FANTOM was an honest zero-row day; CELO hit an isolated upstream RPC archival-state limitation (not a code regression -- shard isolation caught it and continued). See "Gas-fees terminal-state addendum" below for full detail. | **FIXED, verified live**                                                                                                                                                                                                                                                                                                      |

## Gas-fees terminal-state addendum (ALCHEMY, full result)

Execution `uts-prod-mtds-collect-gas-fees-rhfzd` reached terminal state: **SUCCEEDED in 8m2.55s** (well inside the job's
1800s timeout; no OOM/signal-9/timeout kill), `succeededCount=1`. Final log line:
`Gas fee collection complete: 11004 records across 12 chains (skipped_freshness=0)`. `skipped_freshness=0` confirms the
bounded-warmup fix did not silently disable/degrade any chain's freshness-based skip logic.

Per-chain outcome (all 12 EVM chains attempted, no crash, no unhandled exception -- shard-level isolation held):
ETHEREUM/OPTIMISM/BSC/POLYGON/BASE/ARBITRUM/AVALANCHE/LINEA/MANTLE/AURORA all wrote real records (72 through 2710 rows
each). FANTOM returned 0 sampled records for the day (`No gas fee data for FANTOM on 2026-07-21` -- an honest zero, not
a failure). CELO hit one isolated
`WARNING Failed to collect gas fees for chain CELO: RPC error (eth_feeHistory) ... historical state ... is not available`
-- an upstream RPC archival-pruning limitation on that one chain/provider, not a code regression; the per-chain
shard-isolation design correctly caught it and continued to the next chain rather than crashing the whole run (this is
the exact behavior the crash-loop fix was meant to enable). Real GCS objects confirmed under the corrected venue naming
for all successful chains, e.g.:

```
gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-21/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=ALCHEMY/chain=ETHEREUM/instrument_type=spot_asset/data_type=gas_fees/GAS.parquet
gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-21/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=ALCHEMY/chain=ARBITRUM/instrument_type=spot_asset/data_type=gas_fees/GAS.parquet
```

(and 8 more chains, all under `venue=ALCHEMY/chain=<X>` -- confirming the venue-naming fix: previously these would have
landed under `venue=<CHAINNAME>`.)

**ALCHEMY is now genuinely fixed, verified with real production data.** The isolated CELO RPC-provider issue and
FANTOM's honest-zero day are not regressions and not part of this issue -- CELO's archival-state gap is a provider-side
limitation worth tracking separately if it recurs, not a code bug in this fix.

## Terraform apply detail

Freshly re-planned immediately before applying (state can drift since the earlier adversarial-verify pass):
`ENV=prod ./tofu.sh plan` (untargeted) showed `Plan: 15 to add, 67 to change, 0 to destroy` -- identical to the
adversarial-verify pass's numbers, confirming no unexpected drift. To avoid touching the ~67 benign
`client`/`client_version` metadata updates and 9 unrelated pre-existing/pending baseline resources
(`defi_removal_probe_*`, 4 `canonical` buckets -- both out of this task's scope), applied with explicit `-target` flags
scoped to exactly the 6 new resources:

```
-target='module.defi_collect_job["mev-events"]'
-target='module.defi_collect_job["bridge-events"]'
-target='module.defi_collect_job["vault-share-price"]'
-target='google_cloud_scheduler_job.defi_collect_cron["mev-events"]'
-target='google_cloud_scheduler_job.defi_collect_cron["bridge-events"]'
-target='google_cloud_scheduler_job.defi_collect_cron["vault-share-price"]'
```

Targeted plan confirmed exactly `Plan: 6 to add, 0 to change, 0 to destroy` before apply. `tofu apply` completed clean:
all 3 Cloud Run Jobs + 3 Scheduler crons created
(`uts-prod-mtds-collect-{mev-events,bridge-events, vault-share-price}` + `-cron` suffixed schedulers), confirmed live
via `gcloud run jobs list` / `gcloud scheduler jobs list`.

## What was NOT touched (out of scope, correctly left alone)

- The 67 benign `client`/`client_version` metadata drift updates across unrelated Cloud Run Jobs (artifact of someone's
  manual `gcloud run jobs deploy`/`execute` runs) -- pre-existing, not caused by or related to this change.
- The 9 unrelated pending baseline adds (`defi_removal_probe_*` SA/job/scheduler/IAM, 4 `canonical` GCS buckets) --
  committed by prior, unrelated work, not part of this task's scope.
- Historical `venue=<CHAINNAME>` gas_fees objects predating the venue-naming fix -- not moved (that's a separate,
  operator-gated GCS path-migration issue per this workspace's prod-bucket-mutation rule).
- mev_events handler's ~100-row/day relay-page cap (hard-exits after first page) -- filed as a non-blocking follow-up by
  the design, not fixed here.

## Cross-references updated by this doc

- `defi_venue_phase_live_definition_contradiction_2026_07_22.md` -- its "Deferred, NOT included" list
  (FRAX/ALCHEMY/FLASHBOTS/ACROSS/STARGATE "STILL-BROKEN") is now stale; each of those 5 defects is fixed per the table
  above. That doc's own denominator-visibility question (whether `phase=="pipeline"` venues with real capture should
  count toward `completeness_pct`) is UNCHANGED by this ship -- this doc fixes the underlying capture, not the
  phase-registry question, which remains its own separate operator decision.
- `vault_share_price_handler_capture_gap_since_2026_06_22.md` -- root cause is now confirmed: the capture path was never
  crash-looping, it was simply never on any cron. The new `collect-vault-share-price` Scheduler job (`10 1 * * *` UTC)
  closes the "was it still scheduled at all" open question in that doc. The ~1-month historical gap (2026-06-22 through
  2026-07-21) is NOT backfilled by this ship -- only forward capture is fixed. Backfilling the gap is separate,
  non-urgent work (small volume, no data-correctness risk since the gap is honestly absent, not silently wrong).
- `plans/active/distinct_values_noncanonical_audit_2026_07_20.md`'s "DeFi honest-coverage denominator exclusion" row --
  the "5 deferred with real distinct defects" language is now resolved; all 5 defects are fixed. The row's underlying
  `completeness_pct`/`DEFI_VENUE_PHASE` question is untouched by this ship (same as above).
