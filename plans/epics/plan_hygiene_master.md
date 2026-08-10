---
doc_type: epic
title: Plan hygiene — continuous format + integrity + alignment enforcement
summary:
  L5 epic owning continuous plan-corpus hygiene — the check scripts (todo-regression, frontmatter, line-caps,
  codex-refs, archive-candidates, estimate-sanity, superseded-in-active), run_hygiene_sweep.sh + active-plan-inventory
  regen, the 05:00 UTC Cloud Run cron, pre-push hooks, and the codex-alignment audit that catches semantic plan↔codex
  drift.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, frontmatter, scripts, quality-gates, ssot-audit, runbook]
related: [/plans/epics/agent_operating_framework_master.md, /plans/epics/README.md]
created: 2026-05-21
name: plan_hygiene_master
tier: L5
priority: P1
assigned_vm: NA # corrected 2026-08-06 (operator ruling during /plan-reconcile ao, generalising the 2026-08-02 § 2e ruling on plan_reconcile_parked_operator_decisions_2026_08_02.md); PLAN_FORMAT.md:204 — NA is the expected value on every current epic. (was: planning)
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../active/codex_vs_repo_docs_ssot_audit_2026_06_01.md
  - ../active/codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md
  - ../active/infra_satellite_ao_dispatch_batch11_2026_08_09.md
  - ../active/infra_satellite_ao_dispatch_batch11_finalize_2026_08_09.md
  - ../active/june_2026_vintage_audit_findings_2026_07_27.md
cadence: daily-cron + on-demand
locked_by: live-defi-rollout
locked_since: 2026-05-21
last_updated: 2026-07-12 # was 2026-05-23 — stale vs newer body entries; corrected 2026-07-12 (finding 326, §A2 B-queue ruling)
---

# Plan Hygiene Master

Routine maintenance of `plans/active/` and `plans/epics/` run by Ikenna and Harsh on the planning VM. Prevents the
recurring failure mode where agent refactors silently collapse todos, leave orphaned plans, or let the plan corpus drift
from codex.

**Why this epic exists**: this sweep has been done manually 5+ times. Each time it surfaces 50-100 lost todos, stale
frontmatter, broken codex refs, and orphaned plans. Automating the checks and making the runbook a standard daily step
removes the manual cost and catches regressions before they compound.

## Codex SSOTs

> **[DONE 2026-05-22]** Group D audit: all referenced docs verified; `assigned_vm` + `tier` added to required epic
> frontmatter in `plan-hygiene.md` (was missing vs CLAUDE.md).

