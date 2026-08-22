---
doc_type: plan
title: infra satellite — deployment-service client fixes + QG host-contention hardening (batch 2)
summary: >-
  15-todo extraction from /ag-closeout-audit's 2026-08-21 infra-tranche Phase 3 pass, across 3 source docs: (1)
  deployment_service_client_broken_functions_2026_08_20.md's 9 live-broken deployment-service-client function
  fixes + 2 dead-code confirm-and-remove items (all mirror an already-shipped reference fix, no design fork); (2)
  agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md's 2 bounded follow-ups (wire the
  proven split-coverage workaround into quality-gates.sh permanently; cross-check against RB-34953de6); (3)
  agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md's 2 bounded follow-ups (make a cgroup-MemoryMax
  kill loudly diagnosable in the QG log; sweep other repos for similarly stale QG baselines). All three source
  docs' own open-ended/investigation-only items (RSS-doubling root-cause, host-level `--cov` death investigation)
  are deliberately left in the source docs, not extracted here.
status: draft
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-api, agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags:
  [infra, ao-dispatch, satellite, batch-2, ag-closeout-audit, deployment-service, quality-gates, host-contention]
related:
  [
    /plans/active/issues/deployment_service_client_broken_functions_2026_08_20.md,
    /plans/active/issues/agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md,
    /plans/archive/issues/agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md,
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_21.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2.2
estimate_calibrated_ai_days: 0.88
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/deployment_service_client_broken_functions_2026_08_20.md,
    deployment-api/deployment_api/clients/deployment_service_client.py,
    /plans/active/issues/agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md,
    /plans/archive/issues/agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md,
    agent-orchestrator/scripts/quality-gates.sh,
    scripts/quality-gates-base/qg-host-governor.sh,
  ]
source:
  [
    "ag-closeout-audit infra tranche, 2026-08-21 Phase 3 — extracted verbatim from
    deployment_service_client_broken_functions_2026_08_20.md's 11 todos and 2 bounded todos each from
    agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md and
    agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md.",
  ]
---

# infra satellite — deployment-service client fixes + QG host-contention hardening (batch 2)

> **Fresh carve-out, 15-todo, WITH a finalize twin** (`infra_satellite_ao_dispatch_batch2_finalize_2026_08_21.md`,
> gated). `status: draft` / `assigned_vm: NA` pending operator review before dispatch. Each todo below is a pointer
> + extraction provenance, not a re-derivation — read the cited source doc's own text for full context before
> starting.

## Todos 1-9 — deployment-service-client live-broken function fixes

Source: `deployment_service_client_broken_functions_2026_08_20.md` (2026-08-20 audit; already converted from prose
to tracked checkboxes by a 2026-08-20 `/plan-reconcile` pass). Each function is live-broken for the same root
cause `create_deployment()` already fixed as the reference pattern: it still constructs an HTTP request through
`_base_url()`/`DEPLOYMENT_SERVICE_URL` (default `http://localhost:9000`), and deployment-service has no reachable
Cloud Run Service — the fix is the SAME CLI/library-subprocess transport `create_deployment()` already uses
(`deployment_service_client.py:18-27, 197-264`), preserving each function's existing response contract and caller
error handling.

- [ ] [BACKEND] P1. Fix `calculate_shards` — CLI/library transport per the `create_deployment()` reference fix,
      live callers `deployment_manager.py:200,320`. Repo: deployment-api.
- [ ] [BACKEND] P1. Fix `get_data_status` — live callers `routes/data_status_helpers.py:43` and UI
      `DataStatusTab.tsx` (`:832`, `:855`, `:943` via `api/client.ts:628-680`). Repo: deployment-api.
- [ ] [BACKEND] P1. Fix `cancel_vm_jobs` — live caller `_deployment_processor_helpers.py:36-65`. Repo:
      deployment-api.
- [ ] [BACKEND] P1. Fix `get_vm_status_batch` — live caller `routes/deployment_state.py:287`. Repo: deployment-api.
- [ ] [BACKEND] P1. Fix `get_cloud_run_status_batch` — live callers `_deployment_processor_cloud_run.py:33`,
      `services/event_processor.py:332`, `routes/deployment_state.py:223`. Repo: deployment-api.
- [ ] [BACKEND] P1. Fix `get_deployment_events` — live callers `routes/deployments/_lifecycle.py:272-303` and UI
      `DeploymentDetails.tsx:411` via `api/client.ts:3804-3809`. Repo: deployment-api.
