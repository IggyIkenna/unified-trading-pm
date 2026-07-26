---
doc_type: plan
title: Finalize — AO backlog id-collision alert + remediation UI
summary:
  Gated finalize for ao_backlog_collision_alert_and_remediation_ui_2026_07_26.md. Re-verify each todo's cited evidence,
  confirm the new panel/endpoint actually surface and fix a live-reproduced collision (not just unit fixtures), then
  archive the parent via the standard 6-step ritual.
status: complete
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, backlog, regen, id-collision, alerting, dashboard-ui, finalize]
related:
  [
    /plans/archive/2026_07/ao_backlog_collision_alert_and_remediation_ui_2026_07_26.md,
    /plans/archive/issues/backlog_regen_id_reuse_stale_status_2026_07_15.md,
    /plans/archive/2026_07/ao_backlog_regen_integrity_2026_07_20.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on: [ao_backlog_collision_alert_and_remediation_ui_2026_07_26]
gate_on_depends: true
source:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Finalize — AO backlog id-collision alert + remediation UI

## Todos

- [x] ✅ [BACKEND] P1. **DONE 2026-07-26 (slot-14).** Re-verified each parent todo's cited evidence independently from a
      fresh checkout (`agent-orchestrator` venv had never been set up in this slot — `uv sync` +
      `npm --prefix     dashboard install` first). All 4 cited SHAs (`b623c2a`, `948f395`, `ffd0ab0`, `914a825`) exist
      and are reachable from HEAD (`914a825`, the tip that shipped all 4); each commit's described symbol confirmed
      present in current code (`backlog_sibling_reset_guard_refused` activity-log call in `server/bootstrap.py`,
      `notify_backlog_sibling_reset_guard_refused` in `server/notifications/slack.py`, the
      `POST /api/backlog/{task_id}/remint-collision` route in `server/routes/backlog.py`, `BacklogIntegrityPanel`/
      `unresolvedBacklogCollisions` in `dashboard/src/`). `bash scripts/quality-gates.sh` green on HEAD: 1746 backend +
      137 dashboard tests (matching the parent's own final citations), including the exact 6 `backlogCollisions.test.ts`
      unit tests and both Playwright e2e specs cited by todo 4.
- [x] ✅ [BACKEND] P1. **DONE 2026-07-26 (slot-14).** Live end-to-end check against a real (not fixture) collision.
      Reproduced a fresh sibling-reset-guard collision via the REAL `sync_backlog_to_db` guard logic (not the existing
      e2e Playwright harness's hand-seeded `backlog_sibling_reset_guard_refused` activity row, and not the existing unit
      test's `MagicMock` session) — a throwaway script under a fully-isolated temp SQLite DB + temp `config.STATE_DIR`
      (dedup-state JSON also lives there) called the real guard twice against a real done+done_sha row, then the real
      `remint_backlog_collision` route function against the same DB. Confirmed: (a) the guard's own `logger.error` fires
      and Slack pages exactly once on tick 1, 0 new posts on an identical tick 2 (dedup correctly keyed); 2 real
      `ActivityRow`s persisted (the audit trail records every tick; the Slack page is what dedupes, not the activity log
      — a distinction this run surfaced); the original done+done_sha row byte-for-byte untouched throughout. (b) the
      dashboard panel path is covered by the already-passing `backlog-collision.spec.ts` Playwright spec (re-verified as
      part of this todo's QG run above — genuinely drives the live UI, not a mock). (c) the remint endpoint minted a
      fresh task_id, left the original row untouched, and correctly 404s once backlog.yaml no longer carries the
      original id (the post-remint reality). No production DB/backlog.yaml/plans corpus touched — everything ran under a
      throwaway tmp path with only the outbound Slack HTTP call mocked (no real webhook send). Scratch script discarded
      after the run (not promoted — its value was the one-time live verification, fully superseded in permanence by the
      existing unit + e2e test suite it exercised).
- [x] ✅ [REVIEW] P2. **DONE 2026-07-26 (slot-14).** Ran the standard 6-step archival ritual on the parent plan. No
      DEFERRED items to migrate (the one open follow-up — 2 pre-existing flaky Playwright specs — was already filed as
      its own tracked issue doc during todo 4). Added the 🟢 ARCHIVED banner + flipped `status: complete`.
      Codex-alignment check: `/codex/04-architecture/agent-orchestrator-alerting.md` was already current (todo 2's own
      worker had already added the `notify_backlog_sibling_reset_guard_refused` row);
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`'s "known sharp edge" section was STALE
      (still said "never dispatch until someone notices" — the exact gap this plan closes) — updated it to describe the
      shipped detection+remediation flow. Updated both real `related:` path references corpus-wide
      (`plans/active/issues/ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`, this finalize doc's own
      `related:`) to the new archived path; left the auto-regenerated `active_plan_inventory_dashboard_2026_07_24.md`
      table row alone (self-corrects on next regen) and the two bare-mention provenance citations (codex table cell,
      `depends_on`) as historical record, not broken links. Moved the parent via `git mv` to
      `plans/archive/2026_07/ao_backlog_collision_alert_and_remediation_ui_2026_07_26.md`. Cleared
      `locked_by`/`locked_since` (both carried the identical boilerplate `live-defi-rollout`/`2026-05-21` values found
      on this finalize doc too — a stale template default predating either plan's creation, not a real lock) — this
      todo's own text explicitly authorizes clearing it.
