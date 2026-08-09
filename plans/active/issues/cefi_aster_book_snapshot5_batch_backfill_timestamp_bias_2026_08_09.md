---
doc_type: issue
title:
  "ASTER book_snapshot_5 hit a NEW, distinct DP-FETCH-009 mechanism (UpstreamTimestampBiasError, not the schema-contract
  bug) -- a batch/historical re-fetch attempted a UAC-declared no-batch-source cell; current code already excludes it,
  root cause is a one-off stale/mis-pinned launch, self-resolved, no code fix needed this session"
summary: >-
  CRITICAL DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) escalation agt-e488d1 (dp-fleet-monitor -> data_pipeline_failure worker,
  slot 4, 2026-08-09), asset_group=cefi data_type=book_snapshot_5: 9,883 attempted_failed of 935,767 attempted in the
  new 14-day-trailing-window detector (ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14, deployment-service meta_watchers.py --
  a DIFFERENT, smaller-scale counting basis than the sibling doc's lifetime-cumulative numbers), flagged Fresh (2,193
  attempted_failed rows in the last 1d, crossing the 500-row materiality floor). Live investigation found this is NOT a
  recurrence of the schema-contract/ts_event bug tracked in
  `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md` (that doc's fix commits all still
  verified ancestors of `origin/live-defi-rollout`; zero schema-contract-violation rows in the last 24h) -- it is a
  GENUINELY DIFFERENT mechanism isolated entirely to venue=ASTER: 2,000 of the 2,193 fresh rows (100% of ASTER's
  contribution) carry `error_reason=UpstreamTimestampBiasError`, `pipeline_mode=batch_aster`, `source=aster`,
  `transport=rest` -- i.e. a BATCH (not live-WS) re-fetch attempt, targeting HISTORICAL `date` partitions (sampled:
  2026-07-24, 2026-08-01), sustained at a steady ~250 rows/hour from 2026-08-08T17:19:24Z through 2026-08-09T01:24:28Z
  (8h), then STOPPED -- zero further rows in the 10+ hours since (verified against current wall-clock
  2026-08-09T11:47Z). Root cause: ASTER's `book_snapshot_5` is a UAC-declared no-batch-source cell
  (`VENUE_DATA_TYPE_NO_BATCH_SOURCE["ASTER"] ⊇ {"book_snapshot_5"}`,
  `unified-api-contracts/registry/market_data_categories.py`) -- its REST depth endpoint (`AsterAdapter.fetch_depth`,
  `market_tick_data_service/market_interface/adapters/onchain_perps/aster_adapter.py:813`) returns ONLY the CURRENT
  order book (no historical range param), so ANY batch/historical re-fetch attempt for this cell is structurally
  guaranteed to fail `UpstreamTimestampBiasError` every single time (the fetched snapshot's real `now()` timestamp can
  never match a historical target `date` partition) --
  `market_tick_data_service/raw_tick_hive.py::validate_day_partition_alignment`, called from
  `engine/orchestrator/partitioned_writer.py::_prepare_write_df`. Verified the CURRENT codebase already guards against
  this correctly: `OnchainPerpBatchHandler._process_venue` (`cli/handlers/onchain_perp_batch_handler.py`) filters every
  venue's requested data_types through `_onchain_perp_batch_live_only.batch_data_types_for_venue`, which consults
  `unified_api_contracts.venue_data_type_has_batch_source(venue, data_type)` and drops ASTER book_snapshot_5 BEFORE any
  fetch is attempted (comment at `_fetch_or_record_absence`'s call site: "so _process_shard is never reached for them"
  -- confirmed true by reading the filter + registry, both currently correct, case-matching, in place since
  2026-07-13/15 per git blame on `7754661a`/predecessor MTDS-local dict). The dedicated launcher for this handler
  (`deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`) explicitly documents this exclusion in
  its own header comment and RELIES on it. Since the guard is provably correct in the live `origin/live-defi-rollout`
  tree, the most likely explanation for this run is a ONE-OFF operational artifact -- e.g. the terminated VM (no GCP/AWS
  instance matching aster/onchain/hyperliquid found running at investigation time, both clouds checked) was launched
  with an explicit stale `MTDS_TARBALL_SHA` metadata pin (the launcher supports SHA-pinned tarballs for reproducibility,
  `gs://deployment-scripts-central-element-323112/code/mtds-code@<sha>.tar.gz`) predating the 2026-07-13/15 fix, rather
  than the unpinned `mtds-code.tar.gz` (confirmed freshly rebuilt, 2026-08-09T11:31:52Z) -- this specific mechanism is
  NOT confirmed (the VM already terminated, no census/log bucket located within this session's bound), only inferred as
  the best-fit explanation given every other layer checks out correct. No code change made this session -- current code
  is already correct; nothing to fix. Filed per findings-triage (a genuinely new mechanism, distinct from the sibling
  doc's schema-contract scope) with a P3 follow-up to confirm/rule out the stale-tarball-pin hypothesis if this exact
  shape (ASTER + UpstreamTimestampBiasError + pipeline_mode=batch_aster) recurs.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-service]
scope: [engineer]
tags:
  [
    data-correctness,
    upstream-timestamp-bias,
    batch-vs-live,
    no-batch-source,
    aster,
    book_snapshot_5,
    dp-fetch-009,
    escalation,
    self-resolved,
  ]
related:
  [
    /plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md,
    /plans/archive/issues/mtds_cefi_docker_image_stale_5mo_2026_07_30.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-09
author: unknown
parent_epic: cefi_master
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
execution_scope: local-only
resolved_by:
source:
  "CRITICAL DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) escalation agt-e488d1, dp-fleet-monitor -> agent-orchestrator
  data_pipeline_failure worker (slot-4), fired 2026-08-09, asset_group=cefi data_type=book_snapshot_5, 9,883/935,767
  (1.1%), Fresh (2,193 attempted_failed rows in the last 1d)."
last_updated: 2026-08-09 (filed, investigation complete, no code fix needed)
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_onchain_perp_batch_live_only.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh,
  ]
---

# ASTER `book_snapshot_5` batch re-fetch hit its structural no-batch-source limit -- `UpstreamTimestampBiasError` (2026-08-09)

## Alert as received

```
Event: DP_RUN_MOSTLY_EMPTY (DP-FETCH-009), severity CRITICAL, asset_group=cefi, data_type=book_snapshot_5
9,883 attempted_failed cells of 935,767 attempted (ratio 1.1%; abs>=500 or ratio>=10%)
"A backfill exited 0 / captured climbed but failed this batch invisibly."
Fresh -- 2,193 attempted_failed row(s) in the last 1d.
```

No issue doc was pre-filed (`Filed issue: (none — alert carries the details)`). **Note on the numbers**: this detector
reads over a 14-day trailing window (`ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14`,
`deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py`) — a materially different, SMALLER
counting basis than the sibling doc's lifetime-cumulative ~300k/1.1M numbers for the SAME `(cefi, book_snapshot_5)`
cell. The two documents are not directly comparable by raw numerator/denominator.

## Investigation

1. **Ruled out a schema-contract regression first** (pre-task plan/issue conflict check): read
   `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md` (26+ prior dispatches). Re-verified all
   6 of that doc's fix commits are still ancestors of `origin/live-defi-rollout`
   (`market-tick-data-service@339ca767`/`@6bf568ee`, `unified-api-contracts@8db188fe`/`@1c4d8864`,
   `deployment-service@a564cca`/`@1b035c52`/`@9102eb9b`) — all OK.
2. **Pulled a live, column-projected manifest read**
   (`gs://market-data-tick-cefi-prd-central-element-323112/_index/ availability_index.parquet`, bounded via
   `scripts/dev/run-bounded-analysis.sh`) of the last-24h `attempted_failed` breakdown by `error_reason`/`venue`: 2,193
   total, of which 2,000 (100% of ASTER's rows) = `UpstreamTimestampBiasError` on venue=ASTER; the remainder (193 rows:
   COINBASE-SPOT/FUTURES concurrent-IP-lock 91, HYPERLIQUID "unknown coin ticker" 50, DERIBIT UNCLASSIFIED_VENUE_ERROR
   50, 2 misc) are the OTHER already-tracked Tardis rate-limit family
   (`cefi_high_attempted_failed_batch_cluster_2026_07_23.md`) at ordinary noise volume — not investigated further, below
   materiality individually.
3. **Isolated the ASTER tail's full lifetime shape**: zero rows before 2026-08-08 (a couple of 1-row stray pings on
   07-26/07-27), then exactly 2,000 rows from 2026-08-08T17:19:24Z to 2026-08-09T01:24:28Z at a steady ~200-250/hour,
   then a hard stop — zero rows in the 10+ hours since (checked against wall-clock 2026-08-09T11:47Z). Cross-checked
   `capture_status` for the same window: normal `captured` bursts (~500 rows) around 22:00-23:59 UTC on 2026-08-06/07
   (the ordinary daily-job shape), a small overlapping burst of legitimate captures during the failing window itself
   (490 captured + 250 failed in the same 23:00 hour on 2026-08-08), and full recovery to normal captured volume
   (366+131 rows) by 2026-08-09T10:00-11:00Z.
