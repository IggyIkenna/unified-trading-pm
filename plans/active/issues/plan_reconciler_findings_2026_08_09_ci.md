---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — ci tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-c80749 (slot 15, 2026-08-09), sharded to the `ci` topic tranche per
  the 2026-08-06 operator ruling (Sun-Fri per-tranche shards, Saturday whole-corpus). Corpus: 59 active+issue docs
  tagged `asset_group: ci` (~1.85MB); 24 (41%) are in the 12h grace window and read-only this run, leaving 35 non-grace
  docs (~1.16MB) as the actionable set. Normative refs (PLAN_FORMAT.md/task_template.md/INDEX.md/ACTIVE_INDEX.md) and
  codex stay in scope per the sharded-run contract.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, ci]
related: []
created: "2026-08-09"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-09"
supersedes:
superseded_by:
resolved_by:
source: "slot 15, plan_reconciler agt-c80749, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_archive_candidates.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-09 (agt-c80749, ci tranche)

## Scope + method

- `TRANCHE=ci` supplied → sharded run over `asset_group: ci` docs only (the 2026-08-06 operator-ruled Sun-Fri
  per-tranche cadence). Normative refs + codex stay in scope per the sharded-run contract even though this is a topic
  shard.
- Corpus: 59 active+issue docs tagged `asset_group: ci` (~1.85MB total).
- Grace set (newest commit <12h old at run start, 2026-08-09T02:54Z): 24 of 59 docs (41%). Read-only context this run.
- Non-grace actionable set: 35 docs (~1.16MB), batched into 5 hunter batches (~235KB each).
- `ci_consolidated_closeout_2026_07_25.md` (the tranche's former epic hub) is already archived
  (`plans/archive/2026_07/`) — `asset_group: ci` is filtered directly per the SKILL's tranche mechanism, no live epic
  hub dependency.
- 3 non-grace ci docs carry `locked_by: live-defi-rollout` (real locks, never auto-archived/unlocked this run):
  `ui_build_warm_cache_2026_06_17.md`, `issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`,
  `issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`.
- **Phase-0 `run_hygiene_sweep.sh --ci --no-regen`** (corpus-wide, read-only): 2 hard failures, neither squarely
  ci-tranche's to fix — noted here rather than blocking this shard's exit gate (Phase 5's "0 hard failures" bar is an
  unsharded-run design; a topic shard cannot fix debt in tranches it doesn't own without stepping on a concurrent
  sibling shard):
  1. **Archive candidates ratchet** (1 candidate vs baseline 0):
     `plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` — a
     `tradfi`-tagged doc, entirely outside `ci` scope. Not touched this run; belongs to the `tradfi` tranche shard.
  2. **Silent-default-effort ratchet** (250 vs baseline 217, +33 corpus-wide): 21 of my 59 ci docs are in the flagged
     population (declare `assigned_role`, no `effort:`/`thinking_tier:`), but this is a **template-level gap**, not a
     per-doc authoring miss — `plans/active/task_template.md` never mentions `effort:`/`thinking_tier:` anywhere in its
     frontmatter guidance, so EVERY tranche's AO-dispatch-batch docs regress this ratchet by design, not just ci's. The
     4 docs created today (`ci_satellite_ao_dispatch_batch7[_finalize]_2026_08_09.md`,
     `ci_satellite_ao_dispatch_batch8[_finalize]_2026_08_09.md`) are ci's marginal contribution to the +33. Filed as a
     systemic recommendation (below) rather than hand-patched per-doc — an arbitrary per-doc tier choice by one tranche
     shard wouldn't fix the template gap other tranches keep hitting.

## Flips verified

1. **`provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md`** — pre-push-strict-quickmerge.sh deletion
   todo. Evidence: `unified-trading-pm@b02ba28c7` (2026-08-06), independently re-verified (file absent, 0 live
   referrers). unified-trading-pm@[batch commit, see Archived below — flip+archive combined].
2. **`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`** — dormant-cascade investigation todo. Same root
   cause as `post_cutover_silent_assumption_sweep_2026_07_23.md` § F2 (orphaned `semver-agent.yml`), live-verified via
   `gh run list` (0 runs 06-30→07-22, continuous 16-42/day since 07-23) + an end-to-end run trace. 4/4 fixed.
   unified-trading-pm@0408d1ad7 (+9eb8cb3e7 fixing a silently-dropped edit, see below).
3. **`post_cutover_silent_assumption_sweep_2026_07_23.md`** F3 todo — half-flip: `cascade-qg-ordering.yml` +
   `sit-gate.yml` slices confirmed done (batch5 todo 6 + live code verify); 24-repo `semver-agent.yml` slice remains
   open, left `- [ ]` per the half-done-item convention. unified-trading-pm@13eb2dc79.

## Archived (verified-done, unlocked, non-grace)

1. **`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`** → `plans/archive/2026_08/issues/`. 0/4 open
   after the flip above, unlocked. unified-trading-pm@0408d1ad7. Referrers repointed:
   `github_actions_operator_gated_followups_2026_07_17.md` (`related:`),
   `assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md` (removed now-moot list entry).
2. **`provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md`** → `plans/archive/2026_08/issues/`. 0/5
   open after the flip above, unlocked. unified-trading-pm@13eb2dc79. Referrer repointed:
   `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` (`related:` + `context_scope:`, 2 instances).
3. **`client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md`** → `plans/archive/2026_08/issues/`. Whole doc
   resolved as MOOT (not via its own proposed 4-step recipe) — independently re-verified live via `gh api` (not just
   trusting the hunter): `notify-slack.yml` 404 on `main`, `main-backmerge-to-ldr.yml` now delegates to
   `unified-trading-ci`'s reusable workflow (structural fix eliminates the whole drift class), 8 consecutive successful
   backmerge runs, PRs #657-669 (13) all MERGED since 2026-08-07. Was a zero-checkbox doc (prose-only recipe, never
   became todos) — resolved rather than converted since the actual fix path differs from what was proposed. Updated the
   standing `zero_checkbox_sweep_all_tranches_2026_07_31.md` register row. unified-trading-pm@6ea4480c5 (+ a fix for a
   silently-dropped edit, see below).

