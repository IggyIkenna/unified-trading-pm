---
doc_type: plan
title: AO fleet throughput incident — finalize
summary: >-
  Gated closeout for ao_fleet_throughput_incident_2026_07_25.md — machine-held via depends_on + gate_on_depends: true
  until all 3 of that plan's todos are done. Re-verifies each done-claim's cited evidence still resolves, checks whether
  todo 2's dormant-slot finding changes anything about the companion ao_worker_context_lifecycle_gap_2026_07_25.md plan
  (a fixed AutoSpawn cap/backoff could change how many slots are ever candidates for the context-gate logic that plan
  ships), and runs the standard archival ritual.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [orchestrator, autospawn, incident, close-out]
related: [/plans/active/ao_fleet_throughput_incident_2026_07_25.md, /plans/epics/orchestrator_master.md]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_fleet_throughput_incident_2026_07_25]
gate_on_depends: true
source: >-
  Operator ruling 2026-07-24 (task_template.md §4): every AO-dispatched plan needs a gated finalize plan.
assigned_role: infra
drift_direction: advance-code
sequential: true
---

# AO fleet throughput incident — finalize

> **Machine-gated on `ao_fleet_throughput_incident_2026_07_25.md`** — will not dispatch until all 3 of that plan's todos
> are `done`.

## Todos

- [ ] [REVIEW] P1. **Re-verify all 3 parent-plan done-claims.** For each of
      `ao_fleet_throughput_incident_2026_07_25.md`'s 3 todos, confirm the cited evidence (commit SHA, Slack message, or
      activity-log entry) actually resolves — re-run `git show <sha>` for any cited commit and re-check any cited
      activity-log/Slack evidence still exists. **Done when**: all 3 todos' evidence independently re-verified,
      discrepancies (if any) logged in this doc's Progress Log.
- [ ] [INFRA] P1. **Cross-check todo 2's dormant-slot finding against `ao_worker_context_lifecycle_gap_2026_07_25.md`.**
      If the parent plan's audit found slots 13/14/15/0 dormant due to an intentional AutoSpawn concurrency cap (not a
      bug), confirm that cap doesn't undermine the context-lifecycle plan's assumption that all working slots are
      reachable by its new gate/directive logic — if the cap means some slots never actually run long enough to
      accumulate the cross-task context carryover this plan complex was built for, note that explicitly (informational,
      not a required code change). **Done when**: a one-paragraph cross-check note is added to this doc's Progress Log.
- [ ] [INFRA] P2. **Run the standard 6-step archival ritual** on `ao_fleet_throughput_incident_2026_07_25.md`: migrate
      any DEFERRED items into new tracked todos, add a `> **🟢 ARCHIVED**` banner, run the codex-alignment check (does
      any `/codex/05-infrastructure/vm-launcher-runbook.md` or orchestrator-alerting doc need updating given todo 1's
      alert-verification findings?), update CLAUDE.md/codex on any new contract discovered (e.g. if the dormant-slot
      audit revealed AutoSpawn's real concurrency target, that belongs in
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`), fix every referrer's path corpus-wide
      (`grep -rl ao_fleet_throughput_incident_2026_07_25 plans/ codex/` and update each hit), then move the plan file to
      `plans/archive/2026_07/`. **Done when**: the plan is archived with a banner, zero corpus-wide stale referrers
      remain (verified by the grep above returning only the archived copy's own path), and any real new contract found
      is reflected in codex.
