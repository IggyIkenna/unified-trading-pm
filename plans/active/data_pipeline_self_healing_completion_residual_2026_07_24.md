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
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/archive/2026_07/data_pipeline_alert_substrate_residual_2026_07_24.md,
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
context_scope:
  [
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/archive/2026_07/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/data-pipeline-alerts.registry.yaml,
    e2e-testing/scripts/audit/_dp_common.py,
    /plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md,
  ]
---

# Data-Pipeline Self-Healing Completion — Residual Actuator Wiring

> **Forked 2026-07-24** from
> [`data_pipeline_hardening_self_monitoring_2026_06_22.md`](/plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md)
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
- [x] ✅ [INFRA] P1. **Schedule** the auto-flip on the daily reprobe cron — the `dp_reprobe_empty_job` terraform stanza
      (`deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf`) currently runs detect-only
      (`command=[python3, .../reprobe_new_empty_confirmed.py], args=[]`). Change `args = []` →
      `args = ["--reclassify-apply"]` so the 09:00-UTC job both DETECTS and FLIPS proven cells daily, then `tofu apply`
      the single targeted change. **✅ THE `.tf` CHANGE HAS LANDED (re-verified 2026-07-26,
      `/ag-closeout-audit cross-cutting`)** — `deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf:281`
      now reads `args = ["--reclassify-apply"]` on the `dp_reprobe_empty_job` stanza, so the stale "currently runs
      detect-only (`args=[]`)" premise and the **BLOCKED on peer-dirty deployment-service** note below are both
      superseded — do NOT re-do this. (was: "BLOCKED on peer-dirty deployment-service — active foreign WIP
      `cloud_run_job_registry.py`/`escalation.py`/`scripts/recovery/relaunch_*.py` + dirty UAC dep → no clean
      QG-green/quickmerge boundary".) **✅ EXECUTION CONFIRMED 2026-07-26**
      (`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` todo 5):
      `gcloud run jobs executions describe uts-prod-dp-reprobe-empty-55rz8` (the 2026-07-26T09:00:03Z run) shows
      `args: [--reclassify-apply]` live in the deployed spec — the arg has been executing daily since the `.tf` landed.
      Also surfaced by the same check: every recent execution (2026-07-22..07-26) fails with "The configured memory
      limit was reached" (OOM) — see the sibling OOM-fix todo below, now also shipped. — deployment-service
- [x] ✅ [CODE] P1. DONE mtds@477de66. **Bucket-env parity preflight** (DP-ENV-001 — reader env-less vs writer
      env-short) as a generic gate. — market-tick-data-service
- [x] ✅ [CODE] P1. DONE mtds@477de66. **429-aware key-pool rotation** + `DP_KEY_POOL_EXHAUSTED` alert (TheGraph 9-key
      currently degrades silently to unauth). — market-tick-data-service
- [x] ✅ [DOC] P1. DONE /codex/15-runbooks/incidents/rb_data_001.md. **RB-DATA-\* DR runbook** — the
      consolidator→MTDS→features cascade with RTO/RPO + auto-vs-human scope (none of the 22 rb\_\* runbooks is
      data-pipeline). — unified-trading-pm
- [ ] [CODE] P2. Flip `data-pipeline-alerts.registry.yaml` modes `verbose`→`active` as each `escalation:` tier is wired
      to plumbing. — unified-trading-pm
- [x] ✅ [INFRA] P1. **Ship the dp-audit OOM-fix + image-default terraform**
      (`deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf`): bump all 4 dp-audit Cloud Run jobs
      `4Gi/2cpu`→`16Gi/4cpu` (the digest/hygiene/reprobe scripts read the FULL per-AG `_index` with `columns=None` →
      tradfi/cefi OOM-killed at 4Gi, signal-9 "configured memory limit reached", verified 2026-06-22), AND fold in
      `var.dp_audit_image` default → the `e2e-audit:latest` image (closes the IMAGE GAP). — DONE 2026-07-26
      (`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` todo 5, deployment-service@f2d094e).

      **⚠️ CORRECTED 2026-07-26 (`/ag-closeout-audit cross-cutting`) — the "already applied" claim below was MEASURABLY
      FALSE; the OOM fix was NOT live at that point.** Measured, not inferred: (1) `gcloud run jobs describe uts-prod-dp-daily-digest`
      and `… uts-prod-dp-reprobe-empty` (region `asia-northeast1`, project `central-element-323112`) BOTH returned
      `cpu=2;memory=4Gi`; (2) the tracked `.tf` still read `memory = "4Gi" / cpu = "2"` at :91-92, :148-149, :267-268.
      So the 4 dp-audit jobs remained OOM-killable at 4Gi exactly as originally diagnosed — the digest/hygiene/reprobe
      monitoring was silently losing runs on tradfi/cefi. (was: "**Both changes ALREADY APPLIED to live prod state**
      (`tofu apply` targeted, `0 add/4 change/0 destroy`, plan clean) + written to the deployment-service working tree —
      **commit BLOCKED**: this clone has active foreign WIP (`cloud_run_job_registry.py`, `escalation.py`, untracked
      `scripts/recovery/relaunch_*.py` with import-pattern QG violations) + a dirty UAC dep (`honest_coverage.py`) → no
      clean QG-green / quickmerge boundary for a sibling agent's tree." Whether the apply never persisted or a later
      blanket apply reverted it was not established.) **The image-default HALF of this todo DID land** —
      `local.dp_audit_image_resolved` at :57 resolves `var.dp_audit_image` to `…/e2e-audit:latest`, so the IMAGE GAP is
      genuinely closed.

      **✅ MEMORY/CPU BUMP NOW SHIPPED 2026-07-26.** Re-measured before touching anything: ALL 4 jobs were live
      OOM-killing on their most recent execution ("The configured memory limit was reached", confirmed via
      `gcloud run jobs executions describe` on `uts-prod-dp-daily-digest`, `-dp-manifest-hygiene-changed`,
      `-dp-manifest-hygiene-full`, and `-dp-reprobe-empty` — the last one OOM-killed on 5 consecutive daily runs
      2026-07-22..07-26). Bumped all 4 job modules in the `.tf` to `cpu="4"`/`memory="16Gi"`
      (`dp_daily_digest_job`, `dp_manifest_hygiene_changed_job`, `dp_manifest_hygiene_full_job`,
      `dp_reprobe_empty_job`). `ENV=prod ./tofu.sh plan -target=...` (all 4 modules) showed exactly
      `0 to add, 4 to change, 0 to destroy` — additive in-place resource-limit change only, no
      `[OPERATOR]` gate required per this todo's own scoping. Applied via `ENV=prod ./tofu.sh apply` (targeted).
      Post-apply `gcloud run jobs describe` confirms all 4: `cpu=4;memory=16Gi`. `.tf` committed +
      quickmerged — deployment-service@f2d094e, `quality-gates.sh` green (sentinel-verified). — deployment-service

- [x] ✅ [PERF] P2. **DeFi/observability: `data_pipeline_daily_digest.py` + `_dp_common.read_manifest_index` memory
      antipattern** — the digest reads the full index (`columns=None`) then count-EXPANDS into per-row Python lists
      (`["captured"]*N` for millions of rows) → the actual OOM driver (16Gi is a band-aid). Restrict
      `read_manifest_index(columns=[pipeline_mode, venue,chain,data_type,capture_status])` + aggregate counts without
      list-expansion; then the jobs can drop back to ~4–8Gi. — e2e-testing. **⚠️ OWNERSHIP RESOLVED 2026-07-31
      (corpus-wide ownership-conflict sweep, operator ruling newer/more-complete-wins): DO NOT EXECUTE HERE.** This is a
      near-verbatim duplicate of `/plans/archive/2026_07/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`'s
      `[PERF] P2` "Fix the real dp-audit OOM driver", which is the EXECUTION vehicle — it is newer,
      `assigned_vm: planning` (dispatchable, this doc is `NA`), and strictly more complete (it adds the
      sequence-after-the-16Gi-bump coordination constraint and an explicit Done-when). That todo's own Done-when already
      includes flipping THIS checkbox, so this stays `- [ ]` as the owner-of-record for open-task counting
      (`count_open_tasks.py` deliberately excludes satellite/batch aggregators from the deduped total) and gets flipped
      by whoever lands the batch2 item. **✅ FLIPPED 2026-08-02 (`/na-eligibility-audit cross-cutting`, KEEP-NA-STALE
      class) — the batch2 execution vehicle LANDED and its Done-when's "flip THIS checkbox" clause was never executed.**
      Evidence: `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md:299` is now `[x] ✅` citing
      **e2e-testing@5d7f53a** ("restrict daily-digest manifest read to needed columns") + **e2e-testing@edd12c6**
      ("eliminate two further memory blowups found while measuring the digest OOM fix"), both independently verified
      this pass as real commits AND ancestors of `origin/live-defi-rollout` (`git cat-file -e` +
      `git merge-base --is-ancestor` in the `e2e-testing` clone). That work landed exactly this todo's literal ask
      (column-restricted `read_manifest_index` + non-expanding aggregation) plus two further measured OOM drivers; real
      5-AG digest run completes at peak RSS ≈ 11.8GiB. The residual "get below the ~4–8Gi aspiration" is NOT this todo —
      it is batch2's own follow-on `[PERF] P3`, which stays open there. No `assigned_vm` change: this is a
      stale-checkbox citation fix, not a reclassification.

## Later-surfaced self-healing deployment residuals (2026-06-23/24, still open)

- [x] ✅ [INFRA] P1. **SCHEDULED consolidator asset_group guard — deliver via MTDS image (in flight 2026-06-23).**
      **VERIFIED 2026-08-09 (slot-8), all 3 stated Done-when parts confirmed live** — the original build id `beb0b08e`
      has aged out of Cloud Build's list retention, but the plan's own allowance ("or a fresher one has since landed")
      covers this: `market-tick-data-service@81dbe37` (the `af5f6c1e`→`3f2b47f2` digest-bump commit) is a confirmed
      ancestor (`git merge-base --is-ancestor 81dbe37 HEAD` → true) of every build since, and the current Dockerfile pin
      has advanced further still (`bca66133...`, i.e. past `3f2b47f2` — the guard has been baked into every
      `market-tick-data-service:latest` build for weeks). (a) build SUCCESS: build
      `393127d5-b5f6-4a4e-9543-b1382e43eca2` (region `asia-northeast1`, commit `7f699fc`) SUCCESS, finished
      2026-08-09T16:36:19Z, pushing the current `:latest` tag (digest `sha256:da82576a...`) — plus 10+ other SUCCESS
      builds earlier the same day. (b) digest differs from pre-bump `af5f6c1e`: confirmed — every digest observed today
      (`sha256:90a1c00e...`, `sha256:da82576a...`, etc.) is unrelated to the pre-bump base. (c) one consolidator
      execution exit 0 on the new image: `uts-prod-manifest-consolidator-instruments-defi-pt6xw` completed
      `2026-08-09T16:00:56Z` with `completionStatus: EXECUTION_SUCCEEDED`, running image digest `sha256:90a1c00e...`
      built from commit `e24199d` — confirmed a descendant of the guard-bump commit
      (`git merge-base --is-ancestor 81dbe37 e24199d` → true). Bonus finding: Cloud Run Jobs re-resolve the `:latest`
      tag to a fresh digest AT EACH EXECUTION (not pinned at job-deploy time) — confirmed because that execution ran a
      digest from a 13:22 build, not whatever was `:latest` when the job spec was last updated — so the guard has been
      live in every consolidator run since the ordinary build pipeline first carried it past `81dbe37`, not just a
      one-off manual verification. — market-tick-data-service (no code change — verification only) Evidence:
      cloudbuild=393127d5-b5f6-4a4e-9543-b1382e43eca2

- **Follow-up (tracked below)**: the e2e-audit Cloud Run image should be rebuilt from clean LDR so the daily reprobe
  cron runs with all 5 hooks wired (auto-flip is proof-gated → safely no-ops on the current image for tradfi/prediction,
  which both return reached_source=False, so this is a correctness-completeness rebuild, not an outage).
- [ ] [INFRA] P2. **Rebuild e2e-audit:latest from clean LDR** so the daily reprobe cron loads all 5 per-AG hooks
      (currently the image predates `e2e-testing@5db3860`; tradfi/prediction hooks return reached_source=False so the
      missing load is a no-op for them today, but a defi/cefi/sports hook update needs the rebuild to take effect).
      Reuse the `cloudbuild-e2e-audit.yaml` build→smoke→push from the IMAGE-GAP-CLOSED run. — e2e-testing,
      deployment-service

- [x] ✅ [CODE] P1. **Package the self-heal actuators (+ launchers) into the runtime image** so the `auto_recover` tier
      can actually ACTUATE a relaunch from the Cloud Run monitors —
      **deployment-api@a01e2a5bb0274ec7d45d8966a6fe8c57a1854435** (QG-green, sentinel-verified before commit).
      **Correction to this todo's own repo attribution**: the actual runtime host is `deployment-api` (its Dockerfile
      vendors `deployment-service` at build time via `_deployment-service/` + `--no-deps`, confirmed against
      `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s
      `data_pipeline_monitor_image = ".../deployment-api:latest"`), NOT `deployment-service`'s own image (which already
      shipped the whole `scripts/` dir and was never the gap). `scripts.recovery` (the import-probe half) was ALREADY
      fixed in an earlier incident (`heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md`) — that
      fix's `COPY _deployment-service/scripts/vm/vm_zombie_watchdog.py ...` only shipped ONE file from `scripts/vm/`, so
      `RelaunchBackfillVm`/`RelaunchStalledVm` (which subprocess-exec `scripts/vm/launch-*.sh` at ACTUATION time, not
      import time) stayed dead even after `_ACTUATORS_AVAILABLE` went green — every real `auto_recover` relaunch hit
      `FileNotFoundError` internally (caught, degrading to `file_issue`, so it never crashed — it just silently never
      actually relaunched). Fixed by COPYing the whole `scripts/vm/` directory (mirrors the `scripts/recovery/`
      convention already there) instead of one file — structural, no manual Dockerfile edit needed for future launchers.
      Regression test extended: `deployment-api/tests/unit/test_dockerfile_zombie_watchdog_packaging.py`
      (Dockerfile-text-parsing guard, asserts the COPY source is the directory root, not a single filename, and asserts
      the two COPY blocks stay adjacent).

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

## Progress Log

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; re-checked the parked conflict -- it has RESOLVED:
  batch2's `[PERF] P2` execution vehicle LANDED (e2e-testing@5d7f53a + @edd12c6, both verified ancestors of LDR) so this
  doc's twin todo was flipped `[x]` as KEEP-NA-STALE, open todos 7 -> 6. Doc STAYS NA (remaining 6 are
  image-packaging/infra-delivery and a stretch item)): RECLASSIFY candidate PARKED (conflict) — stays KEEP-NA —
  `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` carries an OPEN `[PERF] P2` that is a near-verbatim
  duplicate of this doc's own digest-memory-antipattern todo (same file, same column-restriction fix, cites this doc as
  Source). Flipping would dispatch a duplicate.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: refreshed context_scope (6 entries) -- added the alerts registry
  YAML + the e2e-audit `_dp_common.py` source the P1 escalation-issue todo directly targets.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **2026-08-06**: shipped the P1 self-heal actuator packaging todo —
  `deployment-api@a01e2a5bb0274ec7d45d8966a6fe8c57a1854435` (QG-green). Investigation found the actual gap was narrower
  than this todo's original framing: `scripts.recovery` (the import-probe half) was already fixed off a different
  incident (`heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md`); the residual piece was that
  fix's own `scripts/vm/` COPY only shipping `vm_zombie_watchdog.py` (one file), leaving every `launch-*.sh` launcher
  the relaunch actuators subprocess-exec at actuation time absent from the image. Fixed by COPYing the whole
  `scripts/vm/` directory. Repo attribution corrected in the todo itself: the runtime host is `deployment-api`, not
  `deployment-service` (deployment-service's own image already had full `scripts/` — never the gap).
- **context-scout 2026-08-07**: re-verified context_scope, no change needed (6 entries).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — fresh read of the 5 open todos: 1 is
  dirty-dep-quickmerge-blocked (the e2e half of `file_escalation_issue`, gated on peer `strategy-service` WIP clearing);
  2 are in-flight/verification deploy items (consolidator asset_group guard via MTDS image; rebuild `e2e-audit:latest`
  from clean LDR — the latter reads close to AO-eligible on its own, flagging as a MISCLASSIFIED_LIKELY_AO_ELIGIBLE
  candidate for a future pass); 1 is a bounded registry-mode flip gated on confirming each escalation tier is actually
  wired; 1 is an explicit `(stretch)` design item with no forcing function. Mixed doc, stays NA.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09**: extracted 3 of the 5 remaining open items to
  [`cross_cutting_satellite_ao_dispatch_batch9_2026_08_09.md`](/plans/active/cross_cutting_satellite_ao_dispatch_batch9_2026_08_09.md)
  (+ gated finalize twin): the e2e `file_escalation_issue` half (now unblocked by today's D16 all-repos dirty-deps
  direct-push carve-out ruling, 2026-08-08 — a worker can now direct-push past the peer-`strategy-service` dirty-dep
  block instead of waiting), the `e2e-audit:latest` rebuild (already flagged 2026-08-07 above as
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE, never actioned until now), and the consolidator asset_group-guard MTDS-image
  verify+flip (has a fully mechanical Done-when). The remaining 2 open items (registry-mode flip gated on tier-by-tier
  confirmation; the explicit `(stretch)` launch-spec-persist item) are NOT extracted — genuine
  dependency/no-forcing-function gates the D16/IAM/credential precedents don't touch. Doc stays `assigned_vm: NA`
  (mixed, 2 genuinely-gated items remain). Source checkboxes for the 3 extracted items stay open here until batch 9's
  finalize twin reconciles them.