4. **Sampled full row detail** (first + last failing rows): both carry `pipeline_mode=batch_aster`, `source=aster`,
   `transport=rest`, `service_name=market-tick-data-service`, and — critically — a `date` partition of `2026-07-24` and
   `2026-08-01` respectively (HISTORICAL dates, not "today"). This is a BATCH re-fetch of historical shards, not the
   live WS connector (which uses `datetime.now(UTC)` receive-time and writes via a completely different path —
   `LiveWebsocketTickSink.flush`, which never calls `validate_day_partition_alignment` at all;
   `raw_tick_hive.py`/`partitioned_writer.py` is the ONLY call site that can raise this error, and it's used by exactly
   two batch writers, both keyed to `OnchainPerpBatchHandler`/`venue_fetch.py`).
5. **Confirmed ASTER `book_snapshot_5` is a UAC-declared no-batch-source cell**:
   `VENUE_DATA_TYPE_NO_BATCH_SOURCE["ASTER"] = frozenset({"book_snapshot_5", "liquidations"})`
   (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:2679`), consulted via
   `venue_data_type_has_batch_source()`. `AsterAdapter.fetch_depth`
   (`market_interface/adapters/onchain_perps/ aster_adapter.py:813`) can only ever return the CURRENT order book (no
   historical range param on Aster's REST) — its own docstring says so explicitly. Any batch attempt at a historical
   `date` for this cell is therefore STRUCTURALLY guaranteed to fail the day-partition check every time: the fetched
   row's real timestamp is always "now", which can never equal a backfill target day in the past.
6. **Confirmed the CURRENT code already excludes this correctly** — traced the full call chain:
   `OnchainPerpBatchHandler.process()` → `_process_venue()` →
   `batch_data_types = _batch_data_types_for_venue(venue, data_types)`
   (`= _onchain_perp_batch_live_only.batch_data_types_for_venue`) → filters out `(ASTER, book_snapshot_5)` via
   `venue_data_type_has_batch_source()` BEFORE `_process_shard`/`fetch_depth` is ever called. Verified venue casing
   (`"ASTER"`, upper-cased by `_resolve_csv_arg`) and data_type casing (`"book_snapshot_5"`, lower-cased) both match the
   registry key exactly — no casing bug. This exclusion has been in place since 2026-07-13 (MTDS-local dict) /
   2026-07-15 (moved to UAC, `7754661a`) — i.e. well before this incident. The dedicated launcher
   (`deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`) documents + relies on this exclusion in
   its own header.
7. **Searched for the producing VM**: neither GCP (`gcloud compute instances list`) nor AWS
   (`aws ec2 describe-instances`) currently shows a running instance matching `aster`/`onchain`/`hyperliquid` — whatever
   ran this has already terminated/self-deleted, consistent with the clean stop at 01:24Z and normal capture resuming
   since. Could not locate a VM census/log bucket for this launcher family within this session's time bound to
   positively identify which specific launch produced this (a genuinely open item, not chased further — see Todo below).
8. **Checked the "stale image" precedent** (`mtds_cefi_docker_image_stale_5mo_2026_07_30.md`, archived/resolved
   2026-08-07): that finding was about 7 DIFFERENT Cloud Run jobs
   (`market-tick-cefi-{binance-futures,okx, daily-download}`, all now deleted) sharing a stale
   `market-data-tick-handler` image — NOT the same mechanism as this VM-tarball-based launcher, but the SAME general
   failure class (stale deployed artifact running pre-fix code). The unpinned `mtds-code.tar.gz` in
   `gs://deployment-scripts-central-element-323112/code/` is confirmed freshly rebuilt (2026-08-09T11:31:52Z, i.e. AFTER
   this incident), so if the theory holds, the producing VM most likely used an explicit `MTDS_TARBALL_SHA` metadata pin
   to an older commit (the launcher supports this for reproducibility) rather than picking up a stale unpinned tarball —
   this is inferred, not confirmed.

