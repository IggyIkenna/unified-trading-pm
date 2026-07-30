---
doc_type: issue
title: VM fleet SPOT-preemption auto-recovery gap — canonical-migration VMs + open/resolved alert bookend
summary:
  canonical-migration-* launcher never wrote the PREEMPTED signal blob despite being fully registered in the fleet
  relaunch actuator, so 18/20 SPOT TRADFI shards preempted silently with zero auto-recovery; fixing that launcher,
  adding a resolved-bookend alert, and scoping the broader backfill/migration launcher rollout.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-library]
scope: [engineer]
tags: [spot-preemption, auto-recovery, alerting, candle-migration]
related: [/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md]
created: 2026-07-23
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
source: operator-directed, discovered live during the P7 candle-canonical-path migration
resolved_by:
  "All 9 todos done. 1-7: canonical-migration-* launcher fix + STOP->DELETE + DP_VM_PREEMPTED_RECOVERED resolved-bookend
  event (unified-api-contracts@d3739c57, deployment-service@a32360a/dd7b62e). 8: scoped the broader rollout to 8
  evidence-driven launchers. 9: applied the preemption-signal pattern to all 8, SHIPPED deployment-service@db5d3c7
  (2026-07-30) — first quickmerge attempt was correctly refused by a pre-existing, unrelated sports_trigger_scheduler.py
  945L>930L cap violation (fixed by another slot, deployment-service@5976da7), second attempt landed clean."
last_updated: "2026-07-30"
locked_by:
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-07-30** — status=resolved, all 9 todos done + genuinely shipped (deployment-service@db5d3c7), 0
> open todos, moved to `/plans/archive/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md`. Archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule. (Note: this doc was briefly and
> incorrectly archived earlier the same day before the code had actually landed — reverted, then re-archived once
> `deployment-service@db5d3c7` genuinely shipped; see Progress Log.)

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
      quickmerge as part of items 1-3's commit — see `deployment-service@a32360a` above.
