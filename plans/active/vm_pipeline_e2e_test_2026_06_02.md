---
title: VM pipeline e2e test (vm-e2e-test) — DELETE AFTER
parent_epic: orchestrator_master
assigned_vm: vm-e2e-test
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
created: 2026-06-02
---

# VM pipeline e2e test

**TEST PLAN — safe to delete.** Verifies the FULL pipeline on a real VM:
push → pm-pull → regen → backlog → autospawn → worker → execute → flip → push.

- [ ] [DOC] P0. Create the file `_vm_e2e_test/marker.md` inside the `unified-trading-pm`
      repo containing a single line: `vm pipeline e2e OK — <hostname> — <UTC timestamp>`.
      Then commit it (`test(e2e): vm pipeline marker`) and push to `live-defi-rollout`.
      Do nothing else after that. (Your normal ship → flip-this-checkbox → /done loop
      completes the test.)
