---
doc_type: issue
title: VM fleet SPOT-preemption auto-recovery gap — canonical-migration VMs + open/resolved alert bookend
summary:
  canonical-migration-* launcher never wrote the PREEMPTED signal blob despite being fully registered in the fleet
  relaunch actuator, so 18/20 SPOT TRADFI shards preempted silently with zero auto-recovery; fixing that launcher,
  adding a resolved-bookend alert, and scoping the broader backfill/migration launcher rollout.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-library]
scope: [engineer]
tags: [spot-preemption, auto-recovery, alerting, candle-migration]
related: [candle_feature_canonical_path_divergence_2026_07_20.md]
created: 2026-07-23
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
source: operator-directed, discovered live during the P7 candle-canonical-path migration
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# VM fleet SPOT-preemption auto-recovery gap

## How this was found

While running the TRADFI leg of the candle canonical-path migration (P7d, see
`candle_feature_canonical_path_divergence_2026_07_20.md`), 18 of 20 `SHARD_OF=20` SPOT VMs were preempted within 1-4
minutes of boot — a severe capacity contention event in `asia-northeast1-c`. My own watchdog missed this for ~2 hours
because it only checked `EXIT_STATUS` (never written on a hard preemption kill), not real VM liveness. The operator then
asked: shouldn't the fleet's existing auto-recovery have caught this? Investigation found: **no**, and here's exactly
why, plus what to do about it.

## Root cause (confirmed via code read, not assumption)

`canonical-migration-*` VMs (the launcher this migration uses, `launch-canonical-migration-vm.sh`) are **fully
registered** in the fleet's relaunch machinery:

- `deployment_service/data_pipeline_monitors/launcher_registry.py` — maps
  `canonical-migration-{cefi,tradfi,defi, prediction,sports}-` → `launch-canonical-migration-vm.sh` (registered).
- `deployment_service/vm_prefix_registry.py` — has a `VmPrefixSpec` entry for each of those prefixes (registered).
- `launch-canonical-migration-vm.sh` already calls `lc_write_launch_params(...)` with a FULL resume-capable env
  (`VM_NAME_OVERRIDE`, `RESUME_ASSET_GROUP/START_DATE/END_DATE/MODE/SHARD_OF/SHARD_INDEX`) — shipped in a prior
  session's "adversarial review 2026-07-22" pass specifically to make this launcher `RelaunchPreemptedVm`-compatible.

