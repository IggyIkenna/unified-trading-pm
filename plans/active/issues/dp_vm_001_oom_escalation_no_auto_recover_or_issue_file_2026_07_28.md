---
doc_type: issue
title:
  DP-VM-001 (OOM/nonzero-exit) escalates straight to page — contradicts the self-heal actuator table in the same doc
summary:
  Operator asked (2026-07-28) to confirm VM/job monitoring (incl. manifest consolidator) has full auto-recovery on death
  including OOM, automated rescale-on-OOM, and an issue auto-filed for investigation. Reading
  codex/05-infrastructure/data-pipeline-alerts.md found a real self-contradiction — the DP-VM taxonomy table lists
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

- [ ] [BACKEND] P0. In `deployment-service`, determine ground truth: does
      `deployment_service.data_pipeline_monitors.escalation._DP_RECOVERY_ACTIONS` actually wire
      `DP_VM_EXIT_NONZERO`/DP-VM-001 to `relaunch_backfill_vm.py`'s resize-up-on-OOM actuator today, or is that mapping
      aspirational/unwired? Verify by reading the live escalation dispatch code, not by re-reading the docs. Definition
      of done: a stated, evidence-backed answer (cite the actual code path) — not an assumption.
- [ ] [BACKEND] P0. If unwired: wire DP-VM-001 to auto-recover FIRST (resize-up relaunch via `relaunch_backfill_vm.py`,
      respecting the existing ≤2/(vm-prefix, day) cap) before paging, matching the pattern already used for DP-VM-003/
      DP-VM-008. If already wired: fix `codex/05-infrastructure/data-pipeline-alerts.md`'s DP-VM-001 escalation column
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