- [ ] [BACKEND] P1. Fix `get_vm_events` — live caller `routes/deployments/_lifecycle.py:303-338`. Repo:
      deployment-api.
- [ ] [BACKEND] P1. Fix `live_rollback` — live callers `routes/deployments/_lifecycle.py:341-373` and UI
      `DeploymentDetails.tsx:441` via `api/client.ts:3826-3834`. Repo: deployment-api.
- [ ] [BACKEND] P1. Fix `get_live_health` — live callers `routes/deployments/_lifecycle.py:376-415` and UI
      `DeploymentDetails.tsx:423` via `api/client.ts:3840-3847`. Repo: deployment-api.

Done-when (all 9): each function's implementation routes through the bundled deployment-service CLI in a
subprocess instead of an HTTP call to `DEPLOYMENT_SERVICE_URL`; every named live caller (backend + UI) continues
to receive the same response contract; `quality-gates.sh`-green for deployment-api, shipped via
`quickmerge.sh --agent --files`. Flip each todo here AND the matching row in the source doc's own table in the
same commit citing this batch's completion evidence.

**Conflict-check (this pass, 2026-08-21)**: grepped `plans/active/*.md` + `plans/active/issues/*.md` for
`deployment_service_client.py` — only the source doc and `deployment_service_api_integration_cleanup_2026_08_18.md`
(the parent plan that spawned this audit's original findings-triage) reference it; the parent plan's own scope is
`create_deployment()` only (already done, the reference fix), not these 9 — no overlapping claim.

## Todos 10-11 — dead-code confirm-and-remove

- [ ] [BACKEND] P3. Confirm `quota_acquire_batch` has no external consumer (only self-contained definition at
      `deployment_service_client.py:453-488`, no in-repo caller found per the source audit), then remove it as
      dead code. Repo: deployment-api.
- [ ] [BACKEND] P3. Confirm `quota_release_batch` has no external consumer (only self-contained definition at
      `deployment_service_client.py:535-563`, no in-repo caller found per the source audit), then remove it as
      dead code. Repo: deployment-api.

Done-when (both): a fresh grep across deployment-api and deployment-ui confirms zero external callers (re-verify,
don't just trust the 2026-08-20 audit's count — it may have drifted); the function is deleted along with any
now-unused imports; `quality-gates.sh`-green, shipped via `quickmerge.sh --agent --files`.

## Todo 12 — wire the split-coverage workaround into quality-gates.sh permanently

- [ ] [BACKEND] P2. **Wire the split-coverage-with-separate-`COVERAGE_FILE`-then-`coverage combine` workaround
      into `scripts/quality-gates.sh`'s pytest+coverage step permanently** — extracted verbatim from
      `agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md` todo 1. The source doc already
      proved the exact mechanism twice (bisect `tests/test_*.py` alphabetically into two file-lists, run each as a
      separate pytest invocation with its OWN `COVERAGE_FILE` env var — NOT `--cov-append` onto one shared file,
      which reproduces the same silent death on the second half — then `coverage combine` + `coverage json`/
      `report --fail-under` + the existing ratchet check as separate lightweight steps). Root cause: agent-
      orchestrator's full `pytest --cov=server` run (~5236 tests) dies silently near 96-97% completion under this
      shared host's concurrent-session load, confirmed not OOM/pids/tracer-backend — the same suite WITHOUT `--cov`
      completes cleanly in 211s. Done-when: `scripts/quality-gates.sh` runs the split-then-combine sequence by
      default (no manual workaround needed); a full local run on a loaded host completes without the silent death;
      `quality-gates.sh`-green (self-referential — verify the changed script itself passes), shipped via
      `quickmerge.sh --agent --files`. Repo: agent-orchestrator.
      **Conflict-check (this pass, 2026-08-21)**: grepped `plans/active/*.md` + `plans/active/issues/*.md` for
      "COVERAGE_FILE" + "coverage combine" — only the source doc's own text references the proven workaround; no
      other active plan claims this wiring.

## Todo 13 — cross-check against RB-34953de6

- [ ] [BACKEND] P3. Cross-check `agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md`'s
      finding against repo-blocker `RB-34953de6`'s own diagnosis (different slot/escalation, same day, same repo,
      same class of symptom: coverage/collection failures under concurrent host load) once that blocker is worked
      — confirm whether it's the identical root cause or a distinct one, and fold findings together if so (e.g.
      note the cross-reference in both docs, or merge into one if genuinely the same mechanism). Done-when:
      `RB-34953de6`'s current state is checked (resolved/still open) and this doc's own text is updated with the
      cross-check verdict, either way. Repo: agent-orchestrator.
      **Conflict-check (this pass, 2026-08-21)**: `RB-34953de6` is a repo-blocker id, not a doc path — grepped
      `plans/active/*.md` + `plans/active/issues/*.md` for the literal string, only the source doc references it;
      no other active plan claims this cross-check.

