---
doc_type: issue
title: Seven DeFi MTDS handlers wrote manifest + parquet data to PROD regardless of IS_TEST_RUN
summary: >-
  While running the operator-directed DeFi Ethereum smoke-DUMP (one-block probes into the
  -test- bucket), governance_events and flash_loan_events wrote real per-VM manifest shard
  files into the PROD defi bucket even with IS_TEST_RUN=true set. Root cause: 7 of 14 DeFi
  MTDS collector handlers resolved their write bucket via a bare resolve_bucket_name(cloud=
  "gcp", kind=..., asset_group="defi") call, which is NOT IS_TEST_RUN-aware, instead of the
  test-routed get_write_bucket_name("market_data", "defi") wrapper every other DeFi handler
  uses. Fixed same session; the 2 spurious PROD per-VM shard files (pre-consolidation, created
  by this session, zero downstream consumers) were deleted as self-remediation.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, is-test-run, bucket-routing, manifest, prod-write-safety, smoke-test]
related: [/plans/active/defi_venue_smoke_batch1_2026_08_20.md, /plans/active/venue_smoke_test_bar_2026_08_16.md]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
source: /plans/active/defi_venue_smoke_batch1_2026_08_20.md
resolved_by: market-tick-data-service (this session, SHA to follow ship)
locked_by:
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
context_scope: [/codex/05-infrastructure/gcs-object-operations.md, market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py]
---

# Seven DeFi MTDS handlers wrote manifest + parquet data to PROD regardless of `IS_TEST_RUN`

## What happened

Running the operator-directed Ethereum DeFi smoke-DUMP (`--mode live --asset-group defi`,
`IS_TEST_RUN=true`, per `/data-pipeline-check-mtds`'s Phase-0 `-test-`-bucket pattern), the
first two operations run (`collect-governance-events`, `collect-flash-loan-events`) logged
their per-VM manifest shard write at `market-data-tick-defi-prd-central-element-323112/
_index/per_vm/local-<pid>-<hash>.parquet` — the **PROD** bucket, not the `-test-` sibling.
Both runs returned `0 rows total` (no real chain data was misdirected), but the manifest
per-VM shard write itself was real: `gcs_describe_object()` confirmed both blobs existed in
PROD with today's generation, at 23-23.5 KB each.

## Root cause

`get_write_bucket_name(category, asset_group)` (used correctly by `oracle_prices_handler`,
`lending_indices_handler`, `lending_rewards_handler`, `risk_params_handler`,
`dex_pools_handler`, `lst_rates_handler`, `vault_share_price_handler`) is the ONLY bucket
resolver in this call family that consults `IS_TEST_RUN` (`cloud_constants.py:329`). A bare
`resolve_bucket_name(cloud="gcp", kind=..., asset_group="defi")` call — with no
`deployment_env=` override — always resolves the `-prd-` bucket regardless of the caller's
environment. Seven handlers used the bare form for their `bucket` variable, which every one
of them then reused for BOTH the `DefiManifestRecorder(catalogue_bucket=bucket, ...)`
manifest write AND the `storage.upload_bytes(bucket, shard_path, ...)` parquet data write —
so this is not manifest-only: any prior local/dev/smoke run of these 7 operations that
returned `row_count > 0` would have written real parquet data to PROD too, silently, for as
long as this code has existed.

Affected handlers (grep-verified, all 7 fixed in the same commit as this doc):
`governance_events_handler.py`, `flash_loan_events_handler.py`,
`liquidation_events_handler.py`, `position_data_handler.py`, `dex_swaps_handler.py`,
`staking_yields_handler.py`, `eigenlayer_rewards_handler.py`.

## Fix

Swapped each handler's `bucket = resolve_bucket_name(cloud="gcp", kind=..., asset_group=
"defi")` to `bucket = get_write_bucket_name("market_data", "defi")`, matching the working
7 handlers exactly (same target bucket in PROD; `-test-`-routed only when
`IS_TEST_RUN=true`). No behavior change in production (identical resolved bucket there);
the only behavior change is dev/test/smoke runs now honestly land in the `-test-` sibling.

## Cleanup performed

The 2 spurious PROD per-VM shard files this session's probe run created
(`_index/per_vm/local-95134-b20f.parquet` — governance_events 0-row run,
`_index/per_vm/local-47792-040f.parquet` — flash_loan_events 0-row run) were deleted via
UTL `gcs_delete_object` (never `gsutil`/`gcloud`) immediately on discovery, before the async
manifest consolidator could merge them into the canonical `availability_index.parquet`.
Verified gone via a post-delete `gcs_describe_object` check, and confirmed via
`list_blobs(prefix="_index/per_vm/local-")` that zero other `local-*`-prefixed shards
remained in PROD after cleanup (i.e. nothing else was touched — the prefix is unique to
local/dev-machine runs; real production backfills run on GCE VMs with a different hostname
prefix). No fabricated rows were ever committed to the canonical index; both deleted rows
were also honest 0-row results (real chain state on 2026-08-21), not synthesized data.

## Todos

- [x] ✅ [BACKEND] P0. Fix all 7 affected handlers' bucket resolution to route through
      `get_write_bucket_name`. Evidence: this session's edits to
      `market_tick_data_service/cli/handlers/{governance_events,flash_loan_events,
      liquidation_events,position_data,dex_swaps,staking_yields,eigenlayer_rewards}_handler.py`
      — see the shipping commit for the SHA once quickmerge lands.
- [x] ✅ [BACKEND] P0. Delete the 2 spurious PROD per-VM shard files this session's own
      probe run created, before the consolidator could merge them. Verified gone.
- [ ] [REVIEW] P2. Audit the wider MTDS/instruments-service codebase for any OTHER bare
      `resolve_bucket_name(...)` call sites (non-DeFi asset groups included) that should be
      test-aware `get_write_bucket_name(...)` calls instead — this session only searched the
      14 DeFi collector handlers exercised by the Ethereum smoke-dump; the same bug class
      could exist elsewhere (cefi/tradfi/sports/prediction handlers, or IS's own writers).

## Progress Log

**2026-08-21 — found + fixed + cleaned up in the same session (interactive slot).** Found
mid-flight while running the operator-directed DeFi Ethereum smoke-DUMP
(`/plans/active/defi_venue_smoke_batch1_2026_08_20.md`'s open P1 testnet-verdict todos).
Root-caused, fixed all 7 handlers, deleted the 2 spurious PROD objects, and verified the fix
with a clean re-run (all 14 DeFi collector operations now log their per-VM shard write under
the `-test-` bucket). Todo 3 (wider audit) is left open as a bounded, deterministic follow-up
— out of scope for the smoke-dump task itself.
