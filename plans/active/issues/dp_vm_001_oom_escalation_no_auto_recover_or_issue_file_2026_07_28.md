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

- [x] ✅ [BACKEND] P0. If unwired: wire DP-VM-001 to auto-recover FIRST (resize-up relaunch via
      `relaunch_backfill_vm.py`, respecting the existing ≤2/(vm-prefix, day) cap) before paging, matching the pattern
      already used for DP-VM-003/ DP-VM-008. If already wired: fix `/codex/05-infrastructure/data-pipeline-alerts.md`'s
      DP-VM-001 escalation column (currently reads plain "page") to accurately reflect the real behavior — this doc is
      the operational SSOT other agents read to know what already exists, and it is currently wrong either way this
      resolves.

      **RESOLVED — already wired (per todo 1's evidence), so this fixed the doc, not the code.** Confirmed
                      independently (re-read the same code paths at current HEAD, not just trusted todo 1's claim): OOM subcase
                      (`exit_code==137`) → `EscalationTier.AUTO_RECOVER` → `_recover_backfill_vm` → `RelaunchBackfillVm.relaunch()`
                      (resize-up, ≤2/(vm-prefix, day) cap) — `exit_code_fleet_monitor.py:335` + `escalation.py:498-505,304-367`.
                      Non-OOM subcase → `EscalationTier.PAGE_OPERATOR` directly (no actuator attempted) —
                      `exit_code_fleet_monitor.py:335` — this half of the original doc text was already correct. Fixed
                      `/codex/05-infrastructure/data-pipeline-alerts.md:137`'s DP-VM-001 Escalation cell from plain `page` to
                      `OOM: auto-recover (resize-up relaunch) then file issue · non-OOM: page` — matches the sibling-row style
                      (DP-VM-003/DP-VM-008's "auto-recover (...) then file issue"). The "then file issue" half is accurate for BOTH
                      OOM outcomes: `escalation.py:846-862` files a quiet `_oom_investigate_finding` follow-up issue on a
                      *successful* resize-up relaunch (operator ask 2026-07-27 — a recurring OOM is worth a human look even once
                      self-healed), and falls through to `EscalationTier.FILE_ISSUE` (`escalation.py:818-841`) on a failed/
                      budget-exhausted relaunch. Did not touch `data-pipeline-alerts.registry.yaml` or UAC
                      `alerting/rules.py`'s `DataPipelineEscalation` enum (`PAGE_OPERATOR` there too) — that's a structurally
                      different, closed 3-value enum used for static severity/channel routing (not the per-finding dynamic dispatch
                      this doc describes) with no test enforcing byte-parity against this prose column
                      (`unified-api-contracts/tests/unit/test_data_pipeline_alert_rules.py` only checks well-formedness/severity, not
                      escalation-text match) — out of scope for this todo, not a regression it introduces. —
                      unified-trading-pm (this commit)

- [x] ✅ [BACKEND] P0. Ensure DP-VM-001/OOM ALWAYS files a `plans/active/issues/<slug>_<date>.md` for deeper
      investigation regardless of whether the auto-recover/resize-up succeeds — an OOM recurring on a resized machine is
      itself a signal worth a human eventually looking at the root cause (a genuine memory leak vs. a workload that
      outgrew its shard size), even if the immediate symptom self-heals. Definition of done: an OOM event produces both
      a resize-up relaunch attempt AND a filed issue, verified via a real triggered/simulated OOM on a test VM, not just
      code review.

      **VERIFIED — the code (`escalation.py`, per todo 2's evidence) already always files an issue; this closes the
          gap by proving it, not by changing behavior.** Read every failure/success branch of the OOM auto-recover chain
          and confirmed there is no path where a real classified `exit_code=137` termination produces neither a relaunch
          attempt nor a filed issue. Added 3 new tests driving the REAL entry point
          (`exit_code_fleet_monitor.classify_terminated_vm` → `_finding_for` → `escalation.route_finding`, not a
          hand-built finding — the "simulated real OOM trigger" the todo asks for) — a mocked GCE actuator stands in for
          the actual `gcloud`/subprocess call (no live VM available to a background worker; the actuator boundary is the
          correct/only sanctioned mock point per the existing `test_oom_relaunch_passes_bigger_machine_env` pattern):
          1. `test_oom_finding_always_files_issue_when_relaunch_succeeds` — resize-up relaunch SUCCEEDS → asserts the
             actuator was actually invoked (`relaunch_calls`) AND a `plans/active/issues/*.md` doc was written
             (`oom_investigate_issue_path`, "investigate OOM root cause" body).
          2. `test_oom_finding_always_files_issue_when_no_launcher_binding` — no resolvable `relaunch_launcher` → cannot
             relaunch → still falls through to `file_issue`, doc written.
          3. `test_oom_finding_always_files_issue_when_relaunch_budget_exhausted` — actuator runs but reports it could not
             recover (the ≤2/(vm-prefix, day) cap spent) → still falls through to `file_issue`, doc written.

          All 3 new + the pre-existing 212 tests in the module pass:
          `.venv/bin/python -m pytest tests/unit/test_data_pipeline_monitors.py -q` → `215 passed`. Full
          `bash scripts/quality-gates.sh` green (152s), sentinel `072ec9091f62d331a42c584a788c4756c8ef92ba`. —
          deployment-service@2b6ad53

- [ ] [REVIEW] P1. Once the above lands, add one line to CLAUDE.md's "Launching VMs / infra?" domain-index pointing to
      `data-pipeline-alerts.md` as the SSOT for VM/monitoring-tool escalation design, so future agents building new
      monitoring wire into this taxonomy (auto-recover-before-page, file-issue-for-investigation-worthy classes) instead
      of inventing an ad hoc pattern.