## Todo 14 — make a cgroup-MemoryMax kill loudly diagnosable

- [ ] [SCRIPT] P2. **Make a cgroup-`MemoryMax` kill loudly diagnosable from the QG/quickmerge log itself** —
      extracted verbatim from `agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md` todo 2 (the
      diagnosability ask; the doc's own sibling todo about WHY agent-orchestrator's RSS roughly doubled is
      deliberately NOT extracted here — that's an open-ended root-cause investigation, not a bounded fix). Today
      the only way to tell "died from the reservation-mode governor's memory cap" apart from "died from generic
      host contention" or "died from a real test failure" is manually correlating `ps` RSS growth against the
      committed baseline mid-run — confirm `_qg_governor_detect_oom_kill` (referenced at `qg-host-governor.sh:659`)
      actually surfaces a clear message in quickmerge's own stdout/log for every repo it wraps, not just the
      basedpyright case the existing code comment describes; if it doesn't fire reliably, fix it so it does.
      Done-when: a synthetic/forced cgroup-MemoryMax kill (e.g. an artificially low committed baseline on a scratch
      repo) produces a clear, unambiguous log line in the QG/quickmerge output identifying the memory cap as the
      cause, not a silent stop; `quality-gates.sh`-green, shipped via `quickmerge.sh --agent --files`. Repo:
      unified-trading-pm.
      **Conflict-check (this pass, 2026-08-21)**: grepped `plans/active/*.md` + `plans/active/issues/*.md` for
      `_qg_governor_detect_oom_kill` — only the source doc references it; no other active plan claims this fix.
      Cross-note: the source doc's own CORRECTION section says the memory-cap theory was NOT the actual blocker for
      the specific incident that triggered the doc (a separate `orphan_reap` bug was) — this todo is still real,
      independently-worth-fixing work per the doc's own text, not superseded by that correction.

## Todo 15 — sweep other repos for similarly stale QG baselines

- [ ] [SCRIPT] P3. **Check whether other repos on this shared host have a similarly stale (>20% under-measured)
      QG memory baseline** that would silently fail the same way on their next quickmerge — extracted verbatim
      from `agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md` todo 3. `scripts/dev/
      qg_resource_baseline.json` is the full committed set; run a bulk delta report (current measured peak-RSS vs.
      committed baseline, per repo, without forcing an update) so any repo trending toward the same >=20%
      overshoot that triggered agent-orchestrator's incident is caught proactively rather than discovered by the
      next person's quickmerge silently dying. Done-when: a delta report is produced for every repo in
      `qg_resource_baseline.json`, and any repo found >=20% over its committed baseline gets a follow-up (either
      re-measured via `measure-qg-baseline.sh --force` if the growth is confirmed genuine steady-state, or flagged
      for its own investigation if the cause is unclear) — do not blind-force every repo without checking each
      delta individually. `quality-gates.sh`-green if any script change is made, shipped via `quickmerge.sh --agent
      --files`. Repo: unified-trading-pm.
      **Conflict-check (this pass, 2026-08-21)**: grepped `plans/active/*.md` + `plans/active/issues/*.md` for
      `qg_resource_baseline.json` — the source doc plus `qg_host_adaptive_resource_governor_2026_07_14.md` (a
      LOCAL, operator-driven, `assigned_vm: NA` design plan per its own explicit banner — different scope, the
      full governor redesign, not a bounded per-repo delta sweep) reference it; no overlapping AO-dispatched claim.

## Progress Log

- **ag-closeout-audit 2026-08-21 (infra tranche, Phase 3)**: drafted. All 15 todos re-verified fresh against their
  source docs' current state (not just the parked-audit doc's one-line taxonomy) before extraction — confirmed
  each is genuinely bounded with a concrete done-when bar and no open design fork. Deliberately left in the source
  docs: the RSS-doubling root-cause investigation (open-ended), the host-level `--cov` silent-death investigation
  (open-ended, `agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md`'s own framing), and
  `qg_host_adaptive_resource_governor_2026_07_14.md`'s full governor redesign (explicit operator-ruled LOCAL/human
  plan, not AO-eligible). Source docs' own checkboxes annotated `➡️ EXTRACTED` in the same pass.