**⚠️ Recurring commit-integrity issue this run**: all 3 archival commits above hit the SAME prek stash-restore race
(content edits silently dropped, working tree looked right, HEAD didn't match — the exact SKILL.md Phase 5.9(c) failure
mode, "git mv reporting (100%) rename similarity is the tell"). Caught via the mandatory verify-at-HEAD check each time
(2 post-hoc, 1 pre-push after adopting a stricter `git diff --cached` pre-commit habit mid-run). All 3 are now confirmed
correct at HEAD. Filed as a P1 tooling finding below — this is a real, reproducible bug in the git-mv-archival-commit
path, not a one-off.

## Contradictions

1. **[P0, FIXED]** `ci_satellite_ao_dispatch_batch1_2026_07_26.md` — stale "STATUS: draft" banner directly contradicting
   `status: active` frontmatter + 42/43 shipped todos (same bug already fixed in its finalize sibling 2026-08-02, never
   propagated back). unified-trading-pm@0408d1ad7.
2. **[P1, ROUTED — see Doc-drift]** `monitoring_control_plane_master_2026_06_10.md` `parent_epic: observability_master`
   vs keyword-heuristic top match `infrastructure_master` — mixed evidence (a plausible 2026-06-10 dual-epic naming
   collision, not simply "heuristic wrong"), recommend operator reconfirmation rather than a mechanical flip.
3. **[P1, FIXED]** `github_actions_operator_gated_followups_2026_07_17.md` — self-contradiction: a 2026-08-07
   context-scout note asserting "18 real open drift issues, not false positives — a live unresolved P0" was reversed by
   a deeper 2026-08-08 investigation earlier in the SAME doc (checker bug + mis-recorded cassette, not live drift) —
   never flagged as superseded. unified-trading-pm@6a0a4e407.
4. **[P1, FIXED]** `github_actions_operator_gated_followups_2026_07_17.md` deferred-table rows 3/4/5 — all stale ("NOT
   DONE"/blocked) against actual state (qg-sentinel mostly resolved; codex staging re-entry now documented at
   `ci-cd-flow.md:169`). unified-trading-pm@6a0a4e407.
5. **[P2, FIXED]** `github_actions_operator_gated_followups_2026_07_17.md:861` — off-by-one, table's own KEEP column
   sums to 109 not the stated 108 (independently re-verified by direct summation). unified-trading-pm@6a0a4e407.