## Conclusion

**No code fix needed this session.** The current codebase on `origin/live-defi-rollout` already correctly excludes
`(ASTER, book_snapshot_5)` from every batch/historical fetch path. The 8-hour failure window is best explained as a
one-off VM launch using stale/pinned code that predates that exclusion (or a launch invoked outside the standard
launcher's guardrails); it has already self-resolved (zero recurrence in 10+ hours, normal capture volume restored).
This is a GENUINELY DIFFERENT root cause from the sibling doc's schema-contract/`ts_event` bug — filed as its own issue
rather than folded into that doc's already-closed scope.

## Todos

- [ ] [OPS] P3. If this exact shape recurs (`venue=ASTER`, `error_reason=UpstreamTimestampBiasError`,
      `pipeline_mode=batch_aster`, historical `date` partitions), identify the specific launch: check whether
      `launch-cefi-hl-aster-historical-backfill.sh` was invoked with an explicit `MTDS_TARBALL_SHA` metadata pin
      predating `7754661a` (2026-07-15) — confirm via
      `gcloud compute instances describe <name> --format="value(metadata)"` if the VM is still alive, or a VM census/log
      bucket if a per-launch record exists. If confirmed, either stop pinning stale SHAs in that launcher's
      runbook/history, or add a belt-and-suspenders `assert     venue_data_type_has_batch_source(venue, data_type)`
      directly inside `_fetch_shard_rows`/`_process_shard` (defense-in-depth against ANY future caller bypassing the
      `_process_venue`-level filter, including a stale artifact) — a genuine design/ops-judgment call on which layer
      should own the guard, not unilaterally added here given the CURRENT code is already provably correct at the
      primary choke point.

## Progress Log

- **2026-08-09 (data_pipeline_failure escalation worker, agt-e488d1, slot 4):** Investigated DP_RUN_MOSTLY_EMPTY
  (DP-FETCH-009) for cefi/book_snapshot_5. Ruled out a schema-contract regression (sibling doc's 6 fix commits all still
  ancestors). Live manifest read isolated a genuinely NEW, distinct mechanism: 2,000 `UpstreamTimestampBiasError` rows
  on venue=ASTER, a batch re-fetch attempt against a UAC-declared no-batch-source cell, sustained 8h
  (2026-08-08T17:19-01:24Z) then self-resolved (zero recurrence in 10+ hours since). Traced the full code path and
  confirmed the current codebase already correctly excludes this cell from every batch path — no code fix needed. Filed
  this doc (no issue doc existed for this specific mechanism) with a P3 follow-up to positively identify the producing
  VM/launch if the shape recurs. No GCS/manifest write, no VM launch, no code change this session. Pinged
  `dp-fleet-monitor` (authoring slot) with this outcome.
