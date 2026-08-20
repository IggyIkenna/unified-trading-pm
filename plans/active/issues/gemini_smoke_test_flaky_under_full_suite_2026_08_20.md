---
doc_type: issue
title: "agent-orchestrator QG intermittently RED — test_gemini_litellm_translation_smoke.py::test_tool_use_tool_result_roundtrip_through_real_proxy flakes under full-suite load (passes in isolation)"
summary: >-
  A full `quality-gates.sh` run on agent-orchestrator@1e65044677 failed with exactly one pytest failure:
  `tests/test_gemini_litellm_translation_smoke.py::test_tool_use_tool_result_roundtrip_through_real_proxy`
  (1 failed, 4901 passed). The same test passes in isolation (~7s) and passed on the immediately-following full
  re-run. It is a live `integration`+`smoke` test: starts the real litellm proxy subprocess against the real
  Gemini backend and drives a real two-turn tool-call exchange. Under concurrent full-suite + shared-host load it
  intermittently trips (likely the 45s proxy-startup or 60s API-call timeout). Unrelated to the dirty-gate fix
  shipped in the same commit — the failing file is untouched by that diff.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, quality-gates, flaky-test, integration, smoke]
related: [ao_qg_red_dirty_gate_tests_and_missing_recharts_2026_08_19, ao_consolidated_closeout_2026_08_12]
created: "2026-08-20"
author: worker (slot 14)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
drift_direction: none
parent_epic: orchestrator_master
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Observed 2026-08-20 while shipping the dirty-gate test fix
  (ao_qg_red_dirty_gate_tests_and_missing_recharts_2026_08_19.md BACKEND todo, agent-orchestrator@1e65044677):
  Pass-1 quality-gates.sh run 1 failed on this single flaky test; isolated run passed (~7s); full QG run 2 passed.
context_scope: []
---

# agent-orchestrator QG intermittently RED — gemini smoke test flaky under load

## What I found

`tests/test_gemini_litellm_translation_smoke.py::test_tool_use_tool_result_roundtrip_through_real_proxy` is a live
integration/smoke test (real litellm proxy subprocess + real Gemini backend + real API key resolved on the VM — see
the module docstring: it skips cleanly only when litellm[proxy] or a key is unavailable). On a full QG run it
intermittently fails (1 failed / 4901 passed), yet passes deterministically in isolation (~7s). The module's own
tunables — `_STARTUP_TIMEOUT_S = 45.0` (proxy readiness poll) and 60s per API call — are the likely flake surfaces
under concurrent full-suite + multi-slot shared-host load.

## Why it matters

An intermittent QG red on a live smoke test blocks ANY agent-orchestrator worker's Pass-1/Pass-2 ship (the commit is
the per-repo quality boundary; the sentinel requires a clean full run). A worker whose otherwise-correct change hits
this flake burns a full ~6-min QG re-run, and the red has no relation to their diff.

## Recommended decision

Make the live smoke test resilient to load so it cannot intermittently red QG:
- Mark it `host_load_sensitive` (registered marker — precedent:
  `/plans/archive/issues/agent_orchestrator_qg_red_test_autospawn_magicmock_datetime_2026_07_30.md`), OR
- Add a bounded single retry on proxy-startup / roundtrip for transient load-induced timeouts.

## Todos

- [ ] [BACKEND] P2. Make `tests/test_gemini_litellm_translation_smoke.py`'s live leg
      (`test_tool_use_tool_result_roundtrip_through_real_proxy`) load-resilient: mark it `host_load_sensitive` OR
      add a single bounded retry on proxy-startup/API-call timeouts, so an intermittent full-suite-load timeout
      cannot red `quality-gates.sh`. Done-when: two consecutive full `quality-gates.sh` runs green with no flaky
      failure on this test. Repo: agent-orchestrator.

## Progress Log

- **2026-08-20 (slot 14)**: Filed after QG run 1 failed on this single test while shipping the dirty-gate fix;
  isolated run passed (~7s); full QG run 2 passed. Flake confirmed load/order-dependent, unrelated to the shipped
  diff (which touches only `tests/test_ao_self_pull_dirty_gate.py`).
