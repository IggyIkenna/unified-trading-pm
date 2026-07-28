---
doc_type: issue
title:
  DP-VM-001 (OOM/nonzero-exit) escalates straight to page — contradicts the self-heal actuator table in the same doc
summary:
  Operator asked (2026-07-28) to confirm VM/job monitoring (incl. manifest consolidator) has full auto-recovery on death
  including OOM, automated rescale-on-OOM, and an issue auto-filed for investigation. Reading
  /codex/05-infrastructure/data-pipeline-alerts.md found a real self-contradiction — the DP-VM taxonomy table lists
  DP-VM-001 ("VM run.log terminal exit_code != 0, incl. 137 OOM") escalation as plain "page" — no auto-recover, no
  file-issue — while the SAME doc's "Self-heal actuator layer" table separately lists an actuator for
  `DP_VM_EXIT_NONZERO (137 OOM)` → `relaunch_backfill_vm.py (resize-up on OOM)`, capped at ≤2/(vm-prefix, day). Two
  sibling event classes (DP-VM-003 stall, DP-VM-008 ambiguous-kill) DO combine auto-recover + file-issue in their
  escalation column — DP-VM-001 is the one VM-death class that, as documented, does neither. Unclear whether the
  actuator table describes a shipped-but-undocumented mechanism or an aspirational one never wired to DP-VM-001's real
  escalation path.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [monitoring, alerting, oom, vm-lifecycle, self-heal, escalation]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: "2026-07-28"
parent_epic: infrastructure_master
source:
  Operator request 2026-07-28 to verify VM/monitoring auto-recovery + OOM handling is fully wired; found via direct read
  of data-pipeline-alerts.md, not assumed.
execution_scope: orchestrator-agent
assigned_vm: planning
priority: P0
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# DP-VM-001 (OOM/nonzero-exit) escalates straight to page

## Todos

- [x] ✅ [BACKEND] P0. In `deployment-service`, determine ground truth: does
      `deployment_service.data_pipeline_monitors.escalation._DP_RECOVERY_ACTIONS` actually wire
      `DP_VM_EXIT_NONZERO`/DP-VM-001 to `relaunch_backfill_vm.py`'s resize-up-on-OOM actuator today, or is that mapping
      aspirational/unwired? Verify by reading the live escalation dispatch code, not by re-reading the docs. Definition
      of done: a stated, evidence-backed answer (cite the actual code path) — not an assumption. — deployment-service
      (no code change; investigation only)

      **ANSWER: it is WIRED and live, NOT aspirational — for the OOM subcase.** Evidence chain (all read at
          `deployment-service` HEAD 2026-07-28, plus a live test run):
          1. The finding is constructed with `tier=EscalationTier.AUTO_RECOVER if oom else EscalationTier.PAGE_OPERATOR`
             for `registry_id="DP-VM-001"` / `event=DP_VM_EXIT_NONZERO`
             (`deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py:332-339`, `oom` = `exit_code==137`).
          2. `escalation.py`'s `_DP_RECOVERY_ACTIONS` dict (`escalation.py:498-505`) DOES map
             `_EVENT_VM_EXIT_NONZERO` (`"DP_VM_EXIT_NONZERO"`) → `_recover_backfill_vm`.
          3. `_recover_backfill_vm` (`escalation.py:305-367`) calls `RelaunchBackfillVm.relaunch()`
             (`scripts/recovery/relaunch_backfill_vm.py:144-238`), which gates on `exit_code == 137`, applies the
             `_MAX_RELAUNCHES_PER_DAY = 2` per-(vm-prefix, day) budget (falling to `status=PAGE` once exhausted), and — via
             `escalation._escalated_machine_type` consuming the `launch_budget_registry.MEMORY_TIER_LADDER` — passes a
             bigger `MACHINE_TYPE` env so the relaunch actually resizes up rather than re-OOMing on the same machine.
          4. Confirmed LIVE, not just read: `tests/unit/test_data_pipeline_monitors.py::test_oom_relaunch_passes_bigger_machine_env`
             passes today (`.venv/bin/python -m pytest tests/unit/test_data_pipeline_monitors.py -k test_oom_relaunch_passes_bigger_machine_env` →
             `1 passed`), exercising `escalation._recover_backfill_vm` end-to-end and asserting the escalated machine type.
          5. **The non-OOM subcase of DP-VM-001 genuinely IS plain `page`** (`exit_code_fleet_monitor.py:335` — non-OOM →
             `PAGE_OPERATOR` directly, no actuator attempted) — a non-OOM crash has no deterministic auto-fix, so this half
             of the doc's claim is correct.
          6. **The doc is what's wrong, not the code.** `/codex/05-infrastructure/data-pipeline-alerts.md:137`'s DP-VM-001
             escalation column reads plain `page` with no auto-recover/file-issue callout, which is accurate ONLY for the
             non-OOM subcase — it fails to disclose that the OOM subcase (the common case in practice, and the one the
             same doc's own actuator table at line 209 describes) auto-recovers first. This resolves the "If already
             wired" branch of todo 2 below: fix the doc, don't touch the code.

- [ ] [BACKEND] P0. If unwired: wire DP-VM-001 to auto-recover FIRST (resize-up relaunch via `relaunch_backfill_vm.py`,
      respecting the existing ≤2/(vm-prefix, day) cap) before paging, matching the pattern already used for DP-VM-003/
      DP-VM-008. If already wired: fix `/codex/05-infrastructure/data-pipeline-alerts.md`'s DP-VM-001 escalation column
      (currently reads plain "page") to accurately reflect the real behavior — this doc is the operational SSOT other
      agents read to know what already exists, and it is currently wrong either way this resolves.
- [ ] [BACKEND] P0. Ensure DP-VM-001/OOM ALWAYS files a `plans/active/issues/<slug>_<date>.md` for deeper investigation
      regardless of whether the auto-recover/resize-up succeeds — an OOM recurring on a resized machine is itself a
      signal worth a human eventually looking at the root cause (a genuine memory leak vs. a workload that outgrew its
      shard size), even if the immediate symptom self-heals. Definition of done: an OOM event produces both a resize-up
      relaunch attempt AND a filed issue, verified via a real triggered/simulated OOM on a test VM, not just code
      review.
- [ ] [REVIEW] P1. Once the above lands, add one line to CLAUDE.md's "Launching VMs / infra?" domain-index pointing to
      `data-pipeline-alerts.md` as the SSOT for VM/monitoring-tool escalation design, so future agents building new
      monitoring wire into this taxonomy (auto-recover-before-page, file-issue-for-investigation-worthy classes) instead
      of inventing an ad hoc pattern.
