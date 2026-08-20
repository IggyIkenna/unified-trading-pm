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
    /plans/archive/issues/plan_reconciler_findings_ci_2026_08_16.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: ci_master
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
    /plans/archive/issues/plan_reconciler_findings_ci_2026_08_16.md,
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

- [x] ✅ [REVIEW] P2. Archive
      `plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md` — 0
      open todos, `archive_exempt: true` since 2026-08-16 (plan_reconciler Phase -1), independently re-confirmed
      2026-08-18 (na-eligibility-audit: every todo across both dated Update sections `[x]`). Re-confirmed 0 open
      todos this pass; moved to `plans/archive/issues/`, `superseded_by: /codex/15-runbooks/ci-daily-health.md`
      (the daily-cron move off the blocking Pass-1 path is already documented there). Referrers in
      `ci_satellite_ao_dispatch_batch13_2026_08_13.md` and `ci_satellite_ao_dispatch_batch15_2026_08_16.md`
      repointed at codex.

- [x] ✅ [REVIEW] P2. Archive
      `plans/active/issues/deployment_service_basedpyright_ratchet_exceeded_sports_trigger_2026_08_08.md` — sole
      todo `[x]` RESOLVED, shipped `deployment-service@71871454` (ratchet 1295 -> 1259, live-confirmed in
      `scripts/quality-gates.sh:134`), independently re-confirmed by `ci_satellite_ao_dispatch_batch13`'s fresh
      standalone basedpyright run (0 errors on the 4 named files). `archive_exempt: true` present; the 2026-08-08
      conflict-check that originally held this NA (racing a sibling sports_master plan on the same file family) is
      moot now the fix has shipped and been independently re-verified. Moved to `plans/archive/issues/`,
      `superseded_by: /codex/06-coding-standards/quality-gates.md` (pure incident closure, no new contract beyond
      the existing ratchet-only-goes-down rule). Referrer in `ci_satellite_ao_dispatch_batch13_2026_08_13.md`
      repointed at codex.

- [x] ✅ [REVIEW] P2. Archive `plans/active/issues/ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md`
      — both Follow-up items `[x]` DONE with hard evidence (PR #2714 confirmed CLOSED via live `gh pr view`; the
      fleet-wide `inflight_wait` guard-porting item confirmed moot via `ci_satellite_ao_dispatch_batch13`'s
      2026-08-14 reconciliation — zero `inflight_wait`-shaped code exists in the fleet workflow to port). Referrer
      sweep checked: the doomed-run check-runs supersede fix was NOT previously in codex — added to
      `/codex/08-workflows/ci-cd-flow.md` this pass. Moved to `plans/archive/issues/`,
      `superseded_by: /codex/08-workflows/ci-cd-flow.md`. Referrers in `ci_satellite_ao_dispatch_batch13_2026_08_13.md`
      and `ci_satellite_ao_dispatch_batch15_2026_08_16.md` repointed at codex.

- [x] ✅ [REVIEW] P2. Archive `plans/active/issues/semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` —
      0 open todos across the full 555-line doc (Shipped/Verification/both Follow-up regressions/Live verification
      all `[x]`). The one loose end mentioned in the body (e2e-testing `source_dir` misconfig) is already tracked
      in a different active doc (`ibkr_gateway_infra_release_tag_stall_2026_08_11.md`) — do not duplicate a todo
      for it here. The content-based patch-level fallback contract was already documented in
      `/codex/08-workflows/ci-cd-flow.md`; the ~21,000-char GH Actions `run:` block-scalar cap gotcha (bit the
      fleet twice in 24h during this incident) was NOT captured anywhere in codex — added to
      `/codex/05-infrastructure/cicd-setup.md` this pass. Moved to `plans/archive/issues/`,
      `superseded_by: /codex/08-workflows/ci-cd-flow.md`. Referrers in
      `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md`,
      `ci_satellite_ao_dispatch_batch13_2026_08_13.md`, and `ci_satellite_ao_dispatch_batch15_2026_08_16.md`
      repointed at codex.

