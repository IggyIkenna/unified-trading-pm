---
doc_type: plan
title: Data-Pipeline Self-Healing Completion — Residual Actuator Wiring (forked from the hardening/self-monitoring plan)
summary: |
  The residual self-healing (Phase 6-C) items forked out of data_pipeline_hardening_self_monitoring_2026_06_22.md
  during the 2026-07-24 line-cap remediation split: finishing the e2e escalation-issue ship, scheduling the auto-flip
  reclassifier, flipping registry alert modes verbose to active, shipping the dp-audit OOM-fix + image-default terraform,
  the digest memory antipattern, delivering the consolidator asset_group guard via the MTDS image, rebuilding
  e2e-audit latest for the reprobe hooks, packaging the self-heal actuators into the runtime image, and the stretch
  full-launch-spec persistence. All are tail items on an otherwise-shipped detect-auto_recover-file_issue-page loop.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [data-pipeline, self-healing, actuators, monitoring, plan-split, residual]
related:
  [
    /plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/active/data_pipeline_alert_substrate_residual_2026_07_24.md,
    /plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: observability_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
assigned_role: data_engineering
drift_direction: advance-code
supersedes:
superseded_by:
depends_on:
source:
  [
    "Forked 2026-07-24 from data_pipeline_hardening_self_monitoring_2026_06_22.md per the plan line-cap remediation
    triage (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 9, 'self-healing completion' fork) —
    operator approved unlock+split via interactive Q&A.",
  ]
locked_by:
locked_since:
---

# Data-Pipeline Self-Healing Completion — Residual Actuator Wiring

> **Forked 2026-07-24** from
> [`data_pipeline_hardening_self_monitoring_2026_06_22.md`](/plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md)
> as 1 of a 4-way split (+ 1 excise) approved by the operator via the plan line-cap remediation triage
> (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 9). The detect→auto_recover→file_issue→page loop
> is LIVE end-to-end (see the parent plan's "Progress Log — LOOP LIVE END-TO-END (VERIFIED, 2026-06-23)"); this plan
> carries ONLY the still-open tail items on that loop, moved **verbatim** from their original sections. Sibling forks:
> `data_pipeline_alert_substrate_residual_2026_07_24.md` (Phase 2/3/4/6-B),
> `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md` (TradFi/DeFi AG-specific residuals).

## Residual from Phase 6 (Self-healing completion, tier C — wire tiers to existing recovery, add actuators)

### Self-healing completion (C — wire tiers to existing recovery, add actuators)

- [x] ✅ [CODE] P0. Add `data_pipeline_failure` to `escalate-to-orchestrator` `WALL_TYPES`
      (`agent-orchestrator/server/escalation.py`) + a boot-prompt template, so a DP `file_issue`/`page` finding can
      fast-spawn an autonomous worker (today WALL_TYPES has no DP member → ValueError). — agent-orchestrator,
      unified-trading-pm (.github) — DONE **agent-orchestrator@8e24912** (`data_pipeline_failure` added to
      `WALL_TYPES` + `_DATA_PIPELINE_WALLS` + `_prompt_template_for()` routing to the dedicated
      `agents/data_pipeline_failure.md` boot prompt — push-fix-to-LDR flow like main_ci_red/plan_health, NOT the
      conflict-resolver; the worker cold-starts on SUB_AGENT_MANDATORY_RULES + the DP codex SSOTs + the filed issue doc;
      `EscalateRequest` Literal + `main_ci_red` gap fixed; one-shot AgentRow `agent_kind=data_pipeline_failure`; 5 new
      tests; QG green exit 0) + **unified-trading-pm@d4746eb02** (`.github/workflows/escalate-to-orchestrator.yml`
      accepts `data_pipeline_failure` in the workflow_call/dispatch choice + bash case guard + error message —
      sanctioned `.github` carve-out).
- [x] ✅ [CODE] P1. Wire `escalation.py::route_finding` `auto_recover` tier → the Layer-0 recovery actuators (the
      `refetch-feed` pattern) via a `_DP_RECOVERY_ACTIONS` dispatch; an auto_recover event with no wired actuator OR a
      FAILED/budget-paged actuator falls through to `file_issue` (never a silent no-op). — deployment-service@e695fa3
      (CONSOLIDATOR_DOWN→relaunch_consolidator, DP_VM_EXIT_NONZERO-OOM→relaunch_backfill_vm; QG --no-fix exit 0 53s)
- [x] ✅ [CODE] P1. **Actuators (were detect+page only)**: `scripts/recovery/relaunch_consolidator.py` (re-execute
      `manifest-consolidator-{ag}` Cloud Run Job on CONSOLIDATOR_DOWN via sanctioned `_gcp_sdk` run_v2.JobsClient,
      bounded 1/120s-cooldown, emits CONSOLIDATOR_RECOVERED) + `scripts/recovery/relaunch_backfill_vm.py` (re-launch OOM
      exit-137 backfill via its launcher — streams durable logs + registers, never fire-and-forget — budget ≤2 per
      (vm-prefix, day) then page_operator). 14 credential-free tests. — deployment-service@e695fa3
- [x] ✅ [CODE] P0. **DP_VM_STALL self-heal actuator** (the loop was OPEN — DP_VM_STALL was `auto_recover` tier with NO
      wired actuator → it fell through to `file_issue`; a hung VM like `tradfi-bf-cme` never auto-recovered). NEW
      `scripts/recovery/relaunch_stalled_vm.py` (mirrors `relaunch_backfill_vm` — idempotent, ≤2/(vm-prefix, day) then
      page, emits a lifecycle event, NEVER fire-and-forget; unconditional on exit code since the watchdog already killed
      the VM, the stall verdict is the trigger) + registered `DP_VM_STALL → relaunch_stalled_vm` in
      `_DP_RECOVERY_ACTIONS` + `heartbeat_stall_watcher.sweep` gains a `launcher_for_vm` resolver so the DP_VM_STALL
      finding carries `relaunch_launcher` (absent → falls through to file_issue). DP_EVENT_LOOP_STARVED stays file_issue
      (a never-emitting VM is a code bug, not a relaunch). 5 new credential-free tests. — deployment-service@1b529e4 (QG
      --no-fix exit 0 54s)
- [x] ✅ [CODE] P1. **Make file_issue ACTIONABLE so an agent picks it up** — both issue writers
      (`escalation.py::_write_issue_doc` + `e2e _dp_common.file_escalation_issue`) now emit frontmatter
      `parent_epic: observability_master` + `assigned_vm: vm-cross-cutting` (PlanRegenLoop ONLY ingests an issues/ doc
      with an explicit `assigned_vm` → was silently skipped) + a real
      `- [ ] [CODE] P1. <finding> — diagnose + fix <root cause> in <target repo>` todo (VM-lifecycle →
      deployment-service, misclassified-empty/divergence → MTDS) + cold-start context (read SUB_AGENT_MANDATORY_RULES +
      the DP codex + the finding details). Idempotent (overwrites same slug+date doc). deployment-service half
      (`escalation.py`) SHIPPED **deployment-service@1b529e4**; e2e half (`_dp_common.py`) QG-green but **🟡 BLOCKED ON
      DIRTY DEP** (quickmerge pre-flight refuses while peer's `strategy-service` WIP is uncommitted — never quickmerge
      with dirty deps). Ship the e2e half once that foreign WIP clears. — deployment-service@1b529e4 + e2e-testing
      (pending)
- [x] ✅ [CODE] P1. **Fast CI-parity auto-spawn for CRITICAL** — `route_finding` now ALSO fires a best-effort
      `repository_dispatch` (`escalate-to-orchestrator`, `client_payload[wall_type]=data_pipeline_failure`) for a
      page_operator-tier (CRITICAL) OR confirmed file_issue finding, auth'd with the workflow-capable `GH_PAT` from
      Secret Manager. Best-effort: a missing token (token-less Cloud Run Job) / SM-denied / network failure returns
      `{dispatched: False}` and NEVER breaks the finding (mirrors the alerting soft-gates) — Fix 2's PlanRegenLoop path
      still picks it up. — deployment-service@1b529e4
- [ ] [CODE] P1. **Ship the e2e `_dp_common.file_escalation_issue` actionable-issue half** (frontmatter
      `parent_epic`/`assigned_vm` + `- [ ] [CODE] P1.` todo + `target_repo` routing + new
      `test_file_escalation_issue_is_actionable`) — code is WRITTEN + QG-green (`quality-gates.sh --no-fix` exit 0 31s)
      but quickmerge is **🟡 BLOCKED**: e2e's pre-flight refuses while peer `strategy-service` WIP is uncommitted (never
      quickmerge with dirty deps). Re-run
      `quickmerge --agent --files 'scripts/audit/_dp_common.py tests/unit/test_dp_audit.py'` from e2e-testing once
      `strategy-service` is clean. Provenance: slot-3 escalation-loop 2026-06-23. — e2e-testing
- [x] ✅ [INFRA] P2. **Wire `launcher_for_vm` in the dp-fleet-monitor CLI** — deployment-service@3045b7f: CLI
      `_launcher_for_vm` (wraps `resolve_launcher_for_vm`, None→"") now passed into BOTH
      `exit_code_fleet_monitor.sweep` + `heartbeat_stall_watcher.sweep` (was `None`) → stall/OOM findings carry
      `relaunch_launcher` → actuator relaunches instead of file_issue. QG green (64s). — deployment-service
- [x] ✅ [CODE] P1. **Auto-flip reclassifier** (the detect→prove→FLIP→re-capture loop) — DONE **e2e-testing@1b220fc**.
      `reprobe_new_empty_confirmed.py` gains a `--reclassify-apply` mode (default OFF/dry-run): ONLY a
      `REPROBE_RETURNED_ROWS` verdict (a wired live re-fetch hook ACTUALLY returned rows = PROVEN misclassification)
      flips the manifest cell `empty_confirmed`→`attempted_failed` with typed reason
      `error_reason="REPROBE_PROVED_FETCHABLE"` so the orchestrator's `_should_skip_shard` re-attempts it. NEVER flips
      `ORACLE_EXPECTS_DATA`/`AMBIGUOUS`/`OK_HONEST_EMPTY` (an oracle expectation is not proof — auto-flipping could
      corrupt a legitimate honest-empty; those stay file_issue-only). Backup-then-write (mirrors the canonical
      `instruments-service/scripts/flip_phantom_to_attempted_failed.py`), idempotent, bounded ≤200 cells/run (loud
      `CAP EXCEEDED` log + skip — no silent truncation). Emits `DP_EMPTY_REPROBE_DISAGREEMENT` with `reclassified:true`
      on each flip. 7 new credential-free tests (mock GCS index read+write). QG: `quality-gates.sh --no-fix` exit 0
      (45s).
- [ ] [INFRA] P1. **Schedule** the auto-flip on the daily reprobe cron — the `dp_reprobe_empty_job` terraform stanza
      (`deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf`) currently runs detect-only
      (`command=[python3, .../reprobe_new_empty_confirmed.py], args=[]`). Change `args = []` →
      `args = ["--reclassify-apply"]` so the 09:00-UTC job both DETECTS and FLIPS proven cells daily, then `tofu apply`
      the single targeted change. **BLOCKED on peer-dirty deployment-service** (Phase-6 INFRA item above: active foreign
      WIP `cloud_run_job_registry.py`/`escalation.py`/`scripts/recovery/relaunch_*.py` + dirty UAC dep → no clean
      QG-green/quickmerge boundary). Ship the single-line `.tf` arg change once that foreign WIP clears (pure-terraform,
      cannot affect Python QG). — deployment-service
- [x] ✅ [CODE] P1. DONE mtds@477de66. **Bucket-env parity preflight** (DP-ENV-001 — reader env-less vs writer
      env-short) as a generic gate. — market-tick-data-service
- [x] ✅ [CODE] P1. DONE mtds@477de66. **429-aware key-pool rotation** + `DP_KEY_POOL_EXHAUSTED` alert (TheGraph 9-key
      currently degrades silently to unauth). — market-tick-data-service
- [x] ✅ [DOC] P1. DONE /codex/15-runbooks/incidents/rb_data_001.md. **RB-DATA-\* DR runbook** — the
      consolidator→MTDS→features cascade with RTO/RPO + auto-vs-human scope (none of the 22 rb\_\* runbooks is
      data-pipeline). — unified-trading-pm
- [ ] [CODE] P2. Flip `data-pipeline-alerts.registry.yaml` modes `verbose`→`active` as each `escalation:` tier is wired
      to plumbing. — unified-trading-pm
- [ ] [INFRA] P1. **Ship the dp-audit OOM-fix + image-default terraform**
      (`deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf`): bump all 4 dp-audit Cloud Run jobs
      `4Gi/2cpu`→`16Gi/4cpu` (the digest/hygiene/reprobe scripts read the FULL per-AG `_index` with `columns=None` →
      tradfi/cefi OOM-killed at 4Gi, signal-9 "configured memory limit reached", verified 2026-06-22), AND fold in
      `var.dp_audit_image` default → the `e2e-audit:latest` image (closes the IMAGE GAP). **Both changes ALREADY APPLIED
      to live prod state** (`tofu apply` targeted, `0 add/4 change/0 destroy`, plan clean) + written to the
      deployment-service working tree — **commit BLOCKED**: this clone has active foreign WIP
      (`cloud_run_job_registry.py`, `escalation.py`, untracked `scripts/recovery/relaunch_*.py` with import-pattern QG
      violations) + a dirty UAC dep (`honest_coverage.py`) → no clean QG-green / quickmerge boundary for a sibling
      agent's tree. Ship the single `.tf` file once the foreign WIP clears (it is a pure-terraform change, cannot affect
      Python QG). — deployment-service