6. **[P2, NOT A CONTRADICTION — dedicated verifier]** ci_pipeline_speed_and_cost_redesign vs pytest_timeout doc's "PM
   public flip" phrase — verified NOT a conflict (different axes: repo-visibility vs runner-placement, 3 distinct dated
   events). Added a superseded-note to ci_pipeline_speed doc regardless since its own text now reads present-tense-wrong
   after a later, unrelated revert. unified-trading-pm@0408d1ad7.
7. **[P1, CONFIRMED + FIXED — dedicated verifier]** digest_drift_sweep vs post_cutover F2 — same root cause, live
   `gh run list` + end-to-end run trace confirms the cascade resumed 2026-07-23. See Flips verified #2.
8. Minor/cosmetic (all FIXED in the github_actions batch commit): malformed `~~`/`**` marker nesting (line 538); 41
   lines of corrupted 500+ char leading whitespace (707-749) — content preserved, was silently at risk of markdown
   code-block misrender.

## Doc-drift

1. **`monitoring_control_plane_master_2026_06_10.md` parent_epic** — see Contradictions #2. Routed to operator (genuine
   authority/preference call, not evidence-settleable — SKILL.md Modes § Calibration).
2. **`orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` codex-alignment DRIFT** — cites
   `/codex/07-security/self-hosted-runner-security-posture.md`
   (`authoritative_for: self-hosted runner ambient-identity posture, glue-runner credential-exposure facts`), but that
   codex doc doesn't mention this issue's 5×-recurring, now-operator-ruled (2026-08-08, option b) failure mode at all —
   worse, the codex doc's own STEP 2b design invariant ("drops per-job `auth` steps because ambient ADC is there") is
   directly violated by `cloud-build-router.yml` and sibling glue workflows, which is the actual root cause of the 5
   outages. Codex/SSOT edits require an explicit operator ruling before an agent applies them (SKILL.md Phase 5) — filed
   as a todo below, not auto-fixed.
3. **`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`** (now archived)
   `parent_epic: deployment_and_user_management_master` — inconsistent with 4 sibling ci-cd-token docs in the same batch
   all using `infrastructure_master`, and doesn't match the doc's own `asset_group: [ci]`. Noted, not mechanically
   flipped (parent_epic reassignment isn't in SKILL.md's auto-fix table — a categorization call, not a provable fact).

## Hygiene fixes

- `github_actions_operator_gated_followups_2026_07_17.md` — added a close-proximity SSOT citation for a pre-existing
  unsourced "operator ruling 2026-08-08" mention (corpus-wide `check_plan_operator_ruling_evidence.py` gate,
  pre-existing debt, blocked my unrelated commit).
- `post_cutover_silent_assumption_sweep_2026_07_23.md` — same class, 6 pre-existing unsourced "operator ruling" mentions
  (all part of the same "Option B formally retired 2026-08-08" decision family), cited to
  `github_actions_operator_gated_followups_2026_07_17.md` § "Cost ruling 2026-07-23" + codex.
- `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` — 1 pre-existing unsourced mention; no
  separate durable doc exists for this specific same-session ruling, noted honestly rather than fabricating a pointer.
- `assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md` — corrected "10 more" → "8 more" in its own enumeration
  (2 entries now moot: 1 pre-existing archived doc the moved-doc-referrer hunter found, 1 archived this run).
- **AO-dispatch-readiness (task_template.md finding L / SKILL.md hunter 5)** — 3 `assigned_vm: planning` docs had
  load-bearing todo content stranded past the first physical line (invisible to `regen_backlog_from_plan.py`'s
  `_parse_open_todos`): `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` (both todos, critical qualifiers
  omitted), `ci_satellite_ao_dispatch_batch4_2026_07_31.md` (sole open todo, target doc name hidden mid-bold-wrap),
  `ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md` (todo 1 omitted a distinct sub-instruction entirely, todo 3
  truncated mid-citation with the entire 6-step procedure continuation-only). All rewritten so the complete instruction
  fits on line 1. unified-trading-pm@28e6b883c.

## Filed