But it was **missing the one piece that actually triggers detection**: it never called `lc_write_preemption_signal_file`
(`deployment-service/scripts/vm/lib/launcher_common.sh:357`), the helper that writes a GCE shutdown-script which, on a
genuine SPOT reclaim, writes `gs://deployment-scripts-<project>/vm-logs/<vm>/PREEMPTED`. Without that blob,
`exit_code_fleet_monitor.py`'s `is_vm_preempted()` check always reads false, so a preempted `canonical-migration-*` VM
gets classified as `GONE_NO_CAPTURE` (or just never enters the sweep's `running_vms` set at all, depending on how the
sweep's caller populates it) — never `PREEMPTED` — so the `auto_recover` → `RelaunchPreemptedVm` path never fires.

Confirmed via `gsutil ls` on a real preempted TRADFI shard's vm-logs dir: only `LAUNCH_PARAMS.json` +
`TARBALL_PINS.json` present, no `PREEMPTED` blob, no `run.log`, no `EXIT_STATUS`.

**Verified this launcher family is genuinely disjoint from the general day-frontier auto-resume contract** —
`migrate_candle_canonical_2026_07.py`'s own docstring (~line 110/998) states its checkpoint mechanism is "a NEW,
self-contained mechanism, distinct from the workspace's general day-frontier `PROGRESS.json`" — so this was never going
to auto-wire itself; it needed the explicit `lc_write_preemption_signal_file` call like the 3 launchers that already
have it (`launch-cefi-sharded-backfill.sh`, `launch-defi-backfill-vm.sh`, `launch-mtds-solana-defi-backfill-vm.sh`).

### Second finding while implementing: `STOP` vs `DELETE` termination-action mismatch

`launch-canonical-migration-vm.sh`'s SPOT provisioning uses `--instance-termination-action=STOP`
(`launch-canonical-migration-vm.sh:184`) — unlike the 3 already-working launchers, which use `DELETE`
(`launch-defi-backfill-vm.sh:133`: `--instance-termination-action=DELETE`). Since a `RelaunchPreemptedVm` replay reuses
the EXACT SAME VM name (`VM_NAME_OVERRIDE`, needed so the migration script's checkpoint blob path — keyed on `VM_NAME` —
stays reachable), a `STOP`'d (not deleted) instance would still occupy that name, and the relaunch's
`gcloud compute instances create` would fail with "already exists." No comment in the script explains why `STOP` was
chosen over `DELETE` here — looks like an oversight, not a deliberate choice, given every other SPOT launcher in this
codebase uses `DELETE`. Fixing this is a REQUIRED part of making the relaunch actually work, not optional polish.

### Third finding, from the operator's follow-up ask (open/resolved alert bookend)

Traced `RelaunchPreemptedVm.relaunch()` (`scripts/recovery/relaunch_backfill_vm.py:717-728`): on a successful relaunch
it calls `log_event(_EVENT_VM_PREEMPTED, severity="INFO", details={"relaunched": True, ...})` — but `log_event`
(`unified_trading_library/events/__init__.py:389`) is a **raw event-stream write** (GCS in batch mode, PubSub in live
mode), NOT the same path as `escalation.route_finding()`, which is what actually reaches the alerting-service Slack
channel. So today's "success" signal never becomes a visible Slack message at all, let alone a correlated "resolved"
bookend to the original `DP_VM_PREEMPTED` alert. This matches the workspace's own documented alerting convention ("every
actionable alert that paged an OPEN gets a ✅ CLOSE bookend in-channel") — this VM-preemption class doesn't have one
yet, for ANY launcher family, not just candle-migration.

## Plan

- [x] 1. ✅ [SCRIPT] P1. **`launch-canonical-migration-vm.sh`**: add `lc_write_preemption_signal_file` call — DONE,
      shipped `deployment-service@a32360a`.
- [x] 2. ✅ [SCRIPT] P1. **`launch-canonical-migration-vm.sh`**: add
      `--metadata-from-file="shutdown-script=${PREEMPTION_SIGNAL_FILE}"` to the `gcloud compute instances create` call —
      DONE.
- [x] 3. ✅ [SCRIPT] P1. **`launch-canonical-migration-vm.sh`**: change `--instance-termination-action=STOP` → `DELETE`
      — DONE.
- [x] 4. ✅ [SCRIPT] P1. Verified: `bash -n` clean, `test_spot_preemption_signal_coverage.py` +
      `test_vm_launcher_scripts.py` (79 tests) pass. **Important refinement found while verifying** — this fix is NOT
      redundant with the fleet-wide `setup-data-pipeline-vm.sh` systemd-service fix shipped 2026-07-20
      (`uts-preemption-signal.service`, installed via that script's own `log()`-based startup sequence). That systemd
      unit only becomes active once the startup script progresses far enough to install + `systemctl enable --now` it (a
      few hundred lines into a >1000-line script). `lc_write_preemption_signal_file`'s mechanism is DIFFERENT: it sets
      the NATIVE GCE `shutdown-script` instance metadata key at `gcloud compute instances create` time, which the
      base-image `google-guest-agent` (present from boot, not something `setup-data-pipeline-vm.sh` installs) picks up
      immediately — available from t=0, independent of how far the VM's own userspace startup has progressed. This
      exactly explains the measured TRADFI failure mode (18/20 shards preempted within 1-4 minutes of boot, likely
      BEFORE the custom systemd unit was ever installed) — the fleet-wide 2026-07-20 fix has a real early-preemption
      blind spot this fix closes for `canonical-migration-*`. Confirmed no shutdown-script metadata conflict:
      `setup-data-pipeline-vm.sh` uses a systemd unit, NOT the native GCE `shutdown-script` key, so both mechanisms
      coexist safely (the "gcloud only accepts ONE shutdown-script" caveat in `lc_write_preemption_signal_file`'s
      docstring refers to two callers of THAT helper colliding, not to this cross-mechanism case). Shipped via
      quickmerge — see commit below.
- [ ] 5. [DATA] P2. **New `DP_VM_PREEMPTED_RECOVERED` resolved-bookend event** — **REVISED, needs its own architecture
      trace before implementing** (do not blindly build this). Correction to the earlier plan: `route_finding()` is NOT
      a distinct delivery path from `log_event()` — it's a thin wrapper that runs the tier's extra action
      (auto_recover/file_issue/page_operator) and THEN calls the exact same `log_event(finding.event, ...)` at its own
      end (`escalation.py:841-844`). So `RelaunchPreemptedVm.relaunch()`'s existing success-path
      `log_event(_EVENT_VM_PREEMPTED,     ...)` call already reaches whatever `route_finding` reaches — routing through
      `route_finding` instead buys nothing (and would incorrectly re-trigger the auto_recover actuator dispatch /
      file_issue / orchestrator-dispatch side effects a "resolved" confirmation should NOT re-run). Two real open
      questions found, NEITHER yet confirmed: (a) **Dedup**: `alerting_service/core/dedup.py`'s key is
      `event_name:hash(identity_details)`, excluding only render-only fields (`message`/`summary`/`timestamp`/etc). The
      initial detection's `details` shape
      (`vm_name/asset_group/exit_code/captured_before/captured_after/umbrella/cloud/...`) differs structurally from the
      actuator's success-path `details` shape
      (`vm_name/vm_prefix/asset_group/recovery_action/relaunched/launcher/     relaunches_today/...`) — different key
      sets hash differently even under the SAME `event_name`, so they likely do NOT collapse into one dedup key. Reusing
      the same event name may not actually be the reason there's no visible resolved bookend. (b) **More fundamental,
      unconfirmed**: grepped `alerting-service` for `DP_VM_PREEMPTED` — ZERO matches, anywhere. Before designing a
      "resolved" event, need to confirm HOW (or WHETHER) `DP_VM_PREEMPTED` (or any `DP_*` event) actually reaches
      `alerting-service` at all today — `log_event()` writes to GCS (batch) or PubSub (live); is there a generic
      DP_*-prefix or severity-threshold catch-all subscriber in `alerting-service` (candidate: `error_event_handler.py`,
      unread), or does this whole VM-lifecycle alert family not reach Slack via `alerting-service` at all (a DIFFERENT
      channel/mechanism, e.g. a Cloud Monitoring log-based alert reading the same GCS/PubSub stream directly)? This
      determines whether item 5 is "add a resolved event" or "wire this event family to alerting-service for the first
      time, then add a resolved event." Scope this properly before building — it's a separate architecture question from
      the candle-migration work this issue started from.
- [ ] 6. [SCRIPT] P2. Unit tests for the new resolved-bookend path (mirror `test_dp_recovery_actuators.py`'s existing
      coverage style) — a dry-run relaunch, a real SUCCEEDED relaunch, and a FAILED relaunch (which must NOT emit a
      resolved bookend, only the existing `DP_VM_PREEMPTED_NO_RELAUNCH`).
- [ ] 7. [SCRIPT] P2. Quality gates + quickmerge for items 5-6 (deployment-service, possibly unified-trading-library if
      the event needs a UTL registry constant like `DP_VM_EXIT_NONZERO`'s).
- [ ] 8. [DATA] P2. **Scope the broader "all backfills and migration VMs" rollout**: enumerate the ~74 launchers already
      registered in `launcher_registry.py`, filter to genuinely SPOT-provisioned backfill/migration categories
      (excluding live/forward-poll/cron, which correctly stay on-demand per the HARD RULE — preemption would lose live
      data), cross-reference against which of those already call `lc_write_preemption_signal_file` (confirmed today:
      only 3 — `launch-cefi-sharded-backfill.sh`, `launch-defi-backfill-vm.sh`,
      `launch-mtds-solana-defi-backfill-vm.sh`). Report the exact resulting list before touching more files — likely
      several dozen, not a quick pass. **Independent corroboration (2026-07-23, different session)**:
      `launch-mtds-dex-swaps-backfill-vm.sh` is ALSO confirmed missing this wiring (grepped directly, zero matches for
      `exit_code_fleet_monitor`/`auto_recover`/ `PREEMPTED` in that file) — this is the
      `lst_rate_honest_coverage_2026_07_21.md` Phase 5 #2 backfill VM, which preempted 4 times in one session (manually
      caught + relaunched each time, no auto-recovery fired). Confirms this is a real, general gap affecting multiple
      independent launchers, not isolated to the canonical-migration one this doc was originally filed against.
- [ ] 9. [SCRIPT] P3. Apply the same 2-3 line pattern (`lc_write_preemption_signal_file` call + `--metadata-from-file`
      flag + verify `--instance-termination-action=DELETE`) to every launcher item 8 identifies as missing it. Batch by
      quality-gate sweep per the workspace's QG-sweep-batching convention, not one commit per file.

## Codex SSOTs

- `codex/05-infrastructure/spot-vms-for-backfill.md` — preemption-resume-from-PROGRESS HARD RULE.
- `codex/04-architecture/agent-orchestrator-alerting.md` — open/resolved bookend convention (AO alerts channel; this
  issue extends the same philosophy to the DP-monitor alerting path, which doesn't currently have it).

## Why this matters beyond the current migration

TRADFI's shards run ~2+ hours each (content-repair-heavy), giving each SPOT VM a much longer preemption-exposure window
than the DEFI/PREDICTION/CEFI legs (~35-45min shards) — and this session already measured a SECOND, worse
capacity-contention burst (18/20, vs CEFI's earlier 1/10 then 3/10) in the same zone within the same few hours. This is
not a one-off; any future large SPOT fleet in this zone is exposed to the same silent-loss risk until items 1-4 ship,
and the broader rollout (items 8-9) closes it for every other backfill/migration category too.