- [ ] [PERF] P2. **DeFi/observability: `data_pipeline_daily_digest.py` + `_dp_common.read_manifest_index` memory
      antipattern** — the digest reads the full index (`columns=None`) then count-EXPANDS into per-row Python lists
      (`["captured"]*N` for millions of rows) → the actual OOM driver (16Gi is a band-aid). Restrict
      `read_manifest_index(columns=[pipeline_mode, venue,chain,data_type,capture_status])` + aggregate counts without
      list-expansion; then the jobs can drop back to ~4–8Gi. — e2e-testing

## Later-surfaced self-healing deployment residuals (2026-06-23/24, still open)

- [ ] [INFRA] P1. **SCHEDULED consolidator asset_group guard — deliver via MTDS image (in flight 2026-06-23).** The ~40
      `uts-prod-manifest-consolidator-*` Cloud Run jobs run `unified_trading_library.manifest_consolidator` from
      `market-tick-data-service:latest` (NOT the deployment-service-jobs image). The v9 blank-asset_group self-heal
      (`_asset_group_for_market_data_bucket`, UTL `7b2306c3`/`6acbb9ad`) is in UTL `:latest` (`3f2b47f2`) but NOT the
      MTDS-pinned base `af5f6c1e`. Bumped MTDS `Dockerfile` base-digest `af5f6c1e`→`3f2b47f2`
      (market-tick-data-service@81dbe37) + direct-built `market-tick-data-service:latest` from LDR `b3f67ac` (build
      `beb0b08e`). **Flip when**: build SUCCESS + new MTDS:latest digest verified to differ + one consolidator execution
      (e.g. `uts-prod-manifest-consolidator-instruments-defi`) runs exit 0 on the new image. — market-tick-data-service