- [x] 5. ✅ [DATA] P2. **New `DP_VM_PREEMPTED_RECOVERED` resolved-bookend event** — architecture-traced, THEN built.
      `unified-api-contracts@d3739c57` + `deployment-service@dd7b62e`. **Open question (b) resolved — bigger scope than
      either original guess**: confirmed via code read (NOT grep-0, grep-then-READ) that `DP_VM_PREEMPTED` was emitted
      via `log_event()`, correctly reached alerting-service's `lifecycle-events-sub` subscription, and hit
      `route_event()` — but `route_event()`'s DP_* short-circuit (`data_pipeline_rule_for(event_name)`) does an
      EXACT-MATCH lookup against UAC `DATA_PIPELINE_ALERT_RULES`, and `DP_VM_PREEMPTED` was **not in that registry at
      all**. Root cause: a yaml/python transcription-drift bug (same class as the 2026-07-27 `DP_FLEET_MONITOR_RUN_*`
      regression covered by `test_dp_fleet_monitor_lifecycle_events_registered`) — the human-SSOT yaml
      (`codex/05-infrastructure/data-pipeline-alerts.registry.yaml`) already reserved `DP-VM-007=DP_VM_PREEMPTED` /
      `DP-VM-008=DP_VM_PARTIAL_UNCONFIRMED`, but the Python UAC tuple never transcribed them — `DP-VM-007` was
      independently squatted by `DP_CLOUD_RUN_STALE_IMAGE` (added directly to Python, never added to the yaml), and
      `exit_code_fleet_monitor.py` kept emitting `PipelineFinding(..., registry_id="DP-VM-007"/"DP-VM-008")` pointing at
      IDs that (in Python) either meant something else or didn't exist. `DP_VM_PREEMPTED_NO_RELAUNCH` (the CRITICAL
      "silent vanish" page — the entire point of this issue) was **never registered anywhere, yaml or Python**. Net
      effect: all three events fell through to alerting-service's generic catch-all `_match_routing_rules` (matched
      against `LIVE_ALERT_RULES`, a closed `AlertCode` set that structurally excludes `DP_*` names) — a total miss there
      falls back to `{"slack"}, None` (`#uts-live-alerts`, unformatted, **no PagerDuty severity**), so the CRITICAL
      no-relaunch page was not actually paging via the incident path as its own docstring claimed. This — not the dedup
      question — is why there was no visible resolved bookend: the OPEN alert itself wasn't reaching
      `#data-pipeline-alerts`. **Open question (a) (dedup) is moot given (b)**: since the fix adds a NEW,
      distinctly-named event (`DP_VM_PREEMPTED_RECOVERED`) rather than reusing `DP_VM_PREEMPTED` for the success path,
      the dedup key (`event_name:hash(identity_details)`) can never collide with the open alert's key regardless of
      details-shape — open/resolved are visibly distinct Slack lines correlated by `vm_name`/`asset_group` in both (no
      alerting-service threading exists to do this automatically — webhook-only, per the AO-alerts bookend convention).
      **Shipped**: registered `DP-VM-008=DP_VM_PREEMPTED` (INFO/auto_recover), `DP-VM-009=DP_VM_PREEMPTED_NO_RELAUNCH`
      (CRITICAL/page_operator), `DP-VM-010=DP_VM_PARTIAL_UNCONFIRMED` (WARN/auto_recover, renumbered off the
      DP_CLOUD_RUN_STALE_IMAGE collision), `DP-VM-011=DP_VM_PREEMPTED_RECOVERED` (INFO/file_issue, the new
      resolved-bookend — `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py`);
      corrected + backfilled the yaml SSOT to match (added the missing `DP_CLOUD_RUN_STALE_IMAGE` entry at `DP-VM-007`,
      renumbered `DP_VM_PREEMPTED`→008 / `DP_VM_PARTIAL_UNCONFIRMED`→010, added `DP_VM_PREEMPTED_NO_RELAUNCH`→009 and
      `DP_VM_PREEMPTED_RECOVERED`→011 —
      `unified-trading-pm/codex/05-infrastructure/data-pipeline-alerts.registry.yaml`); fixed the now-stale hardcoded
      `registry_id` literals + docstring/log-line id references in `exit_code_fleet_monitor.py` + `escalation.py`;
      switched `RelaunchPreemptedVm.relaunch()`'s success-path `log_event()` call from `DP_VM_PREEMPTED` to the new
      `DP_VM_PREEMPTED_RECOVERED` (`relaunch_backfill_vm.py`) — the checkpoint-resume mid-flight `log_event` (a
      DIFFERENT call site, "resuming from checkpoint", not a completion claim) intentionally still emits
      `DP_VM_PREEMPTED`. **Not fixed / left as a documented, out-of-scope loose end**:
      `heartbeat_sidecar_reliability.py`/`heartbeat_sidecar_reliability_cli.py` also self-label `DP-VM-008` in their
      module docstrings, but that module never emits a `DP_*` finding with that `registry_id` (grepped — zero
      `registry_id=` occurrences), so it's a harmless doc-label collision with no routing/test impact, not a repeat of
      the registry-drift bug above; flagging here rather than silently leaving it for whoever next greps `DP-VM-008`. A
      more general "does the yaml/python parity `_dp_rule` comment's claimed 'closed-set sanity test' actually exist"
      gap (it does not — I found the collision by hand cross-check, not a failing test) is a separate, larger follow-up
      not in this issue's scope; not filing a new issue doc for it solo (would duplicate this doc's own evidence) —
      noting it here for whoever next touches `DATA_PIPELINE_ALERT_RULES`.
- [x] 6. ✅ [SCRIPT] P2. Unit tests for the new resolved-bookend path (mirror `test_dp_recovery_actuators.py`'s existing
      coverage style) — `test_preempted_relaunch_replays_captured_launch_env` (SUCCEEDED) now asserts
      `DP_VM_PREEMPTED_RECOVERED` instead of the old `DP_VM_PREEMPTED` reuse;
      `test_preempted_relaunch_dry_run_does_not_execute` now asserts zero events emitted;
      `test_preempted_relaunch_guard_refusal_emits_critical_no_relaunch` (FAILED) now additionally asserts
      `DP_VM_PREEMPTED_RECOVERED` is NEVER emitted alongside the CRITICAL no-relaunch alert. Plus new UAC
      `test_data_pipeline_alert_rules.py` coverage (existing `test_registry_ids_and_events_are_unique` +
      `test_critical_rules_page_via_telegram_and_pagerduty` generically cover the 4 new entries — no new test functions
      needed there, the closed-set assertions already exercise them).
