---
doc_type: issue
title:
  launch-mtds-backfill-vm.sh applies the Tardis N=1 concurrency guard to EVERY cefi venue, including the documented
  CAP-EXEMPT native-REST ones — makes a MID-BACKFILL force/skip check structurally unable to pass
summary:
  tardis_concurrency_guard fires whenever asset_group=cefi regardless of which venue is being launched, so
  HYPERLIQUID/ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC (documented CAP-EXEMPT, non-Tardis venues) get refused the same as
  real Tardis venues whenever any Tardis-consuming VM is running elsewhere. Running /data-pipeline-check-mtds --legs
  force,skip during the active Track-2 coverage backfill produced total=468 passed=0 failed=124 skipped=344 — every
  attempted cell, Tardis AND non-Tardis alike, was refused by the guard.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, unified-trading-pm]
scope: [engineer]
tags: [tardis, concurrency-guard, mtds, pipeline-e2e-check, launch-mtds-backfill-vm]
related:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/issues/mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md,
  ]
created: 2026-07-28
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/issues/mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md,
    deployment-service/scripts/vm/launch-mtds-backfill-vm.sh,
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
  ]
source: cefi_track2_coverage_backfill_checkpoints_2026_07_25.md
drift_direction: advance-code
depends_on: []
assigned_role: data_engineering
---

## What I found

Running
`/data-pipeline-check-mtds --asset-group cefi --day 2026-03-15 --legs force,skip --mvp-only --require-captured --auto-day`
(the MID-BACKFILL spot-check todo in `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) while the Track-2
coverage backfill VM (`cefi-queue-heavy-binancefutu-x17-20260727-210013`) was continuously running and holding the sole
Tardis IP lease, across a ~48-minute run (04:20:22 → 05:08:01) **every single attempted cell failed** — Tardis venues
(expected, correctly guard-refused) AND the documented CAP-EXEMPT native-REST venues (HYPERLIQUID, ASTER,
EXTENDED-STARKNET, LIGHTER-ZKSYNC — unexpected). Report:
`plans/audit/results/data_pipeline_e2e_check_mtds_2026_03_15.md`,
`total=468 passed=0 failed=124 ambiguous=0 skipped=344`.

Root cause, confirmed in source (not just log inference):
`deployment-service/scripts/vm/launch-mtds-backfill-vm.sh:238-243`:

```bash
if [[ "${DRY_RUN:-false}" != "true" && "$(echo "${ASSET_GROUP}" | tr '[:upper:]' '[:lower:]')" == "cefi" ]]; then
    source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/tardis-concurrency-guard.sh"
    tardis_concurrency_guard 1 "${ZONE}" "${PROJECT_ID}" || exit 1
fi
```

This gates on `asset_group == cefi` ONLY — there is no venue check. Per the same skill's own § 3 ("CAP-EXEMPT venues:
HYPERLIQUID / ASTER / LIGHTER-ZKSYNC / EXTENDED-STARKNET do NOT fetch from datasets.tardis.dev... so their launcher
(`launch-cefi-hl-aster-historical-backfill.sh`) neither sources this guard, and its VM names... do not match
`TARDIS_VM_NAME_PATTERN`") and CLAUDE.md ("Non-Tardis venues (HYPERLIQUID/ASTER/LIGHTER/EXTENDED) are exempt"), these 4
venues do NOT contend for the shared Tardis IP — but `launch-mtds-backfill-vm.sh` (the launcher THIS pipeline_e2e_check
tool + real MTDS backfills for these venues actually use) blocks them anyway whenever ANY Tardis-consuming VM is
running, anywhere, for any reason. Confirmed live in the run log
(`mtds-backfill-cefi-pipelinecheck-20260728-050106-04cd57`, venue=HYPERLIQUID, data_type=trades): identical
`launcher exited 1 ... 5 streams (default 4 — its own cap) ... Keep total concurrent connections well under Tardis's tolerance`
refusal message as every genuine Tardis venue got, despite HYPERLIQUID never touching Tardis at all.

This is the mirror-image bug of the sibling finding `mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md` (that launcher
is MISSING the guard for venues that DO need it; this launcher applies the guard to venues that do NOT need it) — both
stem from the guard being wired in at the wrong granularity (per-asset_group instead of per-venue).

## Why it matters

By definition, a "MID-BACKFILL" checkpoint runs while a real Tardis backfill VM is active — that is the whole point of
the checkpoint. With this bug, `/data-pipeline-check-mtds --legs force,skip` **cannot produce a single genuine `passed`
verdict for cefi during any MID-BACKFILL window**, including for the 4 venues that have nothing to do with Tardis
contention. The resulting `passed=0` in the report is not evidence of a data-pipeline correctness problem — it is 100%
explained by this launcher bug plus the (expected, correct) guard refusal for real Tardis cells. Left unfixed, every
future MID-BACKFILL checkpoint (this plan's, and any other cefi plan's) will report the same false `passed=0` unless
whoever reads it already knows to discount it, which defeats the point of an automated check.

## Recommended decision

> **✅ SAME-FILE COLLISION RESOLVED 2026-07-31** (corpus-wide ownership-conflict sweep, operator ruling: only one doc's
> todo claims the edit, the other cites it). This doc and
> `/plans/active/issues/mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md` both touch the Tardis-guard machinery. They
> now own **disjoint** files: **this doc** owns `tardis-concurrency-guard.sh`'s exempt logic (DONE —
> `TARDIS_CAP_EXEMPT_VENUES` + `tardis_venue_list_needs_guard()`, `deployment-service@2d6b01a`),
> `launch-mtds-backfill-vm.sh` (DONE), and the skill's **§ 3 (Tardis cap)** note (DONE); **the live-smoke doc** owns
> `launch-mtds-live.sh` + the sibling live launchers and the skill's **Phase-2 (live leg)** section. Nothing here should
> edit a live launcher, and nothing there should re-implement the exempt list.

