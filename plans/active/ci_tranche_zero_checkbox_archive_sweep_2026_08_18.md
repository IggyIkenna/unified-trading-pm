---
doc_type: plan
title: ci-tranche zero-checkbox archive sweep — 2026-08-18
summary: >-
  A dedicated archival-ritual sweep for 6 ci-tranche `plans/active/issues/*.md` docs independently confirmed
  zero-open-todos + HARD-evidence-done by two separate audits (`plan_reconciler_findings_ci_2026_08_16.md`'s Phase
  -1 pass identified 5 of the 6 and deliberately deferred archival mechanics as out of scope for that pass; this
  `na-eligibility-audit` run's own Phase-1 hunters + direct verification independently re-confirmed all 5 plus found
  a 6th). Both prior passes explicitly left this as "a clearly-evidenced, ready-to-archive worklist for the next
  full ci-tranche archival sweep" — this plan IS that sweep, tracked as real `- [ ]` todos rather than left as prose
  in either audit's own findings doc a third time.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, archival, plan-hygiene, ao-dispatch, na-audit]
related:
  [
    /plans/active/issues/plan_reconciler_findings_ci_2026_08_16.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.96
assigned_role: review
effort: medium
drift_direction: advance-docs
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/plan_reconciler_findings_ci_2026_08_16.md,
  ]
source: >-
  Carved out by the ci-tranche /na-eligibility-audit run (2026-08-18, dispatch agt-b10de6) from a convergent finding
  across 2 independent audits — never dispatched before now because both prior passes deliberately deferred the
  archival mechanics as out of scope for their own pass, not because anything was still genuinely open.
---

# ci-tranche zero-checkbox archive sweep — 2026-08-18

Each todo below is one doc, already independently confirmed at 0 open `- [ ]` checkboxes with HARD evidence (commit
shas / live re-verification) by at least one prior audit pass — re-confirm the checkbox count yourself before
touching anything (a concurrent commit could theoretically have re-opened one), then run the standard 6-step
archival ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): migrate any DEFERRED prose
into a real todo, add the archived-banner + `superseded_by`, run the codex-alignment check (does this doc's
completion establish a contract codex should reflect — most of these are pure incident-closure, likely no new
contract, but check per-doc, don't skip), grep the whole corpus for the doc's path and repoint every referrer at
codex (never at the archived plan itself), `git mv` to flat `plans/archive/issues/` (all 6 are `doc_type: issue`),
and verify via `git status --porcelain` that the commit didn't drop the rename's delete side. Drop each doc's
`archive_exempt: true` field as part of its own archival commit (moot once archived).

## Todos

- [x] ✅ [REVIEW] P2. Archive `plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md` — 0
      open todos, `archive_exempt: true` since 2026-08-16 (plan_reconciler Phase -1), independently re-confirmed
      2026-08-18 (na-eligibility-audit: all 5 todos `[x]`, `resolved_by:` cites 6 commits across 2 repos). Moved to
      `plans/archive/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md`; durable
      `waitFor`-vs-template-native contract captured in `/codex/08-workflows/ci-cd-flow.md`; the 3 active-corpus
      docs whose `related:`/`context_scope` pointed at the old active path (`ci_satellite_ao_dispatch_batch13`,
      `ci_satellite_ao_dispatch_batch15`, `unified_api_contracts_image_build_gate_template_lag_...2026_08_14`)
      repointed at codex, same commit.

- [ ] [REVIEW] P2. Archive
      `plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md` — 0
      open todos, `archive_exempt: true` since 2026-08-16 (plan_reconciler Phase -1), independently re-confirmed
      2026-08-18 (na-eligibility-audit: every todo across both dated Update sections `[x]`).

- [ ] [REVIEW] P2. Archive
      `plans/active/issues/deployment_service_basedpyright_ratchet_exceeded_sports_trigger_2026_08_08.md` — sole
      todo `[x]` RESOLVED, shipped `deployment-service@71871454` (ratchet 1295 -> 1259, live-confirmed in
      `scripts/quality-gates.sh:134`), independently re-confirmed by `ci_satellite_ao_dispatch_batch13`'s fresh
      standalone basedpyright run (0 errors on the 4 named files). `archive_exempt: true` present; the 2026-08-08
      conflict-check that originally held this NA (racing a sibling sports_master plan on the same file family) is
      moot now the fix has shipped and been independently re-verified.

- [ ] [REVIEW] P2. Archive `plans/active/issues/ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md`
      — both Follow-up items `[x]` DONE with hard evidence (PR #2714 confirmed CLOSED via live `gh pr view`; the
      fleet-wide `inflight_wait` guard-porting item confirmed moot via `ci_satellite_ao_dispatch_batch13`'s
      2026-08-14 reconciliation — zero `inflight_wait`-shaped code exists in the fleet workflow to port). Referrer
      sweep should check the pytest-timeout doc-chain and `ci_satellite_ao_dispatch_batch13` for inbound links.

- [ ] [REVIEW] P2. Archive `plans/active/issues/semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` —
      0 open todos across the full 555-line doc (Shipped/Verification/both Follow-up regressions/Live verification
      all `[x]`). The one loose end mentioned in the body (e2e-testing `source_dir` misconfig) is already tracked
      in a different active doc (`ibkr_gateway_infra_release_tag_stall_2026_08_11.md`) — do not duplicate a todo
      for it here.

- [ ] [REVIEW] P2. Archive `plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md` — 0 open todos as of
      this same na-eligibility-audit run's own flip (2026-08-18): MTDS half independently verified fixed via
      `market-tick-data-service@1dbdbb90`'s autouse `conftest.py` fixture, covering both named reproducer tests.
      `archive_exempt: true` added in that same commit. This doc has a long (5+ dated) na-eligibility-audit verdict
      history — the codex-alignment check should confirm nothing in that history needs a durable codex home before
      archiving (skim, don't re-litigate the closed sentinel-hardening/environment-alignment work, which already
      shipped and is referenced from `ci-cd-flow.md`/`quality-gates.md` per this doc's own prior Progress Log).

## Progress Log

- **2026-08-18 (na-eligibility-audit, ci tranche, dispatch agt-b10de6)**: carved out this worklist after Phase-1
  classification independently re-confirmed `plan_reconciler_findings_ci_2026_08_16.md`'s own "5 additional docs
  deliberately NOT archived this pass... ready-to-archive worklist" finding, plus found a 6th
  (`qg_sentinel_environment_blind_2026_07_23.md`, closed by this same run). Two prior deferrals (2026-08-16
  plan_reconciler, implicitly this run's own hunters before synthesis) is the exact "audit finds it, defers, never
  gets done" pattern this workspace's meta-skills exist to close — tracking it as real todos rather than a third
  prose mention.