- **Follow-up (tracked below)**: the e2e-audit Cloud Run image should be rebuilt from clean LDR so the daily reprobe
  cron runs with all 5 hooks wired (auto-flip is proof-gated → safely no-ops on the current image for tradfi/prediction,
  which both return reached_source=False, so this is a correctness-completeness rebuild, not an outage).
- [ ] [INFRA] P2. **Rebuild e2e-audit:latest from clean LDR** so the daily reprobe cron loads all 5 per-AG hooks
      (currently the image predates `e2e-testing@5db3860`; tradfi/prediction hooks return reached_source=False so the
      missing load is a no-op for them today, but a defi/cefi/sports hook update needs the rebuild to take effect).
      Reuse the `cloudbuild-e2e-audit.yaml` build→smoke→push from the IMAGE-GAP-CLOSED run. — e2e-testing,
      deployment-service

- [ ] [CODE] P1. **Package the self-heal actuators (+ launchers) into the runtime image** so the `auto_recover` tier can
      actually ACTUATE a relaunch from the Cloud Run monitors (today it always degrades to `file_issue` there because
      `scripts/recovery` + `scripts/vm` are absent from the deployment-api image). Options: move actuator classes into
      `deployment_service/` package + make launcher-dir resolution image-safe (NOT `__file__`-relative), and ship
      `scripts/vm/launch-*.sh` into the image; OR run the monitors on a host where `scripts/` exists. Repo:
      deployment-service. Until then self-heal = detect+file_issue+escalate (the deadman/observability half is
      unaffected).

- [ ] [CODE] P2. **(stretch) Persist the full launch spec (CLI args) into `DeploymentRegistryEntry`** so a relaunch
      replays the EXACT command, not just asset_group/task/mode/dates. Today the launcher knows the args but the
      registry row carries only the coarse tags; the worker reconstructs from launcher+tags. Repo: deployment-service
      (launcher → heartbeat → registry `extras`/new field). Provenance: escalate-to-orchestrator relaunch build
      2026-06-23.

## Success criteria

- All open todos above ticked `- [x]` with evidence (commit sha / QG sentinel / deploy verification per PLAN_FORMAT.md §
  8b for any runtime-infra claim).
- `bash scripts/plan-hygiene/check_line_caps.sh` no longer flags this file, and
  `bash scripts/plan-hygiene/run_hygiene_sweep.sh` shows 0 hard failures across the 4-way split.