- [x] ✅ [DATA] P1. Scope the guard call in `launch-mtds-backfill-vm.sh` to Tardis-sourced venues only — reuse the same
      CAP-EXEMPT venue list (HYPERLIQUID / ASTER / LIGHTER-ZKSYNC / EXTENDED-STARKNET / PACIFICA-SOLANA) the codex
      already documents elsewhere, e.g. gate on `VENUE_TO_ADAPTER_KEY[venue] == 'tardis'` (UAC) rather than
      `asset_group == cefi`. (repo: deployment-service) — deployment-service@2d6b01a
- [x] ✅ [DATA] P2. **DONE 2026-08-03 (slot-14, data_engineering)** — Re-ran `/data-pipeline-check-mtds` force/skip for
      the 4 currently-live CAP-EXEMPT cefi venues (HYPERLIQUID / ASTER / EXTENDED-STARKNET / COINBASE-CDE — the current
      `TARDIS_CAP_EXEMPT_VENUES` set per `tardis-concurrency-guard.sh`; LIGHTER-ZKSYNC and PACIFICA-SOLANA are excluded,
      per the 2026-07-30 removal and 2026-07-16 decommission respectively — the original bug report's venue list is
      stale on both counts). Repos: market-tick-data-service (skill run, no code change), unified-trading-pm (this doc).

      **Live-contention caveat**: no Tardis-consuming VM (`cefi-queue-*` / `mtds-backfill-cefi-*` matching
              `TARDIS_VM_NAME_PATTERN`) was running anywhere in the fleet during this entire run window (verified before, during,
              and after via `gcloud compute instances list` — confirmed 0 matches) — the CeFi Track-2 coverage backfill chain
              (`cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`) had just died its 6th time
              (`WORKER_STALLED`, `2026-08-03T04:17:48Z`) with no relaunch queued at the time. So this run cannot exercise the
              "Tardis venues correctly refused while a real backfill VM is active" half of P2's ask — that needs a genuine
              MID-BACKFILL window, which wasn't available. What it DOES prove, directly: **every** launch across all 4 venues
              (`scripts/pipeline_e2e_check.py --asset-group cefi --venue <V> --day 2026-03-15 --legs force,skip --mvp-only
              --require-captured --auto-day`, one process per venue) returned launcher `exit_status=0` — **zero** guard
              refusals (the original bug's signature was `vm_not_success:launcher_script_nonzero_rc=1` with 0 parquet writes on
              every attempted cell; that signature appears NOWHERE in any of the 4 reports). Every genuine failure has an
              independent, non-guard root cause, cross-checked against each VM's own `run.log`:
              - **HYPERLIQUID** (`total=18 passed=0 failed=8 skipped=10`): `trades`/`book_snapshot_5` force+skip = honest-empty
                (`OnchainPerpBatch complete ... 0 rows`, real fetch, no data for this instrument/day); `derivative_ticker`/
                `perp_funding` force = `vm_not_success:vm_self_deleted_no_exit_status` (the documented early-boot-preemption
                blind window, § 3d of the skill — infra noise, not a code bug).
              - **ASTER** (`total=18 passed=0 failed=8 skipped=10`): all 4 real cells (`trades`/`book_snapshot_5`/
                `derivative_ticker`/`liquidations`, force+skip) = honest-empty (`OnchainPerpBatch complete ... 0 rows`).
              - **EXTENDED-STARKNET** (`total=18 passed=0 failed=6 skipped=12`): all 3 real cells (`trades`/`derivative_ticker`/
                `ohlcv_1m`, force+skip) failed because the underlying Extended REST call itself 400'd
                (`WARNING Extended /funding AZTEC-USD@LIN: HTTP 400`) — a real venue-API issue, not a launcher/guard problem.
              - **COINBASE-CDE** (`total=18 passed=0 failed=2 skipped=16`): the one real cell (`trades`, force+skip) failed on
                `InstrumentCatalogUnavailableError: cefi catalogue unavailable for the sentinel expected-universe` — the
                already-tracked, separate bug in `issues/cefi_coinbase_cde_urdi_zero_records_2026_07_28.md`.

              No venue passed cleanly (every real cell is a genuine `failed`, not a `passed`) — but that is a **content**
              finding independent of this todo's scope (0-row honest-empties / an upstream HTTP 400 / the tracked
              COINBASE-CDE bug), not a guard-scoping regression. The launcher-guard fix (P1) is confirmed working exactly as
              designed: it neither fires (0 running Tardis VMs → nothing to contend for) nor spuriously blocks these 4 venues
              the way `asset_group == cefi` used to. **P2's "Tardis venues still correctly refused" half stays open as a
              standing verification gap** — re-verify opportunistically the next time a genuine Track-2 (or any Tardis-venue)
              backfill VM is confirmed live, no new todo needed (the launcher code path itself is unchanged since P1 and
              already covered by P1's own manual `tardis_venue_list_needs_guard` unit-level verification).

              **Evidence**: 4 parallel `pipeline_e2e_check.py` runs, `--day 2026-03-15` (this plan's own pinned MID-BACKFILL
              spot-check date), reports at
              `plans/audit/results/data_pipeline_e2e_check_mtds_2026_03_15_{hyperliquid,aster,extended_starknet,coinbase_cde}_nontardis_recheck.{md,json}`
              (this repo — per-venue filenames since 4 same-day runs would otherwise collide on the skill's default
              `{service}_{day}.md` naming). VM names:
              `mtds-backfill-cefi-pipelinecheck-20260803-{144806,144808×2,144811,...}` and their re-runs after an unrelated
              first-attempt orphan-reap — see below. `quality-gates.sh` not applicable (skill run, no code touched in this
              repo or market-tick-data-service).

              **Process note (unrelated to the P2 finding itself, worth recording)**: the first attempt at this run detached
              from the harness's tracked process tree (a nested `bash script.sh &` background pattern) and was killed by the
              shared-host orphan-reap ~5 min in, before any report was written — matches the documented
              `nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md` failure class. Re-ran cleanly via 4
              separate `run_in_background`-tracked invocations (no nested `&`) with no further issues; no cleanup needed since
              `launch-mtds-backfill-vm.sh` stamps `VM_SHUTDOWN_ON_COMPLETION=true` unconditionally, so the orphaned attempt's
              already-launched single-shard VMs self-terminated on their own regardless of the parent checker's death.
              (repo: market-tick-data-service / unified-trading-pm, cited in
              `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`)

- [x] ✅ [DATA] P3. Note in the `data-pipeline-check-mtds` skill's § 3 (Tardis cap section) that
      `launch-mtds-backfill-vm.sh` currently does NOT honor the CAP-EXEMPT list (contradicts the skill's own claim that
      only Tardis venues are gated) until P1 ships — so a MID-BACKFILL force/skip run's `passed=0` should be read
      against this doc, not taken at face value. (repo: unified-trading-pm, `.claude/skills/data-pipeline-check-mtds/`)

      **RESOLVED-MOOT 2026-07-30** — this todo's own trigger condition was "until P1 ships." Re-verified 2026-07-30:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  P1 (`deployment-service@2d6b01a`) is confirmed live in the current codebase
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  (`grep -n "TARDIS_CAP_EXEMPT_VENUES\|tardis_venue_list_needs_guard" scripts/vm/tardis-concurrency-guard.sh
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  scripts/vm/launch-mtds-backfill-vm.sh` shows both wired and in use). Since P1 already shipped, the skill's
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  existing § 3 claim ("Non-Tardis cells... UNAFFECTED... may still run in parallel") is now ACCURATE again —
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  adding a caveat saying it's currently broken would itself be the stale/wrong statement. Decision, not silence:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  no skill-doc edit needed; closing as moot rather than leaving open against a condition that already resolved.

No manifest corruption or data-correctness issue here — every "failed" cell in this run genuinely never launched a VM
(`vm_not_success:launcher_script_nonzero_rc=1`, zero parquet writes), so nothing was mis-captured. This is a
checker/launcher-tooling accuracy gap, not a pipeline correctness regression.

## Progress Log

- 2026-07-28 (cicd agent, plan_health gate agt-6c658d): reclassified `assigned_vm: NA → planning`
  (`execution_scope: orchestrator-agent`, `assigned_role: data_engineering`) — all three todos are bounded, worker-
  determinable outcomes (gate the guard on `VENUE_TO_ADAPTER_KEY[venue] == 'tardis'` instead of `asset_group == cefi`,
  re-run the check, update the skill doc), not an operator judgment call; this NA default was never actually assessed
  for AO eligibility. Done as part of shrinking the `assigned_vm:NA` corpus ratchet back toward baseline.
- 2026-07-28 (slot 7, data_engineering): P1 shipped — `deployment-service@2d6b01a`. Added `TARDIS_CAP_EXEMPT_VENUES` +
  `tardis_venue_list_needs_guard()` to `tardis-concurrency-guard.sh` (the SSOT for the CAP-EXEMPT list, mirroring UAC
  `VENUE_TO_ADAPTER_KEY`) and wired `launch-mtds-backfill-vm.sh`'s guard call to check `--venues` against it before
  invoking `tardis_concurrency_guard`; skips the guard entirely when every requested venue is cap-exempt, still applies
  it (unscoped `--venues`, or any non-exempt venue present) otherwise. Note: verified against the live UAC registry
  (`unified_api_contracts/registry/venue_adapter_keys.py`) that **PACIFICA-SOLANA is decommissioned**
  (`DECOMMISSIONED_VENUE_BASES`, operator ruling 2026-07-16) and no longer a real venue, and that **COINBASE-CDE** is
  also currently a non-Tardis cefi venue (native Advanced Trade REST) not named in this doc's original list — used the
  CURRENT 5-venue set (HYPERLIQUID/ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET/COINBASE-CDE) rather than the doc's
  PACIFICA-SOLANA-inclusive one. `quality-gates.sh` green (deployment-service, 119s); manually verified
  `tardis_venue_list_needs_guard` against empty/single/mixed/case-insensitive venue lists. P2/P3 left open — P2 (re-run
  the MID-BACKFILL checker leg) needs a live Track-2 backfill window to be meaningful; P3 (skill doc note) is a separate
  unified-trading-pm-repo todo.
- **context-scout 2026-08-03**: re-verified context_scope, still accurate (4 entries) — no changes.
- **2026-08-03 (slot-14, data_engineering)**: P2 done — re-ran the MTDS force/skip checker for the 4 live CAP-EXEMPT
  cefi venues (HYPERLIQUID/ASTER/EXTENDED-STARKNET/COINBASE-CDE). Zero guard refusals across all 4 (every launch
  `exit_status=0`); every real failure traced to an independent, non-guard cause (honest-empty 0-row fetches, an
  Extended-side HTTP 400, the already-tracked COINBASE-CDE URDI bug). No live Tardis-consuming VM was running during the
  run window, so the "Tardis venues still correctly refused" half of P2 remains an open, low-priority opportunistic
  re-verify (not a new todo — same launcher code path P1 already covers). Full evidence in the flipped todo above.
