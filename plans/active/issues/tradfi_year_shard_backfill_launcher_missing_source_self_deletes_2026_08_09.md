---
doc_type: issue
title: >-
  launch-tradfi-backfill-vm.sh's VM_TASK=cefi-backfill matched no dispatch branch — every year-shard VM self-deleted
  within 2-4 minutes, 0 data written; fixed VM_TASK=mtds-backfill + VM_SOURCE=databento
summary: >-
  While executing batch6 todo #2 (ES_OPT launch), 5 freshly-launched `tradfi-bf-es-opt-*` VMs were each deleted by
  `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` within 2-4 minutes of insert, 0 data written. Root cause:
  `launch-tradfi-backfill-vm.sh`'s `_create_vm()` sets `VM_TASK=cefi-backfill`, but `setup-data-pipeline-vm.sh` has no
  dispatch branch for that value at all (verified via full text search — only `mtds-backfill` exists), so every VM fell
  through to the generic fallback, which never appends `--source` to the MTDS CLI. MTDS hard-fails immediately
  ("--source databento is REQUIRED for a TradFi OHLCV download"), writes 0 rows, and the VM self-deletes via its own
  `VM_SHUTDOWN_ON_COMPLETION=true` convention. This is NOT an external killer, NOT a billing kill-switch, and NOT the
  same root cause as `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md` (that doc's Claude-Code-agent-
  manual-delete finding, principal `unified-trading-sa`, is unrelated — this incident's deleter is `uts-prd-sa`, the
  VM's own attached service account self-terminating per its normal completion contract, just triggered by an immediate
  failure rather than a real completion). Fixed by mirroring the already-shipped pattern in
  `launch-tradfi-forward-poll.sh`: `VM_TASK=mtds-backfill` (the only branch that builds `--source`) +
  `VM_SOURCE=databento`. Fix applied + committed same-session as part of unblocking batch6 todo #2; re-launch confirmed
  VMs surviving past the previous failure window.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [tradfi, vm, backfill, premature-deletion, databento, vm-task-routing, data-pipeline]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-09"
author: slot-28
priority: P1
parent_epic: tradfi_master
source: >-
  Discovered live 2026-08-09 while executing tradfi_satellite_ao_dispatch_batch6-002 (ES_OPT launch todo). The singleton
  lock cleared after ~2.5 days; the first launch attempt's 5 VMs all self-deleted within 2-4 minutes. Investigated via
  `gcloud logging read` / `gcloud compute operations list` / a GCS run.log read + a dedicated sub-agent that traced the
  exact code path, confirming `--source` was never appended for VM_TASK=cefi-backfill.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: fix
estimate_class: bug
estimate_baseline: 0.3
calibrated_ai_days: 0.2
assigned_role: infra
resolved_by:
locked_by:
depends_on: []
---

# tradfi year-shard backfill launcher missing --source — self-deletes within minutes

## Evidence

**Deletion timing** (`gcloud compute operations list --filter='targetLink~"tradfi-bf-es-opt"'`):

| VM                                          | Inserted (UTC) | Deleted (UTC) | Elapsed |
| ------------------------------------------- | -------------- | ------------- | ------- |
| tradfi-bf-es-opt-light-2022-20260809-023757 | 02:38:01       | 02:40:48      | 2m47s   |
| tradfi-bf-es-opt-light-2023-20260809-023814 | 02:38:17       | 02:40:59      | 2m42s   |
| tradfi-bf-es-opt-light-2024-20260809-023829 | 02:38:33       | 02:41:14      | 2m41s   |
| tradfi-bf-es-opt-light-2025-20260809-023847 | 02:38:50       | 02:41:26      | 2m36s   |
| tradfi-bf-es-opt-light-2026-20260809-023902 | 02:39:05       | 02:42:59      | 3m54s   |

All 5 deletes authenticated as `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` (the VM's own attached SA per
`lc_tier_service_account()`, `launcher_common.sh:168` — NOT a Claude Code agent, NOT `unified-trading-sa`), each from a
DIFFERENT `callerIp` matching that specific VM's own external IP — confirming 5 independent self-deletes, not one
centralized deleter.

**run.log** (`gs://deployment-scripts-central-element-323112/vm-logs/tradfi-bf-es-opt-light-2022-.../run.log`):
`tick_data_handler.py::_resolve_source` raised `ValueError: --source databento is REQUIRED for a TradFi OHLCV download`,
batch completed "0 results collected", process exited rc=1, `DEPLOYMENT_FAILED`, then
`VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete`.

## Root cause

`deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh`'s `_create_vm()` (line ~231, pre-fix) hardcoded
`metadata="VM_TASK=cefi-backfill"`. `setup-data-pipeline-vm.sh` has **no dispatch branch for `cefi-backfill` at all**
(confirmed via `grep -n '"cefi-backfill"'` — zero matches; only `"mtds-backfill"` exists as a real branch, plus a stale
example comment at line 22 that never became real code). Every VM launched via this script therefore fell through to the
generic fallback branch (~line 2776), which builds `CLI_ARGS` WITHOUT `--source` — only the dedicated `mtds-backfill`
branch (line 1642) appends `--source $VM_SOURCE` (line 1728), and only when `VM_SOURCE` metadata is present, which this
launcher also never set.

This is a stale copy-paste bug (`VM_TASK=cefi-backfill` makes no sense for a TradFi launcher) that has likely affected
**every** VM ever launched via this script's year-shard default path (`_legacy_es_default`, used for
ES/ES_OPT/MES/IBIT/ETHA) and the ad-hoc single-window mode — the earlier report of "no active venues" / "--source ...
REQUIRED" failures noted in passing elsewhere in the tradfi corpus may trace back to this same root cause. Not
investigated further here (out of scope for this incident) — flagged as a follow-up below.