- [x] ✅ [REVIEW] P2. Archive `plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md` — 0 open todos as of
      this same na-eligibility-audit run's own flip (2026-08-18): MTDS half independently verified fixed via
      `market-tick-data-service@1dbdbb90`'s autouse `conftest.py` fixture, covering both named reproducer tests.
      `archive_exempt: true` added in that same commit. This doc has a long (5+ dated) na-eligibility-audit verdict
      history — the codex-alignment check should confirm nothing in that history needs a durable codex home before
      archiving (skim, don't re-litigate the closed sentinel-hardening/environment-alignment work, which already
      shipped and is referenced from `ci-cd-flow.md`/`quality-gates.md` per this doc's own prior Progress Log).
      Confirmed the sentinel-environment-binding contract is already well-documented across 4 codex docs — no gap.
      Moved to `plans/archive/issues/`, `superseded_by: /codex/06-coding-standards/quality-gates.md`. Referrers in
      `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` (related + context_scope) and
      `post_cutover_silent_assumption_sweep_2026_07_23.md` repointed at codex.

## Progress Log

- **context-scout 2026-08-19**: populated/verified context_scope (2 entries) — first scout pass on this doc; both
  entries (the archival-discipline codex SSOT and the source `plan_reconciler_findings_ci_2026_08_16.md` issue doc)
  confirmed resolving on disk. No source-code paths added — this is a pure archival-ritual sweep over 6 already-done
  docs, matching the process/meta-audit skip-source carve-out.
- **2026-08-18 (na-eligibility-audit, ci tranche, dispatch agt-b10de6)**: carved out this worklist after Phase-1
  classification independently re-confirmed `plan_reconciler_findings_ci_2026_08_16.md`'s own "5 additional docs
  deliberately NOT archived this pass... ready-to-archive worklist" finding, plus found a 6th
  (`qg_sentinel_environment_blind_2026_07_23.md`, closed by this same run). Two prior deferrals (2026-08-16
  plan_reconciler, implicitly this run's own hunters before synthesis) is the exact "audit finds it, defers, never
  gets done" pattern this workspace's meta-skills exist to close — tracking it as real todos rather than a third
  prose mention.

- **2026-08-19T23:1XZ (slot 7, dispatched as review-role, task assigned_role=review)**: Executed the remaining 5
  archival todos (item 1 was already done). Re-confirmed 0 open todos on each of the 5 target docs by a fresh
  full read (not trusting the prior audit markers alone). Codex-alignment check per-doc: 3 of 5 already had their
  durable contract captured (semver squash patch-fallback, sentinel env-binding — both pre-existing); 2 genuine
  gaps found and closed — the `ldr-to-main-promote.yml` doomed-run check-runs supersede fix (added to
  `/codex/08-workflows/ci-cd-flow.md`) and the GH Actions ~21,000-char `run:` block-scalar cap gotcha that bit the
  fleet twice in 24h during the semver-agent incident (added to `/codex/05-infrastructure/cicd-setup.md`). Added
  `status: archived` + `superseded_by` + an archived-banner to each doc (matching item 1's own convention), dropped
  `archive_exempt: true` (moot once archived), `git mv`'d all 5 to flat `plans/archive/issues/` in one commit shaped
  per the ritual's rename-safety rule (plain full-staged commit, no `--only` path-scoping). Corpus-wide referrer
  sweep: grepped every `.md` for the 5 old paths (44 raw hits), narrowed to the 5 active-corpus docs whose
  **structural `related:`/`context_scope:` frontmatter** actually cited an old path (the check
  `check_active_refs_archived_plans.py` enforces — prose citations in archived docs/codex/Progress-Log entries are
  the correct end-state, left untouched) — `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`,
  `post_cutover_silent_assumption_sweep_2026_07_23.md`, `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md`,
  `ci_satellite_ao_dispatch_batch13_2026_08_13.md`, `ci_satellite_ao_dispatch_batch15_2026_08_16.md` — all 5
  repointed at the corresponding codex doc (deduping against an already-present codex citation in the two satellite
  batch plans rather than adding a redundant duplicate entry). Verified `git status --porcelain` shows no dangling
  staged deletion at any old path before committing.
