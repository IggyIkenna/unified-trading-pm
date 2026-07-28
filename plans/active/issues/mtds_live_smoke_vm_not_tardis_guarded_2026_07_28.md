---
doc_type: issue
title:
  launch-mtds-live.sh does not source the Tardis N=1 concurrency guard — a live-leg smoke check can contend with an
  active Tardis backfill
summary:
  launch-mtds-live.sh creates real Tardis-fetching test-run VMs without sourcing tardis-concurrency-guard.sh, unlike
  launch-mtds-backfill-vm.sh — a live-leg pipeline_e2e_check smoke test against a Tardis-sourced venue can contend for
  the shared single-IP Tardis key with an active real backfill, risking the same 403-storm/false-attempted_failed
  corruption the guard exists to prevent.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, unified-trading-pm]
scope: [engineer]
tags: [tardis, concurrency-guard, mtds, live-leg, pipeline-e2e-check]
related: [/plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md]
created: 2026-07-28
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
resolved_by:
locked_by:
source: cefi_track2_coverage_backfill_checkpoints_2026_07_25.md
---

## What I found

Running `/data-pipeline-check-mtds --asset-group cefi --day 2026-03-15` (the MID-BACKFILL spot-check todo in
`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) while the Track-2 coverage backfill VM
(`cefi-queue-heavy-binancefutu-x17-20260727-210013`) was actively running and holding the sole Tardis IP lease:

- The check's **force/skip legs** (`launch-mtds-backfill-vm.sh`) correctly sourced `tardis-concurrency-guard.sh` and
  were refused/retried for the `BINANCE-SPOT/trades` cell
  (`launcher exited 1 ... 5 streams (default 4 — its own cap) ... Keep total concurrent connections well under Tardis's tolerance`)
  — the guard working as designed. Neither VM (`mtds-backfill-cefi-pipelinecheck-20260728-035930-6f8fe8` force,
  `...-035948-6f8fe8` skip) was ever created (absent from `gcloud compute instances list`).
- The check's **live leg** (`launch-mtds-live.sh --test-run --max-duration-seconds 90`) for the SAME
  `BINANCE-SPOT/trades` cell launched successfully and unconditionally
  (`mtds-live-smoke-cefi-binance-spot-trades-20260728-040020`, `RUNNING`) — no guard refusal, no retry.
  `grep -n "tardis-concurrency-guard\|tardis_concurrency_guard\|TARDIS_VM_NAME_PATTERN\|VM_TARDIS_CONSUMER" deployment-service/scripts/vm/launch-mtds-live.sh`
  returns **zero matches** — the script never sources the guard.

BINANCE-SPOT is Tardis-sourced (`VENUE_TO_ADAPTER_KEY['BINANCE-SPOT'] == 'tardis'`), so this smoke VM used the SAME
shared single-IP Tardis key as the active backfill, concurrently, with zero coordination. This is exactly the condition
the guard's incident history (measured 2026-07-16: N>1 Tardis VMs → ~94% 403 storm + 37,212 false `attempted_failed`
manifest rows + coverage regression) exists to prevent — the live-leg path is simply not wired into that protection.

Checked the backfill VM's `run.log` for the ~2 min window the smoke VM was up: **0 HTTP 403 occurrences** in that window
(real fetching continued cleanly), so no observed damage this time — but that is luck (a 90s single-instrument smoke
fetch is a small fraction of the backfill's total request volume), not a structural guarantee. A longer-running or
repeated live-leg smoke check, or a real `--mode live` producer launch, against a Tardis venue while a real
backfill/sharded-VM run is active could reproduce the measured 403-storm / false-`attempted_failed` corruption.

A prior precedent (`cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md`) exercised `launch-mtds-live.sh --test-run`
successfully for `mtds-live-smoke-cefi-hyperliquid-trades-...` — HYPERLIQUID is CAP-EXEMPT (native-REST, not Tardis), so
that run never touched this gap. This is the first known exercise of the live-leg smoke path against a Tardis-sourced
venue while a Tardis-consuming VM was concurrently running.

## Why it matters

The whole point of the N=1 Tardis cap (codified `tardis-concurrency-guard.sh`,
`/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap) is that EVERY Tardis-consuming VM must be counted, no
matter which launcher creates it. A launcher that creates a real Tardis-fetching VM without sourcing the guard is a
silent hole in that protection — it can corrupt the manifest (false `attempted_failed` rows that later trigger
unnecessary reclass/re-investigation churn, per the already-open `deribit_options_chain_af_g4_blocker_2026_07_03.md`
pattern) and burn real backfill throughput, exactly during the highest-value window (an active coverage backfill).

## Recommended decision

- [ ] [DATA] P1. Source `tardis-concurrency-guard.sh` in `deployment-service/scripts/vm/launch-mtds-live.sh` — call
      `tardis_concurrency_guard` pre-flight + `tardis_guard_reserve_slot` immediately before VM creation, gated on the
      shard's venue being Tardis-sourced (mirror the CAP-EXEMPT venue list already used elsewhere: HYPERLIQUID / ASTER /
      LIGHTER-ZKSYNC / EXTENDED-STARKNET / PACIFICA-SOLANA skip the guard call; every other cefi venue does not). (repo:
      deployment-service)
- [ ] [DATA] P2. Audit sibling live launchers for the same gap (`launch-mtds-live-cefi-consolidated.sh`,
      `launch-mtds-live-prediction-consolidated.sh`, any other `launch-*-live*.sh` under `scripts/vm/`) — grep each for
      the same guard-sourcing markers used above; wire in whichever are missing it. (repo: deployment-service)
- [ ] [DATA] P3. Update `data-pipeline-check-mtds` skill's Phase-2 (live leg) section to note the guard-gap risk and
      recommend deferring live-leg checks for Tardis-sourced venues while a real Tardis backfill/sharded VM is confirmed
      running, until P1 above ships. (repo: unified-trading-pm, `.claude/skills/data-pipeline-check-mtds/`)

No corruption confirmed this run (0 403s observed in the concurrent window) — this is a structural gap finding, not a
live-incident report. Not escalating to the operator as a page; tracked here per the findings-closure rule.