- [x] 7. ✅ [SCRIPT] P2. Quality gates + quickmerge for items 5-6 — unified-api-contracts (registry) +
      deployment-service (emission + tests); no unified-trading-library change needed
      (`DP_VM_PREEMPTED`/`_NO_RELAUNCH`/`_RECOVERED` deliberately stay local string constants, not UTL-exported — see
      the updated code comments; that's a SEPARATE axis from UAC alert-routing registration, per the existing
      `DP_VM_EXIT_NONZERO`-vs-`DP_VM_PREEMPTED` precedent in the same files). Both repos' full `quality-gates.sh` PASSED
      and landed on `live-defi-rollout`: `unified-api-contracts@d3739c57`, `deployment-service@dd7b62e`.
- [x] 8. ✅ [DATA] P2. **Scope the broader "all backfills and migration VMs" rollout — REVISED after checking real
      coverage, not just direct-call grep**: my original framing ("only 3 of ~74 launchers call
      `lc_write_preemption_signal_file`, so ~dozens are uncovered") was misleading. Re-checked: **125 of 158**
      `launch-*.sh` scripts already reference `setup-data-pipeline-vm.sh` (the shared boot seam that ITSELF installs the
      `uts-preemption-signal.service` systemd unit fleet-wide, per the 2026-07-20 fix — confirmed via
      `test_spot_preemption_signal_coverage.py`'s `test_every_spot_launcher_can_emit_the_preemption_signal`, which
      already PASSED with 0 failures before my change today). So most launchers DO have baseline coverage — this is NOT
      a "close a total absence" sweep.

      **But the early-preemption blind spot this doc's fix closes (native GCE shutdown-script, available from t=0, vs
                                                                                                                                                                                          the shared seam's systemd unit which only activates once `setup-data-pipeline-vm.sh` progresses far enough to
                                                                                                                                                                                          install it) is REAL and independently corroborated**: `launch-mtds-dex-swaps-backfill-vm.sh` — confirmed via
                                                                                                                                                                                          direct grep to ALSO use the shared seam AND be registered in `launcher_registry.py` (so it SHOULD have had
                                                                                                                                                                                          coverage) — preempted 4 times in one session
                                                                                                                                                                                          (`lst_rate_honest_coverage_2026_07_21.md` Phase 5 #2) with zero auto-recovery firing (a different session,
                                                                                                                                                                                          independently caught + manually relaunched each time). This is consistent with the SAME early-preemption
                                                                                                                                                                                          pattern measured on TRADFI (18/20 shards preempted within 1-4 minutes of boot), not a separate coverage gap —
                                                                                                                                                                                          strengthening, not weakening, the case for rolling out the native-shutdown-script defense-in-depth more broadly.

                                                                                                                                                                                          **Revised scoping question for item 9**: not "which launchers lack ANY coverage" (few, if any, genuinely do —
                                                                                                                                                                                          confirm with the passing test), but "which launchers run large concurrent SPOT fleets (more zone-contention
                                                                                                                                                                                          exposure, matching TRADFI's failure mode) or have a long `setup-data-pipeline-vm.sh` staging chain before their
                                                                                                                                                                                          task-specific work starts (wider blind-spot window)" — a smaller, evidence-driven list, not a blanket 100+-file
                                                                                                                                                                                          sweep. Candidates already identified: `launch-mtds-dex-swaps-backfill-vm.sh` (proven hit), any `*-sharded-*`/
                                                                                                                                                                                          `SHARD_OF`-fan-out launcher (same concurrency profile as candle-apply), and the two Phase-D pipeline-check
                                                                                                                                                                                          launcher name patterns `mtds-backfill-*-pipelinecheck-*` and `instr-backfill-*-pipelinecheck-*` (registered in
                                                                                                                                                                                          the fleet relaunch machinery by launcher-prefix match but never previously named as candidates here; exhibited
                                                                                                                                                                                          the same early-boot `vm_self_deleted_no_exit_status` preemption pattern repeatedly on single-shard smoke-test
                                                                                                                                                                                          VMs during the TradFi Phase-D terminal-gate work — see `tradfi_phase_d_terminal_gate_2026_07_24.md`).

                      **Final candidate list (enumerated 2026-07-30, not just categories) — every `launch-*.sh` matching the revised
                      criteria (SHARD_OF/SHARD_INDEX/NUM_SHARDS fan-out var, `-sharded-` filename, or a Phase-D `*-pipelinecheck-*`
                      VM-name pattern), cross-checked for `lc_write_preemption_signal_file` absence AND actual
                      `--provisioning-model=SPOT` use (grep-then-READ, not grep-0-and-conclude):**

                      1. `launch-mtds-dex-swaps-backfill-vm.sh` — proven hit (4 preemptions, `lst_rate_honest_coverage_2026_07_21.md`).
                      2. `launch-mtds-dex-pools-backfill-vm.sh` — same SHARD_INDEX-fan-out family as #1, same exposure.
                      3. `launch-features-sharded-backfill.sh` — `-sharded-` filename fan-out.
                      4. `launch-mdps-sharded-backfill.sh` — `-sharded-` filename fan-out.
                      5. `launch-tradfi-is-defs-sharded.sh` — `-sharded-` filename fan-out.
                      6. `launch-instruments-backfill-vm.sh` — emits the `instr-backfill-*-pipelinecheck-*` VM names named above.
                      7. `launch-mtds-backfill-vm.sh` — emits the `mtds-backfill-*-pipelinecheck-*` VM names named above.
                      8. `launch-mdps-backfill-vm.sh` — its own driver names `mdps-backfill-<cat>-pipelinecheck-<ts>`, same pattern.

                      All 8 confirmed via direct grep: `provisioning-model=SPOT` present (genuinely preemption-exposed) AND
                      `lc_write_preemption_signal_file` absent (zero calls) AND already `--instance-termination-action=DELETE` (so none
                      of them need item 3's STOP→DELETE fix — only the signal-file + metadata-flag pair from items 1-2).

                      **Two launchers matched the filename/category sweep but are correctly OUT of scope, not silently dropped:**
                      - `launch-cefi-sharded-backfill-aws.sh` — an AWS EC2 launcher (`source lib/aws_ec2_launch_lib.sh`, `aws ec2`/`aws
                        s3` calls, no `gcloud`). `lc_write_preemption_signal_file` sets a native **GCE** `shutdown-script` instance
                        metadata key — that mechanism does not exist on AWS. Fixing AWS spot-interruption detection would need EC2's own
                        instance-metadata-service `/spot/instance-action` poll, a genuinely different implementation, not this
                        2-3-line pattern. Out of this issue's scope; flag as a separate follow-up only if this launcher shows the same
                        silent-loss symptom in the field.
                      - `launch-legacy-bucket-migration-sharded.sh` — grepped for `provisioning-model=SPOT`: zero matches: this
                        launcher is on-demand, not SPOT, so it is not preemption-exposed at all (nothing to fix here). Also
                        `Lifecycle: oneoff` / `Delete-when: after prod-run verified + GCS orphan-sweep=0` — a temporary migration
                        script slated for deletion, not a standing fleet member.

- [ ] 9. [SCRIPT] P3. Apply the same 2-3 line pattern (`lc_write_preemption_signal_file` call + `--metadata-from-file`
      flag; `--instance-termination-action` already `DELETE` on all 8, so that sub-step is a no-op verify only) to the 8
      launchers item 8 enumerated above (`launch-mtds-dex-swaps-backfill-vm.sh`, `launch-mtds-dex-pools-backfill-vm.sh`,
      `launch-features-sharded-backfill.sh`, `launch-mdps-sharded-backfill.sh`, `launch-tradfi-is-defs-sharded.sh`,
      `launch-instruments-backfill-vm.sh`, `launch-mtds-backfill-vm.sh`, `launch-mdps-backfill-vm.sh`) — not a blind
      sweep of all 158, and not the two out-of-scope launchers above. Batch by quality-gate sweep per the workspace's
      QG-sweep-batching convention, not one commit per file. **DONE 2026-07-30 — `deployment-service@db5d3c7`.** All 8
      launchers now call `lc_write_preemption_signal_file` immediately before their `gcloud compute instances create`
      call and pass `--metadata-from-file="shutdown-script=${PREEMPTION_SIGNAL_FILE}"`;
      `--instance-termination-action=DELETE` confirmed already present on all 8 (verify-only, no change needed).
      `launch-tradfi-is-defs-sharded.sh` was the one launcher of the 8 that didn't even source `lib/launcher_common.sh`
      yet — added the source line. `bash -n` clean on all 8, full test suite green (2968 passed) via
      `bash scripts/quality-gates.sh` at Pass-1. First `quickmerge.sh` attempt correctly REFUSED on a pre-existing,
      unrelated hard-cap violation (`deployment_service/sports_trigger_scheduler.py: 945L > 930L`, untouched by this
      change) — another slot fixed it independently (`deployment-service@5976da7`, split into
      `sports_trigger_evaluation.py`) while this was pending; pulled that fix in and re-ran quickmerge, which landed
      clean.

## Codex SSOTs

- `/codex/05-infrastructure/spot-vms-for-backfill.md` — preemption-resume-from-PROGRESS HARD RULE.
- `/codex/04-architecture/agent-orchestrator-alerting.md` — open/resolved bookend convention (AO alerts channel; this
  issue extends the same philosophy to the DP-monitor alerting path, which doesn't currently have it).

## Why this matters beyond the current migration

TRADFI's shards run ~2+ hours each (content-repair-heavy), giving each SPOT VM a much longer preemption-exposure window
than the DEFI/PREDICTION/CEFI legs (~35-45min shards) — and this session already measured a SECOND, worse
capacity-contention burst (18/20, vs CEFI's earlier 1/10 then 3/10) in the same zone within the same few hours. This is
not a one-off; any future large SPOT fleet in this zone is exposed to the same silent-loss risk until items 1-4 ship,
and the broader rollout (items 8-9) closes it for every other backfill/migration category too.

## Corroborating observation (2026-07-23, concurrent session) — the STOP→DELETE flip observed live, plus a gap for the new `defi-rebuild`/`defi-pi-range` categories

Running the DeFi manifest-rebuild leg of `defi_consolidated_closeout_2026_07_18.md` on this SAME
`launch-canonical-migration-vm.sh` (via two new categories, `defi-rebuild`/`defi-pi-range`, added earlier this session
from a stashed foreign-WIP merge — `deployment-service@065cf70`) independently reproduced exactly the item-3 fix
mid-flight:

- **VM #1** (`canonical-migration-defi-rebuild-20260722-193748`, launched before `a32360a` landed): SPOT-preempted, left
  `TERMINATED` (a `stop` operation) — inspectable after the fact, resumed manually from its last-logged date.
- **VM #2** (`canonical-migration-defi-rebuild-20260722-194751`, launched after `a32360a` had propagated into this
  session's local `deployment-service` checkout via an unrelated `git pull`): preempted again, but this time fully
  **deleted** (a `delete` operation by the compute default service account, confirmed via
  `gcloud compute operations describe`) — no `EXIT_STATUS`, no graceful shutdown log lines, the instance simply
  vanished. Only the `operations list` audit trail revealed what happened; without it this would have looked like an
  unexplained disappearance rather than a preemption.

This is independent field confirmation that item 3's `DELETE` change is real and already active, and that it changes the
FORENSICS available after a preemption (a `STOP`'d instance survives for inspection; a `DELETE`'d one does not,
audit-trail-only). Not itself a problem — `DELETE` is required for `RelaunchPreemptedVm` to reuse the VM name — but
worth noting for anyone diagnosing a "VM vanished, no error" case going forward: check
`gcloud compute operations list --filter="targetLink~<vm>"` before assuming something is wrong.

**A gap this issue's scoping (items 8-9) doesn't yet cover**: the two new `defi-rebuild`/`defi-pi-range` categories have
no `PROGRESS.json`-style checkpoint (confirmed — `gsutil stat` on the expected path 404s), unlike the
`defi-per-instrument` category's year-chunked resume. So while the preemption-signal fix now lets the fleet's
auto-recovery correctly _detect_ a preempted `defi-rebuild`/`defi-pi-range` VM, a `RelaunchPreemptedVm` replay would
still restart from the ORIGINAL launch's `--start-date`, not the actual last-scanned date — safe (idempotent, manifest
writer is upsert-safe) but wasteful for a multi-day rebuild. Not fixed here; flagging as a known residual gap for
whoever picks up items 8-9, since these two categories didn't exist yet when this issue was first scoped.

## Progress Log

- **2026-07-30 (plans-corpus reduction marathon, wave 3)** — Closed todo 9. First archival attempt was premature (code
  written+verified locally but not yet shipped) — reverted per evidence-backed-completion discipline once the quickmerge
  re-gate genuinely refused (pre-existing `sports_trigger_scheduler.py` size-cap violation). Once another slot
  independently fixed that unrelated blocker (`deployment-service@5976da7`), pulled it in and re-ran quickmerge: landed
  clean as `deployment-service@db5d3c7`. All 9 todos now genuinely done — archiving.