## Fix applied

`deployment-service@6b1057cc` (same-session): `VM_TASK=cefi-backfill` → `VM_TASK=mtds-backfill` +
`metadata="${metadata},VM_SOURCE=databento"`, mirroring the identical fix already shipped in
`launch-tradfi-forward-poll.sh` (which carries its own comment documenting this exact failure mode). Re-launch of the 5
ES_OPT VMs with the fixed script confirmed all 5 surviving past the previous 2-4 minute failure window (boot/setup phase
progressing normally at last check).

## Known secondary gap (not blocking, not fixed here)

`VM_FORCE_WINDOW` metadata (this launcher's own `--force-window`/`--no-force-window` flag, default `true`) is only wired
to `--force-window` in the generic fallback branch (line 2782) — the `mtds-backfill` branch this fix now routes through
does NOT read `VM_FORCE_WINDOW` at all (it reads a differently-named `VM_FORCE` for its own `--force` flag, which this
launcher never sets). For THIS incident's launch this is harmless (0 pre-existing ES_OPT rows, so the manifest
pre-flight skip-filter has nothing to skip either way), but it means `--no-force-window` silently has no effect on any
launch routed through `mtds-backfill`. Not investigated/fixed here — see action items.

## Second finding (2026-08-09, same session, post-relaunch) — stall-timeout reaps VMs on a slow-but-real historical fetch

After the `VM_TASK`/`VM_SOURCE` fix, all 5 re-launched ES_OPT VMs started genuinely fetching data (confirmed via run.log
— no more `--source` error). But **4 of 5 (2022, 2023, 2024, 2025) went silent for ~10-18 minutes on their FIRST real
(non-holiday) trading day and were then externally deleted** (not self-deleted — no `DEPLOYMENT_FAILED`/
`VM_SHUTDOWN_ON_COMPLETION` line in any of their logs; the log simply stops mid-day, before a `Processed date=...`
completion line, at RSS ~8-10GiB). Only **2026 succeeded** — it processed multiple real trading days
(`venue=CME: 24180 rows written`, `Processed date=2026-01-08: 1 venues ok, 0 failed`) with RSS cycling ~2.6GiB→9GiB→
(presumably down again after each write), never stalling.

**Working hypothesis (not yet confirmed against dmesg/OOM logs — the VMs are already deleted so this can't be verified
post-hoc for this run)**: the launcher header's own comment documents `STALL_TIMEOUT_SEC=600` (a 10-minute log-mtime
watchdog, inherited from `vm-exec-with-gcs-tee.sh`). Fetching a FULL ES_OPT chain (11 underlyings × all
strikes/expiries) for a single historical date produces no incremental log output while the Databento API call is in
flight — if that single call takes >10 min for some (older? more-strikes? less-cached?) dates, the stall watchdog kills
the VM as "hung" even though it's making real, silent progress. 2026 (recent, likely faster/cached Databento response)
apparently never hit this; 2022-2025 (older, possibly slower) did, but not deterministically — investigate before
assuming this exact mechanism without direct confirmation (e.g. add a heartbeat/progress log line INSIDE the fetch call,
or check `STALL_TIMEOUT_SEC` handling for a way to raise it per-launcher).

## Action items

- [ ] [DATA] P1. **Verify the ES_OPT backfill eventually completes across all 5 years and write real data** — 2022-2025
      died mid-fetch (see second finding above); 2026 succeeded. Once the singleton lock is next clear, retry the failed
      year-shards (idempotent, per this task's own safety framing), then run the manifest count-check (venue=CME ×
      ohlcv_1m × instrument_type=options_chain × the 11 canonical ES_OPT instrument_ids) per
      `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` todo #2's own done-criteria. Repo: unified-trading-pm
      (progress tracked in that plan, not duplicated here).
- [ ] [INFRA] P1. **Investigate + fix the stall-timeout-kills-slow-real-fetch pattern** documented in the second finding
      above — either raise `STALL_TIMEOUT_SEC` for `mtds-backfill`-routed ES_OPT launches specifically, or add
      incremental progress logging inside the per-date Databento fetch so the watchdog sees liveness during a
      legitimately slow (not hung) call. Confirm root cause first (check for an actual OOM-killer dmesg entry vs. a
      genuine stall-watchdog kill — the two need different fixes) on the NEXT retry before assuming this hypothesis.
      Repo: deployment-service (`vm-exec-with-gcs-tee.sh`) + market-tick-data-service (Databento adapter fetch path).
- [ ] [INFRA] P2. **Audit whether this same `VM_TASK=cefi-backfill` bug affects other callers of
      `launch-tradfi-backfill-vm.sh`** (BTC/ETH crypto-basis tier-plan, ad-hoc single-window mode) and whether any
      historical ES/BTC/ETH TradFi manifest data that appears "captured" actually came through THIS launcher (broken
      since some unknown-but-possibly-long-ago point) versus a different path. Repo: deployment-service +
      market-tick-data-service (manifest cross-check).
- [ ] [CODE] P3. **Wire `VM_FORCE_WINDOW` into the `mtds-backfill` branch** (or document why it's intentionally scoped
      only to the generic fallback) — currently silently ignored for every `mtds-backfill`-routed launch, including this
      one. Repo: deployment-service, `scripts/vm/setup-data-pipeline-vm.sh`.

## Progress Log

- **2026-08-09, slot-28**: Discovered + root-caused + fixed live while executing batch6 todo #2. Fix committed
  `deployment-service@6b1057cc`; re-launch in progress, VMs surviving past the previous failure window at time of
  filing.