| Doc                                                             | Owns                                                                                                                                                                                                            |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/codex/11-project-management/plan-hygiene.md`                  | Scripts, runbook, cron — canonical SSOT for hygiene tooling; required frontmatter field lists                                                                                                                   |
| `/codex/11-project-management/active-plan-inventory-tracker.md` | Active plan inventory regenerator (`regenerate_active_plan_inventory.py`); orphan check                                                                                                                         |
| `/codex/11-project-management/issue-doc-lifecycle.md`           | Issue doc state machine; archive trigger conditions                                                                                                                                                             |
| `plans/epics/README.md`                                         | Epic-flow SSOT — 23 epics × 6 tiers (registry regenerated 2026-07-12; was: "19 epics × 5 tiers × 10-VM topology" — the 10-VM model is SUPERSEDED by single-VM role dispatch; finding 10004, §A2 B-queue ruling) |
| `plans/PLAN_FORMAT.md`                                          | Plan format; Cursor checkboxes; required todo syntax                                                                                                                                                            |

---

## Phase 1 — Core scripts (tooling that makes everything else automatable)

- [x] ✅ [SCRIPT] P0. `scripts/plan-hygiene/check_todo_regression.sh` — compare every `plans/active/*.md` `^- \[ \]`
      count vs `origin/live-defi-rollout` baseline; exit 1 if any plan lost open todos. Wire as pre-push hook + optional
      QG step. **Root-cause fix for the todo-collapse failure mode.** (PM@a85f151e9)
- [x] ✅ [SCRIPT] P0. `scripts/plan-hygiene/check_frontmatter.sh` — for every `plans/active/*.md` + `plans/epics/*.md`:
      assert `---` on own first line; required fields present (`parent_epic` for plans, `name` for epics); deprecated
      fields absent (`slug`, `type`, `deadline`, `owner`, `asset_group`, `horizon`); `estimate_*` fields numeric. Exit 1
      on any violation, print file + field. (PM@a85f151e9)
- [x] ✅ [SCRIPT] P1. `scripts/plan-hygiene/check_line_caps.sh` — soft-warn >500L, hard-fail >1000L. Umbrella plans with
      `locked_by` AND >247 todos are exempt (writegate pattern). Print sorted table of offenders. (PM@a85f151e9)
- [x] ✅ [SCRIPT] P1. `scripts/plan-hygiene/check_codex_refs.sh` — grep all `codex/...` paths cited in active plans;
      resolve relative to workspace root; report broken refs (file moved, renamed, or deleted). (PM@a85f151e9)
- [x] ✅ [SCRIPT] P1. `scripts/plan-hygiene/check_archive_candidates.sh` — find plans where `^- \[ \]` count == 0 AND
      all `^- \[x\]` > 0; print candidates with todo counts. Does not archive — outputs a list for operator review.
      (PM@a85f151e9) — **UPGRADED 2026-07-29**: was purely informational and missed `plans/active/issues/` + used
      non-portable `grep -P` (silently blind outside an interactive PCRE-aliased shell — every non-interactive run,
      incl. CI/prek/cron, saw ~0 candidates regardless of the real corpus). Now scans both dirs with portable POSIX ERE
      and is a real shrinking-ratchet hard gate (`archive_candidates_baseline.yaml`), same shape as
      `check_terminal_status_archived.py`. See `/plans/archive/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md`'s
      Progress Log for the investigation.
- [x] ✅ [SCRIPT] P2. `scripts/plan-hygiene/check_estimate_sanity.sh` — verify `estimate_calibrated_ai_days` ≈
      `estimate_baseline_ai_days × multiplier` for the declared `estimate_class` (refactor 0.4×, design 0.6×, infra
      0.8×, brand-new 1.0×, research 1.2×). Flag >20% drift as typos. (PM@a85f151e9)
- [x] ✅ [SCRIPT] P2. `scripts/plan-hygiene/check_superseded_in_active.sh` — grep `plans/active/` for filenames or body
      text containing `SUPERSEDED`; those plans should be in `plans/archive/`. (PM@a85f151e9)

## Phase 2 — Runbook (what Ikenna and Harsh run daily on the planning VM)

- [x] ✅ [SCRIPT] P0. `scripts/plan-hygiene/run_hygiene_sweep.sh` — orchestrates all Phase 1 checks in sequence; prints
      a per-check PASS/FAIL table; exits 0 only if all hard checks pass. Soft checks (line caps, estimates) print
      warnings but don't fail. Output is human-readable and agent-parseable. (PM@a85f151e9)
- [x] ✅ [SCRIPT] P0. `scripts/plan-hygiene/run_hygiene_sweep.sh` — also runs
      `python3 scripts/plans/regenerate_active_plan_inventory.py` at end so the master plan auto-inventory is always
      fresh after a sweep. (PM@a85f151e9)
- [x] ✅ DEFERRED-SUPERSEDED [SCRIPT] P1. Wire `run_hygiene_sweep.sh` into both `ikenna_orchestrator/LEDGER.md` and
      `harsh_orchestrator/LEDGER.md` as a **morning boot step** — superseded by Phase 3 Cloud Run cron approach; LEDGER
      boot step is optional since cron runs at 05:00 UTC before work day begins. (PM@a85f151e9)

## Phase 3 — Cron on planning VM

- [x] ✅ [SCRIPT] P1. Add `run_hygiene_sweep.sh` to planning-VM cron: `0 5 * * *` UTC. Implemented as Cloud Run Job
      `uts-prod-plan-hygiene-sweep` + Cloud Scheduler. Failures append `## [hygiene-cron]` notification to both
      orchestrator inboxes. (deployment-service@5f4eb6b + PM@a85f151e9) **⚠️ 2026-07-11 correction**: the job silently
      failed exit(1)/zero-stdout for 8 consecutive days (2026-06-12→2026-06-19), dying BEFORE its own
      `## [hygiene-cron]` failure-notification path could fire — so the notification claim above was never proven under
      a real failure. It self-recovered and has run green daily 2026-06-20→2026-07-11 (verified via
      `gcloud run jobs executions list`, asia-northeast1): current monitoring IS operational, but the
      failure-notification path remains unverified. Retirement in favour of the central-VM reconciler is tracked in
      `plans/archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md`. Synced per
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` (finding 227).
- [x] ✅ [SCRIPT] P2. Added as `deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf` (adjacent to
      `orphan_ping_audit_scheduler.tf`). Entrypoint: `scripts/plan-hygiene/cron_hygiene_sweep_entrypoint.sh`. Reuses
      `t1_batch_sa` + `GH_PAT` IAM binding. (deployment-service@5f4eb6b) **RETIRED 2026-07-28** (RULE-11
      prove-then-retire, operator approval `june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED #21): the Cloud
      Run job + Cloud Scheduler deleted live, `hygiene_sweep_scheduler.tf` + both repos' copies of
      `cron_hygiene_sweep_entrypoint.sh` deleted, superseded by the daily deep `plan-reconciler` agent (01:00 UTC,
      central orchestrator VM). Full record: `/codex/11-project-management/plan-hygiene.md` § "Daily deep reconciler".

## Phase 4 — Codex alignment audit (agent work)

> Script checks (Phase 1-3) are blind to SEMANTIC drift — a plan can pass all formatting checks but reference a codex
> doc that contradicts what it says to do. That requires agent judgment.

- [x] ✅ [AGENT] P1. Spawn a read-only agent against `plans/active/` + `codex/`: for each plan, verify the codex SSOTs
      it cites (a) exist, (b) still describe the same pattern the plan's todos assume. Flag deviations for operator
      review. Output: `plans/active/issues/codex_alignment_deviations_<date>.md`. — Result: CLEAN. 1 broken ref (planned
      future doc, not a regression); 0 semantic deviations across 8 plans with open todos × codex refs.
      `plans/archive/issues/codex_alignment_deviations_2026_06_25.md` — PM@e8e1f189f (slot-1)
- [x] ✅ [AGENT] P2. For each flagged deviation: determine whether the plan is stale (codex evolved, plan didn't) or the
      codex is incomplete (plan captured a rule change that wasn't propagated to codex). Propose targeted codex augments
      or plan updates. — N/A: P1 returned 0 semantic deviations; no follow-up augments needed. (PM@slot-1)
- [x] ✅ [SCRIPT] P2. `scripts/plan-hygiene/check_codex_refs.sh` — mechanical subset: grep all `codex/...` path strings
      in active plans; verify each file exists at that path. Catches renames/deletes but not semantic drift. Runnable as
      a soft check in `run_hygiene_sweep.sh`. — unified-trading-pm@bf6d2a77a (already shipped + wired)

## Phase 5 — Pre-push hook (prevent regressions at commit time)

- [x] ✅ [SCRIPT] P1. `scripts/plan-hygiene/install_hooks.sh` — installs `check_todo_regression.sh` +
      `check_frontmatter.sh` as `.git/hooks/pre-push` in the `unified-trading-pm` repo. Agents call this once after
      workspace setup. (PM@a85f151e9)
- [x] ✅ [SCRIPT] P2. Document in `/codex/11-project-management/active-plan-inventory-tracker.md` § "Pre-push hygiene
      hooks" — how to install, what they check, how to bypass for emergency pushes (`SKIP_HYGIENE=1 git push`). —
      unified-trading-pm@HEAD (this session)

## Completed wrapper plans

### [`plan_hygiene_automation_2026_05_21`](../archive/2026_05/plan_hygiene_automation_2026_05_21.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-6 all complete: all 10 check scripts + `run_hygiene_sweep.sh` +
`install_hooks.sh` + `fix_frontmatter.py` + Cloud Run Job + Cloud Scheduler Terraform +
`cron_hygiene_sweep_entrypoint.sh`. · **estimate**: 5.6 cal AI-days (class: brand-new)

### [`codex_plan_audit_differential_2026_05_22`](../archive/2026_05/codex_plan_audit_differential_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phase 1+2+3 all complete: broken-ref scan (0 refs), codex SSOT audit (23 plans
classified), L0-L2 epic SSOT pointers added, `post-May-23` markers cleaned (0 stale), `codex-audit-playbook.md` stub
written. · **estimate**: 2.4 cal AI-days (class: brand-new)

## Findings — 2026-06-01 cross-plan deviation sweep (slot-1)

Surfaced by a plan-hygiene + cross-plan-deviation pass (sweep green; 2 frontmatter + 8 todo-format hard failures fixed
in PM@6a1d2e466). Corpus is largely well-disciplined — vocabulary (`asset_group`/`source`/removed-providers/URDI) clean,
SSOT pointers unbroken, and contentious technical decisions (source auto-stamp, custody staging, promote targets,
single-walk discipline) consistently aligned. Residual items:

- [x] ✅ [CLAUDE-MD] P2. **Manifest v9 framing generalised** — CLAUDE.md documented v9 only under the TradFi-source
      bullet while 11 active `*_manifest_canonicalisation` plans make v9 the workspace-wide canonical target. Added a
      general "current canonical schema = v9, all asset groups" line. (CLAUDE.md this session.)
- [x] ✅ [PLAN] P2. **2 RESOLVED issue docs archived** — `quality_gates_sh_missing_sentinel_write_2026_05_29` +
      `check_staging_lock_ruleset_hygiene_2026_05_29` both self-declared `status: RESOLVED` + "Issue archives." with 0
      open todos; moved to `plans/archive/2026_06/` this session (issue-doc-lifecycle HARD RULE).
- [ ] [PLAN] P1. **Stale 2026-05-23 deadline framing** (today is past the milestone) —
      `master_to_live_defi_2026_05_23.md` + ~10 cross-refs (INDEX, `aws_cloud_toggle_and_backfill_parity`,
      `human_work_backlog`) still use future-tense "live by 2026-05-23 / pre-/post-cutover". Slot-1 owns the master-plan
      refresh: re-date to actual status or archive if the cutover executed. (Master plan was dirty/in-flight at sweep
      time — coordinate before editing.)
- [x] ✅ [PLAN] P2. **DEFERRED items with placeholder successors** — resolved per-item audit 2026-06-25: -
      `tradfi_cfe_vx_futures_<date>` → **RESOLVED/MOOT**: VX futures via Databento XCBF.PITCH shipped + is
      CLAUDE.md-canonical (2026-06-24); `tradfi_datasource_closeout_krx_yahoo_parity_2026_06_24.md` 100% done. Named
      successor plan not needed. - `tradfi_massive_live_ws_<TBD>` → **BLOCKED-OPERATOR-DECISION**: massive is now
      SOURCE*PRIORITY[1] (fallback, 2026-06-24 operator decision); live massive WS deprioritised until operator chooses
      to invest in it. Tracked in `tradfi_massive_dual_source_2026_05_28.md` as an out-of-scope deferred item; no
      separate plan needed until the operator re-prioritises. - `cleanup_v1_quality_gates_workflows*<TBD>`→ tracked
      in`cicd_consolidated_remaining_2026_06_24.md` scope (the v1 workflow retirement is part of the broader CI/CD
      consolidation). -`mdps_pure_polars_migration`→ **RESOLVED/SUPERSEDED**: active plan
      `mdps_adapter_protocol_pandas_to_polars_2026_06_21.md`is the canonical
      successor. -`features_registry_status_versioning`→ **RESOLVED**: archived in`plans/archive/2026_06/`.

## Deferred work — migrated from archived plans

- [x] ✅ [AGENT] P2. **MIGRATED FROM: plans/archive/codex_refactor_2026_05_08.plan.md Phase B.4-bis** — Expand the
      highest-leverage codex stub docs (unexpanded forwarder stubs with deep-link anchors). Priority order by
      incoming-ref count: `testing.md` (4 incoming refs — already substantive at 7473 bytes),
      `service-structure-standards.md` (3 refs), `sub-agent-workflow.md` (2 refs), then others. Each stub is a forwarder
      that points to a canonical home; the expansion makes the stub a substantive SSOT so deep-links resolve to real
      content. — unified-trading-pm@HEAD (this session: service-structure-standards.md + sub-agent-workflow.md +
      cursor-rules-system.md expanded; remaining single-ref stubs are low-priority forwarders)

## Temporary states + canonical follow-up plans

- Phase 1-3 + 5 (P1+P2): shipped. No temporary states.
- Phase 4 (codex alignment agent work): open P1/P2 items remain — low-priority ongoing; no blocking successor plan
  needed.
- Phase 5 P2 (hook documentation in codex): shipped — `/codex/11-project-management/active-plan-inventory-tracker.md` §
  "Pre-push hygiene hooks" (corrected 2026-07-15, plan-reconcile: this summary was stale against the Phase 5 P2 todo
  already checked off above).

## Assigned active plans

_5 active plans declare `parent_epic: plan_hygiene_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority)_

## P1 — important; post-current-gate

### [`codex_vs_repo_docs_ssot_audit_2026_06_01`](../active/codex_vs_repo_docs_ssot_audit_2026_06_01.md)

**status**: active · **estimate**: 3.2 cal AI-days (class: refactor) **title**: Codex-vs-repo-docs SSOT audit +
consolidation (all active repos)

### [`june_2026_vintage_audit_findings_2026_07_27`](../active/june_2026_vintage_audit_findings_2026_07_27.md)

**status**: active · **estimate**: 2 cal AI-days (class: refactor) **title**: June-2026 vintage audit findings — bugs,
archives, migrations, rehomes, operator-gate queue

## P2 — useful; opportunistic

### [`codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27`](../active/codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md)

**status**: active · **estimate**: 0.2 cal AI-days (class: infra) **title**: >-

### [`infra_satellite_ao_dispatch_batch11_2026_08_09`](../active/infra_satellite_ao_dispatch_batch11_2026_08_09.md)

**status**: active · **estimate**: 0.08 cal AI-days (class: refactor) **title**: Infra satellite AO batch 11 —
na-eligibility-audit body-hash blind to context-scout's Progress Log marker line

### [`infra_satellite_ao_dispatch_batch11_finalize_2026_08_09`](../active/infra_satellite_ao_dispatch_batch11_finalize_2026_08_09.md)

**status**: active · **estimate**: 0.06 cal AI-days (class: refactor) **title**: Infra satellite AO dispatch batch 11 —
finalize (reconcile source-doc checkboxes + archive)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
