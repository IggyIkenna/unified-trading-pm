---
doc_type: issue
title:
  /data-pipeline-check-mtds cannot exercise DeFi force/skip legs — its launcher runs op=download, which skips all DeFi
  venues (DeFi needs the collect-* handlers)
summary:
  The pipeline-e2e checker launches launch-mtds-backfill-vm.sh (op=download). The download orchestrator deliberately
  skips all 98 DeFi venues ("use collect-* handlers"), so a DeFi force-leg fetches NOTHING and every DeFi cell fails
  no_parquet. The check mechanism (VM launch/poll/report, write-prefix verify) works; only the DeFi COLLECTION route is
  missing from the checker.
status: open
nature: issue
asset_group: defi
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [defi, pipeline-e2e-check, checker, collect-handlers, download-op]
related: [defi_consolidated_closeout_2026_07_18, defi_mvp_backfill_optimization_ready_2026_07_20]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
drift_direction: stable
depends_on: []
source: ["filed 2026-07-20 during MTDS DeFi pipeline-check work; frontmatter completed 2026-07-21 to pass the schema gate"]
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# /data-pipeline-check-mtds cannot fetch DeFi — download op skips DeFi venues

## What was measured (real VM run, 2026-07-20)

Ran
`pipeline_e2e_check.py --asset-group DEFI --venue AAVE_V3 --data-types lending_indices --day 2025-03-12 --legs force,skip --require-captured --auto-day`
(with `GCP_PROJECT_ID` set + `MANIFEST_ALLOW_STALE_FALLBACK=true` to read capture state during the active rebuild). The
check ran end-to-end — enumerated the shard, sampled a real PROD instrument, launched a real force-leg VM, polled it to
terminal (EXIT 0), and wrote a report. **Verdict: force + skip both FAILED `no_parquet`.**

**Ground truth from the force VM run.log** (`mtds-backfill-defi-pipelinecheck-…-ffe613`) — NOT a glued-id or
migration-boundary issue as first hypothesised:

```
INFO ServiceRuntime: op=download mode=batch ...
INFO API keys validated for 1 data source(s): ['thegraph']
INFO Skipping 98 DeFi venues (use collect-* handlers): ['UNISWAP_V2-ETHEREUM', 'UNISWAP_V3-ETHEREUM', ...]
WARNING No active venues for date=2025-12-31 asset_groups=['DEFI']
INFO Batch complete: 1 results collected   # 0 fetched
```

The checker launches `launch-mtds-backfill-vm.sh`, which has **zero** `collect` references (grep-verified) — it always
runs the generic `op=download`. The download orchestrator **deliberately skips all 98 DeFi venues**, directing them to
the `collect-evm-defi` / `collect-solana-defi` handlers (DeFi is instrument/subgraph-driven, not a Tardis-style bulk
download). So the DeFi force-leg fetches nothing → writes no parquet → `no_parquet`, on EVERY DeFi cell, regardless of
day/venue.

## Why the check still "looks" like it should work

The checker HAS a DeFi-aware branch (`pipeline_e2e_check.py:762`) — but it only shapes the WRITE-VERIFICATION prefix
(`asset_group=defi/` vs `category=defi/`), it does NOT route the FETCH to the collect-* operation. So the check
enumerates DeFi cells + verifies the DeFi write path, but never triggers a DeFi collection. The two other gates it
passed here (Phase-0 `-test-` bucket exists; capture-state read via the stale-fallback merge) are real — only the fetch
is missing.

## Impact on the 6h mandate deliverable #3 ("test all shards under /data-pipeline-check-mtds")

DeFi shards are currently **un-testable** via this checker. The force/skip legs cannot pass for any DeFi cell until the
checker learns to launch the DeFi collection operation. This is a **checker gap, not a pipeline failure** — the DeFi
collect handlers themselves (evm_defi/solana_defi) are exercised in production by the
`uts-prod-mtds-collect-{evm,solana}-defi-cron` schedulers.

## Fix direction (checker enhancement — NOT applied; test-harness change wants real-VM validation)

Route DeFi cells through the collect-* path instead of `op=download`:

- **Option A (preferred):** in `pipeline_e2e_check.py::launch_vm_and_wait`, when `shard.asset_group == "DEFI"`, invoke
  the collect operation — either `launch-mtds-solana-defi-backfill-vm.sh` (Solana venues:
  ORCA/RAYDIUM/KAMINO/PHOENIX/METEORA/LIFINITY/…) or an evm-defi collect launcher / `launch-mtds-backfill-vm.sh` with an
  added `--operation collect-evm-defi` flag (EVM venues: AAVE_V3/COMPOUND_V3/UNISWAP_*/CURVE/…). The collect handlers
  are instrument-driven, so the sampled instrument-id maps to the reserve/pool the handler fetches.
- **Option B:** add an `--operation` passthrough to `launch-mtds-backfill-vm.sh` and have the checker pass
  `collect-evm-defi` / `collect-solana-defi` for DeFi cells.
- Validate on ONE real DeFi cell (AAVE_V3 lending_indices on a captured day) that the collect route writes a parquet to
  the `-test-` bucket + the manifest row shows `captured`, then the skip leg fires the freshness signal.

## Provenance

Found running deliverable #3 of the DeFi catalogue closeout (`defi_consolidated_closeout_2026_07_18.md` Progress Log,
2026-07-20). The checker report is at `plans/audit/results/data_pipeline_e2e_check_mtds_2025_03_12.md` (total=2
failed=2, both `no_parquet`). Test VMs self-deleted (VM_SHUTDOWN_ON_COMPLETION); no lingering spend.
