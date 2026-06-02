---
title: Orchestrator pipeline e2e discovery test (DELETE AFTER)
parent_epic: orchestrator_master
assigned_vm: vm-0
priority: P3
status: active
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
created: 2026-06-02
---

# Orchestrator pipeline e2e discovery test

**TEST PLAN — safe to delete.** Validates that the central VM (`vm-0`) pulls a
newly-pushed plan from the remote PM repo (`pm-pull` timer) and ingests its todo
into the orchestrator backlog (`PlanRegenLoop`). Created 2026-06-02 to verify the
create-plan → push → pm-pull → regen → backlog discovery path end-to-end.

- [ ] [DOC] P3. Pipeline discovery marker (no-op). If this todo appears in the
      central VM's backlog, the create-plan → push → pm-pull → PlanRegenLoop →
      backlog routing path works.