1. **`BLK-987241fb`** (ASK, answered async) — `monitoring_control_plane_master_2026_06_10.md` `parent_epic` question
   (observability_master vs infrastructure_master — see Contradictions #2 / Doc-drift #1 for full evidence). Options A
   (reassign, [WORKER REC]) / B (keep as-is) / C (split). `can_continue: true`.
2. **P1 tooling bug — prek stash-restore silently drops staged content on `git mv` archival commits.** Reproduced 3/3
   times this session (`digest_drift_sweep`, `provenance_gate_override`, `client_reporting_api_promote_wedge` archival
   commits): a commit combining a `git mv` with content edits (status/banner) lands with the RENAME but not the content
   — "Restored unstaged changes from `<patch>`" appears to restore a STALE pre-edit snapshot over the staged version.
   Symptom matches SKILL.md Phase 5.9(c) exactly ("git mv reporting (100%) rename similarity is the tell"). Caught every
   time via mandatory verify-at-HEAD (`diff <(git show HEAD:<path>) <path>`), never silently shipped wrong, but costs a
   full extra commit+push cycle each time and would silently corrupt an archival for any agent that skips the
   verify-at-HEAD step. Needs investigation in `agent-orchestrator`/pre-commit hook infra (prek's stash handling around
   renames) — outside a plan-doc reconciliation pass's own remit to fix.
   - [ ] [BACKEND] P1. Root-cause why prek's "Restored unstaged changes from patch" step drops staged content
         specifically on commits combining a `git mv` with a content edit to the moved file — reproduce with
         `git mv <f> <new>; <edit new>; git add <new>; git commit` on a throwaway branch, inspect the `.patch` file prek
         generates immediately before the drop to confirm it's stashing a stale (pre-edit) tree state. Fix in the prek
         hook config or upstream prek itself. Done-when: 10 consecutive git-mv+edit commits in a row land correctly at
         HEAD with zero manual re-fix commits needed.
3. **Systemic gap — `plans/active/task_template.md` never mentions `effort:`/`thinking_tier:` anywhere in its
   frontmatter guidance**, so every tranche's AO-dispatch-batch docs silently regress the corpus-wide
   `check_effort_signal_ratchet.py` gate by design (250 vs baseline 217 corpus-wide as of this run; ci's marginal
   contribution: 4 docs created today). See Scope+method above for full detail.
   - [ ] [DOC] P2. Add `effort:`/`thinking_tier:` to `plans/active/task_template.md`'s AO-dispatched frontmatter block
         (§2, alongside `assigned_vm: planning`), with a one-line note on when the role-generic default is fine vs when
         to declare explicitly (mirrors CLAUDE.md's "every `assigned_vm: planning` plan defaults to `effort: max`" + the
         2026-07-22 todo-count-derivation ruling). Done-when: a fresh AO-dispatch-batch doc authored from the template
         no longer silently regresses `check_effort_signal_ratchet.py`.
4. **Codex-alignment drift** — `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` cites
   `/codex/07-security/self-hosted-runner-security-posture.md`
   (`authoritative_for: self-hosted runner ambient-identity posture, glue-runner credential-exposure facts`), but that
   codex doc doesn't document this issue's 5×-recurring, now-operator-ruled (2026-08-08, option b) failure mode at all —
   worse, `cloud-build-router.yml` and sibling glue workflows directly violate the codex doc's own STEP 2b design
   invariant ("drops per-job `auth` steps because ambient ADC is there"), which is the actual root cause of the 5
   outages. Per SKILL.md Phase 5, a codex/SSOT edit is only ever applied after an explicit operator ruling — filed, not
   auto-fixed.
   - [ ] [DOCS] P2. After operator ruling: update `/codex/07-security/self-hosted-runner-security-posture.md` to (a)
         document the WIF-job-auth-overwrites-shared-active-account failure mode and its 2026-08-08 ruling (option b,
         non-shared credential file per job), and (b) either fix or explain the apparent contradiction between the codex
         doc's STEP 2b invariant and `cloud-build-router.yml`'s actual per-job `auth` steps. Done-when: codex reflects
         the live 2026-08-08-ruled state and the STEP 2b contradiction is resolved or explicitly scoped.

## Archive candidates (operator review)

None beyond the 3 already auto-archived above (all were UNLOCKED + fully-verified-done, so archived directly per
SKILL.md Phase 4's auto-fix table — no operator gate needed for an unlocked, verified-done plan/issue doc).

## Refuted (dropped by verify)

1. **"PM public flip" vs `ci_pipeline_speed_and_cost_redesign`'s self-hosted fix** — NOT a contradiction (dedicated
   verifier): different axes (repo-visibility vs runner-placement), 3 distinct dated events, no doc is factually wrong
   about its own claim. See Contradictions #6.

_(populated in STEP 4)_

## Coverage (hunters / batches / docs)

_(populated in STEP 7)_

## Plans not reached

_(populated if applicable)_
