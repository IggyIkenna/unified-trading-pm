---
doc_type: plan
title: CI satellite AO batch 4 — fourth AO-dispatch extraction for the ci tranche
summary: >-
  Fourth AO-dispatch batch for the `ci` topic tranche, produced by `/ag-closeout-audit ci` (autonomous mode, 2026-07-31,
  ag_closeout_auditor scheduled worker, slot 12). Phase 0 re-checked batch1's still-open conflict-gated Deferred items
  (D1-D33) and batch2's (E1-E15) per the skill's iterative-drain methodology: batch2's todo 1 (which claimed both
  `scripts/quality-gates-base/base-service.sh` and `scripts/quickmerge.sh` for the ENVIRONMENT-binding fix) landed
  2026-07-30, freeing those files — this cleared the file-contention half of D3(2)/E3, D4/E4, and part of D3(4)/E5.
  Phase 1 read all 35 ci-tranche-primary candidate docs end-to-end via a `Workflow` (one agent per doc): 3
  `archivable_now` (fully done, awaiting only an operator `[unlock-plan]` archival step or a stale-checkbox flip — not
  this batch's scope), 2 `orphaned_never_touched` (one bounded and extracted below; one needs a re-scoping pass before
  it is AO-eligible, left Deferred), 4 `archivable_after_planned_work` (self-dispatched or batch2's own active todo —
  already correctly covered, no new work), and 26 `orphaned_partial_coverage`. Phase 3's conflict-check found
  `scripts/quickmerge.sh` re-contended by 3 of the 26 candidates (all downstream of the same now-freed file) — rationed
  to ONE combined todo, per the tranche's now-familiar file-contention discipline; a 4-part billing/capacity
  re-measurement sweep was similarly combined into ONE todo to avoid 4 concurrent writers on the same source doc. 9
  conflict-cleared bounded todos below; the rest deferred by taxonomy (operator-gated / role-mismatch / too-large /
  live-incident / time-gated-not-yet / needs-re-scoping) or already covered.
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-4, satellite-docs, quickmerge, github-actions, billing, promote-fleet]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_finalize_2026_07_29.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/08-workflows/deployment-flow.md,
  ]
created: "2026-07-31"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.6
estimate_calibrated_ai_days: 2.9
assigned_role: cicd
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md,
    /codex/08-workflows/ci-cd-flow.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit ci` run 2026-07-31 (ag_closeout_auditor scheduled worker, slot 12), re-triaging batch1's Deferred
  D1-D33 and batch2's Deferred E1-E15 per the iterative-drain methodology, plus a fresh Phase 1 Workflow-based read of
  all 35 current ci-tranche-primary candidate docs.
---

# CI satellite AO batch 4

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** All 9 todos shipped. Finalize plan
> `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md` (source-doc reconciliation, the
> 20-item Deferred re-check, and this archival) completed and archived alongside in the same commit set. Every
> still-genuinely-open Deferred item (D4-1, D4-7, D4-8, D4-9, D4-12, D4-13, D4-14, D4-17, D4-18) remains tracked in its
> own live active source doc with a real `- [ ]` checkbox (none was uniquely resident in this plan), so archiving it
> strands no open work — see the finalize plan's todos 2-3 for the full per-item re-verification. D4-5/D4-6/D4-10 are
> now operator-ruled and independently dispatchable directly in their own source docs; D4-2/D4-3/D4-4/D4-11/D4-15/D4-16/
> D4-19/D4-20 are fully resolved or superseded-by-completion. Successor: none drafted here; D4-1 (`quickmerge.sh`
> branch-check broadening) is ready for a future `ci_satellite_ao_dispatch_batchN` to extract.

> **✅ STATUS: `active`** — operator-approved 2026-08-06, dispatching. Todos 7 and 8 were found already shipped via
> `ci_satellite_ao_dispatch_batch1_2026_07_26.md` before dispatch (see their checkboxes); the other 7 todos are
> unaffected and dispatch as originally drafted.

> **Why this plan exists.** `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (11/30 todos still open) and
> `ci_satellite_ao_dispatch_batch2_2026_07_29.md` (4/14 still open) both remain active — this is NOT a replacement for
> either. This is the tranche's FOURTH extraction: items batch1/batch2 deliberately deferred on file-contention grounds
> that have now cleared, plus items genuinely new since batch2/batch3's snapshots (2026-07-29/30).

## Same-file contention — read before editing this plan

Same-priority todos in one plan run **concurrently**, so they must touch disjoint files (CLAUDE.md § Plans).
`scripts/quickmerge.sh` is — for the fourth consecutive round — the tranche's chronic contention point:

- **`scripts/quickmerge.sh` — 3 candidates this round (all released by batch2 todo1 landing 2026-07-30), rationed to ONE
  todo.** Todo 1 below combines the two smallest, already-fully-decided quickmerge.sh edits
  (`stale_staging_versions_manifest_2026_07_23.md`'s STAGE 1.6 dormancy gate +
  `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md`'s redundant-hook deletion+repoint) into one
  sequential-within-itself todo, since both are small, non-conflicting, operator-already-decided edits a single worker
  can land in one sitting. `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`'s step 3 (broadening
  the branch check) is EXPLICITLY NOT included here — it is doubly gated: on its own step 2 (todo 2 below, which does
  NOT touch `quickmerge.sh`) landing first, AND on `quickmerge.sh` being free again next round. Do **not** add a second
  `quickmerge.sh`-touching todo to this plan.
- **`plans/active/github_actions_operator_gated_followups_2026_07_17.md` — 4 read-only measurement/verification items
  all naturally write their findings back into this ONE source doc.** Rationed into ONE combined todo (todo 9) rather
  than 4 concurrent todos that would race each other's Progress-Log edit to the same file. A 5th item in the same doc
  (the operator-approved test-impact/selective-test-execution design-scoping todo) is deliberately NOT included here —
  seeing the file is already claimed by todo 9, it stays in `## Deferred` for batch 5.
- Every audit/verification todo below records its findings **in its own named source doc** (or, for todo 9, ONE shared
  dated Progress Log entry), never in this plan's body, so concurrent workers do not collide on this file.

## Todos

- [x] ✅ [INFRA] P2. **Implement the STAGE 1.6 dormancy-aware `scripts/quickmerge.sh` dependency gate (already
      operator-decided) + delete the now-redundant `scripts/dev/hooks/pre-push-strict-quickmerge.sh` + repoint its
      referrers.** — unified-trading-pm@b02ba28c7 Two small, independent, already-fully-decided `quickmerge.sh`-touching
      fixes, combined into one todo per the same-file-contention note above (do them sequentially within one session, do
      not split into two concurrent todos):
  1. **STAGE 1.6 dormancy gate — na-eligibility-audit 2026-08-01: VERIFIED ALREADY DONE, drop this sub-item.** Performed
     exactly the live-code verification this todo itself demands: `scripts/quickmerge.sh`'s current working tree
     (`_dep_versions_behind`) already reads `dormant = bool(rm.get('staging_dormant_mode', False))` /
     `r = ('' if dormant else rstag.get(dep, '')) or rmain.get(dep, '')` — exactly the option-1 fix this sub-item asks
     for. Shipped `unified-trading-pm@b3abf1bd5` (2026-07-30, the day before this batch4 doc was drafted), confirmed a
     genuine ancestor of current HEAD via `git merge-base --is-ancestor` and never reverted
     (`git log -S"dormant = bool"` shows exactly one touching commit). Source doc closed + archived at
     `/plans/archive/issues/stale_staging_versions_manifest_2026_07_23.md`. When this todo is actually dispatched, only
     sub-item 2 (delete the redundant hook) remains real work — re-verify sub-item 1 is still unnecessary at that time
     in case of an intervening revert, but do not re-implement it from scratch.
     <details><summary>Original sub-item text (superseded by the above, kept for history)</summary>

     `scripts/quickmerge.sh:998`'s dependency-version gate reads `staging_versions` before falling back to `versions`,
     which is wrong now that staging is dormant (`staging_dormant_mode: true`) — `staging_versions`'s only writer is
     frozen since 2026-06-27. Implement option 1 (operator-confirmed,
     `autonomous_session_operator_decisions_2026_07_25.md` entry #33): in `_dep_versions_behind`, ignore
     `staging_versions` when the manifest says `staging_dormant_mode: true` —
     `r = ('' if dormant else rstag.get(dep,'')) or rmain.get(dep,'')`. Verify by running a quickmerge in a repo that
     depends on `unified-api-contracts` and confirming the spurious "local=X < staging/main=Y" line is gone (the doc's
     own drift table has the exact repos to check). **CAUTION — this doc's own `[INFRA] P2` checkbox is already marked
     `[x]` but is a FALSE-CHECKED pointer**: its trailing text admits the fix was never implemented, only "queued for
     ci's next batch" — do not trust the checkmark, verify the live code (`_dep_versions_behind`/STAGE 1.6) directly
     before concluding this is already done.
     </details>

  2. **Delete the redundant hook.** `scripts/dev/hooks/pre-push-strict-quickmerge.sh` is dead weight — all three
     installers (`scripts/hooks/pre-push` chaining, `setup-tab-worktrees.sh`, the 5-min self-heal) now point at
     `scripts/hooks/pre-push` instead. Delete it and repoint its 4 known referrers: `migrate-slots-to-pathb.sh`,
     `scripts/quickmerge.sh` (a stale path reference), `/codex/08-workflows/ci-cd-flow.md:783`, and
     `/codex/05-infrastructure/per-tab-worktrees.md` — grep the corpus first to confirm no 5th referrer exists before
     deleting (per "delete deprecated code, no shims").
  - **Done when**: (1) a real quickmerge run against a UAC-dependent repo shows no spurious staging-drift warning under
    `staging_dormant_mode: true`, with a regression test if the surrounding STAGE 1.6 code has one already; (2)
    `scripts/dev/hooks/pre-push-strict-quickmerge.sh` no longer exists and `grep -rn pre-push-strict-quickmerge` (repo +
    codex) returns zero hits outside this todo's own commit history; both repos' `quality-gates.sh` green.
  - Source: `issues/stale_staging_versions_manifest_2026_07_23.md` ([INFRA] P2, batch2 Deferred E3 / batch1 D3(2)/D8) +
    `issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` ([DEVOPS] P3, batch2 Deferred E4 /
    batch1 D4).

- [x] ✅ [INFRA] P2. **Align `UnifiedCloudServicesConfig.environment`'s pydantic alias precedence with
      `BaseConfig.environment`'s (caller audit first), then grep the fleet for the same ambient-default-reliant test
      pattern.** — unified-trading-library@dc1dc7df. Caller audit: zero in-repo callers pass `environment=` to the real
      constructor (all use `model_construct`, which bypasses alias resolution) — fix safe. Fix: added
      `populate_by_name=True` to `model_config` + `"environment"` to `AliasChoices("ENVIRONMENT", "ENV")` in
      `core/config.py`, matching `BaseConfig.environment`'s pattern. Regression test
      `test_environment_kwarg_wins_over_ambient` proves kwarg wins over ambient env. Fleet grep of 23 repos: none found
      — no other repo has the ambient-default-reliant test pattern. Findings recorded in source doc Progress Log.
      `unified-trading-library` QG green (147s).

- [x] ✅ [DOC] P2. **Rewrite `/codex/08-workflows/deployment-flow.md`'s "Full Pipeline: LDR → Cloud Build" diagram +
      Gate 1/2/3 walkthrough to reflect the LDR-direct-promote-with-dormant-staging model.** —
      unified-trading-pm@445f02081. The doc still described the retired staging-mediated promotion pipeline;
      `/codex/08-workflows/ci-cd-flow.md` already got the equivalent rewrite (`unified-trading-pm@b9d0b9209`) — mirrored
      that pattern and cross-referenced it. Rewrote § "Full Pipeline: LDR → Cloud Build" (7-step ASCII diagram →
      LDR-direct model with dormant staging), § "Gate 2 — Quickmerge (Pass 2)" (renamed from "Staging via Quickmerge",
      lands on LDR not staging), and § "Gate 3 — Main Promotion + Semver Bump" (LDR→main direct via fleet promoter with
      3-gate MVP set, semver on push:[main], main-backmerge-to-ldr). `prettier` + `check_reference_paths.py` both clean
      on the edited file.
  - Source: `issues/deployment_flow_doc_stale_pre_ldr_direct_mvp_2026_07_30.md` ([DOC] P2) — filed 2026-07-30 as a
    byproduct of batch2 todo 1's own post-phase codex audit, never previously extracted into any batch.

- [x] ✅ [SCRIPT] P3. **Fix the stale structural-anchor pattern in
      `scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh:50`.** — unified-trading-pm@eff7413da.
      Updated the structural-anchor glob to match `setup.sh:438`'s current pip-fallback form (unquoted `uv==0.10.8`,
      `--quiet` flag, `$PYTHON_CMD -m` prefix). Test passes 5/5, QG green, shipped.
  - Source: `issues/uv_bootstrap_fallback_test_structural_anchor_stale_2026_07_30.md` (sole todo) — never cited by any
    covering doc; a clean, small, previously-untriaged orphan.

- [x] ✅ [REVIEW] P2. **Decide + implement whether `deployment-api` should be REMOVED from
      `scripts/workflow-templates/self-hosted-qg-repos.txt`** — unified-trading-pm@917fc626a. **DECISION: YES, remove
      (already done 2026-08-05).** `deployment-api` is a PUBLIC repo (confirmed `gh repo view --json visibility` →
      `PUBLIC`) — GitHub-hosted runners are unmetered for public repos; self-hosting wastes shared VM capacity for zero
      billing benefit. The entry was already removed from the active allowlist on 2026-08-05 as part of the
      15-public-repos cleanup (`self_hosted_runner_public_repo_revert_2026_08_05.md`, `self-hosted-qg-repos.txt` lines
      68-77). Verified: (1) `deployment-api` is NOT in the 8 active allowlist entries (lines 80-87, private repos only);
      (2) `deployment-api`'s own `quality-gates-v2.yml` uses `runs-on: ubuntu-latest` on all 3 jobs (lines 99/154/184);
      (3) template rollout `--dry-run --repo deployment-api` confirms `get_qg_runner_labels("deployment-api")` returns
      empty → `ubuntu-latest` fallback — all 8 updated templates render `ubuntu-latest`. No code change needed — the
      removal was already implemented and verified.
  - Source: `issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (`## Follow-up`, `[REVIEW] P2`) —
    never cited by any covering doc.

- [x] ✅ [VERIFY] P1. **Confirm a real post-flip triggered run succeeded (not just the YAML edit) for each of the 4
      "borderline" Tier-B self-hosted-runner files** — `cascade-qg-ordering.yml`, `freeze-deferred-build-replay.yml`,
      `reconcile-staging-versions.yml`, `update-repo-version.yml` — and append the sign-off + run URL/id for each into a
      new "## Tier-B sign-off log" section in the source doc (that section does not exist yet). Ground-truth check
      already confirms all 21 Tier-A files carry `runs-on: [self-hosted, glue]` (their own 2 checkbox todos are stale
      pointers, not real remaining work — do not re-do them). **Done when**: all 4 Tier-B files each have one
      run-id-cited successful post-flip run recorded in the new section. **COMPLETE 2026-08-06** — all 4 confirmed +
      sign-off log appended (`unified-trading-pm@f83716c0b`).
  - Source: `pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md` ([VERIFY] P1) — never cited by any
    covering doc.

- [x] ✅ [CI] P1. **DONE-ELSEWHERE 2026-08-06 (governance-sweep activation-readiness check).** Already shipped via
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Migrated prevention todos from resolved incidents (2026-08-02)"
      section, commit `unified-trading-pm@4bf65b67c` ("tally auto-merge ARM_FAILED separately from PROMOTED in
      ldr-to-main-promote-fleet", 2026-08-02) — the root cause was the concurrent GitHub Actions billing-wall incident,
      not a code defect, plus an adjacent ARM_FAILED-tally bug fixed in the same commit. Verified live on the current
      branch. No action needed. Original text preserved below for record. **Root-cause and fix
      `market-tick-data-service`'s promote PRs never getting auto-merge armed** — confirmed reproducing across 12+
      consecutive worker re-checks through 2026-07-31 (PRs #788→#793, each superseded before merging despite
      `mergeable: MERGEABLE` and every required check green; `autoMergeRequest: null` every time).
      `.github/workflows/ldr-to-main-promote-fleet.yml`'s PR-creation path (~line 1030-1038) DOES attempt
      `gh pr merge --auto --squash --delete-branch` loudly (echoes `⛔ WARN: auto-merge ARM FAILED` on failure, not
      silently swallowed) — start by reading the actual run logs for MTDS's recent promote-fleet dispatches to find
      whether that WARN line printed (a real arm failure — check the underlying `gh` error, likely a branch-protection
      or merge-method mismatch) or whether the arm call is never being reached at all for MTDS specifically (a different
      bug in the branch/loop logic upstream of the arm call). Fix the root cause; if the fix is "add a
      re-arm-if-not-armed check on the existing-PR re-inspection path" (since only the fresh-PR-creation branch attempts
      the arm today), add it there. **Explicitly out of scope**: do not touch the `--squash`/`--delete-branch` semantics
      or the provenance-gate check — only the auto-merge-arming mechanism. **Done when**: MTDS's current open promote PR
      (or the next one it regenerates) shows `autoMergeRequest` non-null and merges without manual intervention once
      green, and the fix is verified against a real live run (not just a code read). This closes a real, ongoing waste
      source: the sibling `defi_venue_pipeline_to_live_ao_build_2026_07_30.md` VERIFY-gate todo (a DIFFERENT tranche's
      doc, not this batch's to edit) has been re-dispatched 12+ times solely to re-confirm this same unfixed root cause
      — landing this fix stops that churn too.
  - Source: `issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` ([CI] P1, the 2026-07-30
    slot-3 finding) — never cited by any covering doc. **Not gated on this doc's own operator-only items A/B/C** (the GH
    throttle-banner check) — this is a separate, fully-diagnosed, unrelated bug found while investigating the
    now-self-resolved startup_failure incident.

- [x] ✅ [SCRIPT] P2. **DONE-ELSEWHERE 2026-08-06 (governance-sweep activation-readiness check).** Already shipped via
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md`, commit `unified-trading-pm@ccb1d7b10` ("monitor + page on 3+
      consecutive startup_failure runs on the LDR->main promote workflows", 2026-08-02). Verified live on the current
      branch (`scripts/cicd/promote_fleet_startup_failure_monitor.py` present, wired into `notify-slack.yml`). No action
      needed. Original text preserved below for record. **Add a standing monitor for 3+ consecutive `startup_failure`
      runs on `ldr-to-main-promote.yml` / `ldr-to-main-promote-fleet.yml`.** The 2026-07-30 incident (both workflows
      failing every tick for ~10h) ran silently until noticed as a side-effect of an unrelated task — a dedicated alert
      would have caught it in under an hour. Extend `scripts/cicd/promotion_lag_monitor.py` (or add a new lightweight
      check) to fire through the `notify-slack.yml` carrier with a state-transition `dedup_key` per
      `/codex/04-architecture/ci-alerting.md` (fire on change / RESOLVED / re-remind, never every tick) — do NOT edit
      `ldr-to-main-promote-fleet.yml` itself for this (keep it a separate detector, avoiding any collision with todo 7's
      edits to that file). **Done when**: a synthetic 3-consecutive-`startup_failure` case fires exactly one alert, and
      a healthy/intermittent-failure pattern fires none.
  - Source: `issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` ([SCRIPT] P2) — never cited
    by any covering doc.

- [x] ✅ [VERIFY] P0. **DONE 2026-08-09 (slot-28, review→cicd craft)** — Time-gated billing/capacity re-measurement
      sweep — 4 items in `github_actions_operator_gated_followups_2026_07_17.md`, all now unblocked, combined into one
      todo per the same-file-contention note above.** Recorded all 4 findings as ONE dated Progress Log entry in the
      source doc (2026-08-09 entry, end of Progress Log) + flipped all 4 source checkboxes. Live Enhanced-Billing pull
      (`github-billing-token` from GCP Secret Manager,
      `GET /users/IggyIkenna/settings/billing/usage?year=2026&month={7,8}`, 2241 `product=actions` line items,
      `netAmount` per-item — never `/timing.total_ms`; token never printed, shredded from the shell env post-pull) + a
      real `gh api .../actions/runs/{id}/jobs` pull for the QG-minutes measurement.
  1. **Phase-5 two-week billing ledger re-pull vs the Phase-0 baseline** (batch1 Deferred D29 — gate was "earliest
     ~2026-07-31"; today IS 2026-07-31). Method + exact commands are already in the doc's 2026-07-23 billing entry —
     re-run verbatim. Target check: fleet ~$1,000/mo → ~$300-400/mo, and whether the +47% non-PM-repo rise masking PM's
     own real savings (noted at the 1-week checkpoint) has resolved.
  2. **Re-measure a representative QG run's billed job-minutes + the docs-PR/identical-tree skip rates**, before/after
     comparison via ledger + run counts (a distinct, never-run measurement from item 1).
  3. **Enhanced-Billing per-repo re-pull**, scoped to the first-flipped repo, confirming its `Actions Linux` line
     dropped with no new billed line replacing it (`billable: {}` is the honest self-hosted check, not
     `/timing.total_ms`) — gate was "one week after the first repo's flip lands"; Phase 7's fan-out shipped
     2026-07-27/28, so this has been unblocked for days.
  4. **Enhanced-Billing FULL FLEET re-pull** (not just PM, not just flipped repos), compared against the Jul23-26
     baseline (fleet ~~$37/day, non-PM ~$23/day) — gate was "once ≥5 repos are flipped"; all 24 non-PM repos are flipped
     as of 2026-07-27/28, so this too has been unblocked for days. This is the number the original
     "~~$1,000/mo →
     ~$300-400/mo" target was actually about.
  - **Done when**: all 4 measurements are recorded with real numbers (or a note that the billing token is unavailable —
    do not estimate) in one dated Progress Log section of the source doc, honoring its own documented measurement traps
    (skipped jobs aren't billed; a throttled API call silently counts as 0; `billable: {}` with no `UBUNTU` key is the
    real zero, not `/timing.total_ms`).
  - Source: `github_actions_operator_gated_followups_2026_07_17.md` (Phase 5 `[VERIFY] P0` line 154; the
    representative-QG-run `[VERIFY] P0` line 149; the two Enhanced-Billing `[VERIFY] P2` items lines 753/756) — none
    previously cited by any ci-tranche covering doc despite 3 of the 4 gates now being long-expired.

## Deferred

Tagged by WHY, per the `/ag-closeout-audit` non-batchable taxonomy. Only **conflict-gated** items can be converted by a
future batch's re-triage; the rest need direct operator/human action, elapsed time, or a re-scoping pass.

### Conflict-gated (re-triageable in batch 5+)

| id   | Item                                                                                                                                                                        | Competing claim it collided with                                                                                                                                                                      |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D4-1 | `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` step 3 — broaden `quickmerge.sh`'s branch check to recognise `live-defi-rollout`/`staging`            | Todo 1 owns `quickmerge.sh` this round; also internally gated on todo 2 (step 2, the alias-precedence fix) landing first                                                                              |
| D4-2 | `github_actions_operator_gated_followups_2026_07_17.md`'s operator-approved (2026-07-28) test-impact/selective-test-execution design-scoping todo (`[REVIEW] P2`, line 776) | Todo 9 owns this file this round for the 4-item billing sweep                                                                                                                                         |
| D4-3 | `github_actions_operator_gated_followups_2026_07_17.md`'s BigQuery `resource_samples` utilization verification against the pre-stated 50-70% band (`[VERIFY] P2`, line 632) | Same file, same reason as D4-2 — folding this in too would have made todo 9 a 5-part sweep; held for a cleaner batch-5 extraction                                                                     |
| D4-4 | `sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md`'s stuck-gate-monitor todo                                                                             | Already claimed by batch1's own still-open todo ("A repo SIT-BLOCKED for N consecutive promoter ticks must be visible") — not a fresh item, just re-confirmed still-open coverage, no new todo needed |

### Operator-gated (needs a ruling, not a re-triage)

| id    | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D4-5  | `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` — direction (a)-(d) for the shared gcloud active-account collision between GH-Actions self-hosted-runner WIF steps and the AO orchestrator's own SA; corroborated by 2 fresh 2026-07-30 occurrences, still unruled. Same as batch1 D9.                                                                                                                                                                                                                                                                                                                                                           |
| D4-6  | `aws_codebuild_terraform_import_pending_2026_07_22.md` — the D1-D4 rulings table (IAM policy scope, whether to create 18 webhooks, compute/timeout/tags direction, fix 2 live-side drifts) must be answered before the real `terraform import` can run. Batch1's D27 citation (blocked on AWS credits) is now STALE — the 2026-07-30 session actually stood up the S3 backend using the operator's own credentials; the live blocker is this rulings table, not missing perms.                                                                                                                                                                                    |
| D4-7  | `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md` — both residuals explicitly "should not be auto-queued to a worker" per the doc's own text (same as batch1 D19).                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| D4-8  | `build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` — all 4 remaining items under an explicit operator instruction: "Page-first, do NOT fix here… loop Ikenna in." Same as batch1 D26.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| D4-9  | `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`'s DESIGN P2 item (should a UAC registry-change promote fan out consumer QG?) — already escalated as batch2's own operator question 1 (E8), unruled.                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| D4-10 | `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` — **RECLASSIFIED this round.** Was tagged conflict-gated (E1, `base-service.sh` contention with batch2 todo1). Batch2 todo1 landed 2026-07-30, so the file-contention half is cleared — but the doc's own "Recommended decision" independently states the BATS-execution-phase addition (touching the shared fleet-wide `base-service.sh`) "needs its own properly-scoped plan with the operator's plan-destination call," not a silent batch todo. The TRUE blocker was never file contention — it's an authority/scope call this skill cannot make. See `## Escalated to the operator` question 1. |
| D4-11 | `ldr_to_main_promote_churn_fix_verification_2026_07_27.md` — removing quickmerge.sh's PM-specific Option-B direct-PR-open step needs explicit operator sign-off (same as batch2 E6, still unruled). Todo 2 (churn re-measurement) stays transitively gated on todo 1.                                                                                                                                                                                                                                                                                                                                                                                             |
| D4-12 | `mtds_deployment_env_race_survives_single_worker_2026_07_23.md` — genuinely-unbounded investigation (5 failed prior sessions per batch2 E7); same shared blocker as `mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`. Same as batch1 D3(3) / batch2 E7.                                                                                                                                                                                                                                                                                                                                                                                     |
| D4-13 | `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` — items [A]/[B] (dependency-content-aware v2 sentinel) explicitly require operator sign-off before an autonomous ship; unchanged since batch1 D11.                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| D4-14 | `post_cutover_silent_assumption_sweep_2026_07_23.md` §F4 — disable/fix the 4 vacuous crons + diagnose `digest-drift-sweep` non-convergence; needs a per-cron ruling. Same as batch1 D2/D6, batch2 E9/E10 — re-verified this round, still unchanged/unruled.                                                                                                                                                                                                                                                                                                                                                                                                       |
| D4-15 | `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` — whether the 33 already-laundered commits need a dep-order spot-check beyond the bot's own gate, or whether the doc simply closes. Genuine judgment call, unchanged.                                                                                                                                                                                                                                                                                                                                                                                                                     |
| D4-16 | `sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` — the direction ruling among lease / SIT-sha-pin+gate-change / accept-and-monitor. Unchanged since batch1 D12.                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| D4-17 | `qg_sentinel_environment_blind_2026_07_23.md` — the one genuinely-unresolved residual is the MTDS-specific ENVIRONMENT-coupled test pair (same underlying blocker as D4-12/E7); everything else in this doc is done (batch2 todo1/todo3), just not all checkboxes flipped — a doc-hygiene note, not new work.                                                                                                                                                                                                                                                                                                                                                     |
| D4-18 | `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` — P0 redo of the `\|\| true` fix in `glue-runner-run.sh` needs a `--selfcheck` mode + a staged one-unit roll (it crash-looped all 5 live runners once already); same live-runner-infra risk profile for the P3 `StartLimitBurst` item. Both stay Deferred, unchanged since batch1 D14/D15.                                                                                                                                                                                                                                                                                                     |

### Live incident (too risky to batch while hot)

| id    | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D4-19 | `github_actions_billing_wall_recurrence_2026_07_29.md` — the incident itself is still `status: open`/unresolved as of its latest entry (2026-07-30T06:11-06:16Z). Item 1 is operator-only (clear the billing block). Items 2-4 are real bounded bugs (spend-telemetry remediation status, outage-aware v2 status dispatch, the literal `authoring_slot="ci-reconcile"` 400 bug) but folding any of them into a batch risks colliding with the doc's own actively-evolving state while the incident is hot — matches the precedent set by batch3 declining to extract from other live-incident docs the same way. Re-triage once the doc's own Progress Log shows the incident resolved. |

### Needs a re-scoping pass before it is AO-eligible

| id    | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D4-20 | `cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` — "roll the empty-tag guard out to the 19 consumer repos" (`[DEVOPS] P2`). This is `orphaned_never_touched` (genuinely never cited by any covering doc) but is NOT simply draftable as-is: the drift checker that shipped 2026-07-28 now correctly REFUSES 15/19 consumers, meaning the rollout mechanism this todo originally assumed (a clean `--apply` sweep) no longer applies — the replacement approach (hand-apply per repo vs. resolve each repo's drift first) is itself undecided. Needs a scoping pass (name the actual mechanism) before it can become a bounded todo. |

### Already covered (re-confirmed this round, no action needed)

- `/plans/archive/issues/mtds_ungated_test_families_2026_07_17.md` — was `archivable_now`; both its Todos were fully
  done (evidenced), only its own stale todo-5 checkbox was never flipped. **Archived 2026-07-31** by
  `/na-eligibility-audit ci` (todo 5 flipped with citation, then the standard 6-step ritual) — no longer active-corpus
  work, confirming this batch's own prediction.
- `promotion_lag_alert_hides_provenance_block_2026_07_17.md` — `archivable_now`; fully resolved 2026-07-30, awaiting
  only an operator `[unlock-plan]` on `locked_by: live-defi-rollout` to actually archive.
- `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` — `archivable_now`; 29/29 todos done, own 2026-07-30
  na-eligibility-audit verdict independently confirms ARCHIVE-READY, awaiting the same operator `[unlock-plan]` step.
- `/plans/archive/issues/plan_health_agent_dead_schedule_trigger_2026_07_27.md` — was `archivable_after_planned_work`;
  batch2 todo 13 landed (resolved as moot 2026-07-31). **Archived 2026-07-31** during the batch2 finalize
  (`ci_satellite_ao_dispatch_batch2_finalize_2026_07_29.md` todo 1) — no longer active-corpus work.
- `ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md`,
  `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` — `archivable_after_planned_work`: either batch2's own
  active todo or genuinely self-dispatched (`assigned_vm: planning`), confirmed still live/being worked through
  2026-07-31. No new coverage needed. `qg_mem_wrap_systemd_bus_unavailable_2026_07_26.md` — both todos closed 2026-08-01
  (P2 shipped 2026-07-30, P3 analysis-closed no code change); **resolved + archived**, no longer live.
- `monitoring_control_plane_master_2026_06_10.md` — G3 (manifest-consolidator-health) is already batch2's own active
  todo; its 3 other open items (Rollout-ratchet panels, Runtime-deploy-signal-v2, G4) are correctly parked in batch2's
  own Deferred (E13 role-mismatch, E14 too-large/escalated) — re-confirmed unchanged, not re-listed here.
- `ui_build_warm_cache_2026_06_17.md` — the pnpm migration item is role-mismatch (needs `[UI]`, same as batch1 D20); the
  `setup.sh` pre-warm sync to `deployment-ui` is small and genuinely actionable now (its blocker cleared 2026-07-30) but
  is PM/UI-repo-boundary-adjacent enough (a `cp` into a UI repo, even though it's a plain script not `src/`) that it is
  held for a `[UI]`-capable slot's judgment rather than assumed safe here — flagging for batch 5, not drafted this round
  to avoid guessing wrong on the UI-gate boundary.
- `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`,
  `cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md` — both have exactly one open item each,
  already correctly parked (E8 escalated; a self-described "still an open judgment call" sub-todo respectively) —
  re-confirmed unchanged.

## Escalated to the operator (parked, not guessed)

One question, quote/location/options/recommendation, not resolved autonomously:

1. ~~**D4-10 (`pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`)** — should adding a BATS test-execution
   phase to the shared, fleet-wide `scripts/quality-gates-base/base-service.sh` be its own dedicated AO-dispatched or
   human plan?~~ **RESOLVED 2026-08-08 (round5-ci-question-resolution) via the workspace default, not a fresh operator
   ruling.** CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE states: _"Default is human
   (`assigned_vm: NA`) unless the operator explicitly says otherwise."_ No explicit override exists anywhere in the
   corpus, so option (b) below is the answer by default, not this entry's own soft-recommended option (a) — which this
   entry itself correctly declined to assume without operator sign-off. Original options/quote preserved for the record:
   Quote (doc's own "Recommended decision"): _"This is a base-service.sh change (used by every repo in the fleet), so it
   needs its own properly-scoped plan with the operator's plan-destination call, not a silent addition inside an
   unrelated one-script todo."_ Options were (a) fold into a future ci-tranche batch anyway, scoped as warn-only-first
   (mirrors the existing actionlint pattern); (b) **[DEFAULT — now the answer]** author it as its own standalone human
   plan (`assigned_vm: NA`); the operator may still explicitly override to (a) later.

## Codex SSOTs (read before executing any todo)

- `/codex/08-workflows/ci-cd-flow.md` — pipeline / quickmerge / strict-quickmerge / gate set / release + wheel
- `/codex/08-workflows/deployment-flow.md` — the doc todo 3 rewrites
- `/codex/06-coding-standards/quality-gates.md` — how gates run; never `pytest` directly
- `/codex/04-architecture/ci-alerting.md` — `notify-slack.yml` carrier, `dedup_key` + cooldown, recovery-gated
  all-clears (todo 8)
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-07-31** — Drafted by `/ag-closeout-audit ci` (autonomous mode, `ag_closeout_auditor` scheduled worker, slot
  12). Phase 0: re-checked batch1's D1-D33 and batch2's E1-E15 against current state — batch2 todo1 (landed 2026-07-30)
  freed `scripts/quickmerge.sh` and `scripts/quality-gates-base/base-service.sh`, clearing the file-contention half of
  D3(2)/E3, D4/E4, D3(4)/E5(partial), and E1(partial — E1's TRUE blocker turned out to be operator-scope, not file
  contention, see D4-10). Phase 1: all 35 current ci-tranche-primary candidate docs read end-to-end via a `Workflow` (35
  parallel agents, 0 errors) — 3 `archivable_now`, 2 `orphaned_never_touched`, 4 `archivable_after_planned_work`, 26
  `orphaned_partial_coverage`. Phase 3: conflict-check found `quickmerge.sh` re-contended 3 ways (rationed to todo 1;
  todo 2 scoped to avoid it; D4-1 deferred) and `github_actions_operator_gated_followups_2026_07_17.md` contended 5 ways
  by read-only measurement/design items (rationed to todo 9's 4-item sweep; D4-2/D4-3 deferred). 9 todos drafted, 20
  items deferred (D4-1 through D4-20), 1 escalated to the operator. Nothing shipped, nothing flipped to `active`.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries) — the sole remaining open todo's source
  (`github_actions_operator_gated_followups_2026_07_17.md`), the still-open sibling batch1, this batch's own gated
  finalize, the umbrella pipeline codex SSOT, and the `/ag-closeout-audit` methodology this batch was produced by;
  dispatch-batch-coordinator shape (each done todo already cites its own separate source doc inline).

- **2026-08-09 (slot-28, review→cicd craft)** — Completed todo 9 (the 4-item billing/capacity sweep), the last open todo
  in this batch. Pulled live GitHub Enhanced-Billing usage (`github-billing-token` from GCP Secret Manager,
  `GET /users/IggyIkenna/settings/billing/usage?year=2026&month={7,8}`, 2241 `product=actions` line items across both
  months, `netAmount` field per item — never `/timing.total_ms`, per the doc's own documented trap; token loaded into a
  shell var, never echoed/printed, unset after use).
  1. **Phase-5 two-week+ re-pull vs Phase-0 baseline**: Jul1-15 baseline fleet $35.51/day (PM $16.89/day, non-PM
     $18.61/day) vs Aug1-8 (8 clean days, well past the 2-week mark) fleet $12.72/day (PM
     $6.86/day, non-PM
     $5.85/day). Fleet -64.2% (~$1065/mo→~$382/mo, **lands the ~$300-400/mo target**), PM -59.4%,
     non-PM -68.5% — the 2026-07-23 checkpoint's +47% non-PM-masking finding has fully reversed (non-PM now falling
     faster than PM).
  2. **Representative QG run billed minutes + skip rates**: pulled
     `gh api repos/IggyIkenna/features-service/actions/ runs/{id}/jobs` for a real `pull_request`-triggered run
     (31298538159) — content-sentinel 1min + QG-slice(tests) 5min + QG-slice(checks) 3min + rollup 1min = **~10 billed
     min/run** (vs. the doc's own 2026-07-27 ~14min/run figure — consistent, run-to-run variance). Identical-tree
     sentinel skip rate: grepped 20 real job logs per repo for the actual `content-sentinel HIT`-vs-`MISS` STDOUT line
     (disambiguated from the always-both-present source-echo dump by occurrence count, not a simple string-presence
     check, which false-positived 20/20 on the first pass) — PM 1/20 (~5%), features-service 0/20 (its run mix is
     dominated by promote-PRs, which always touch code by construction, so 0% is the expected honest reading there, not
     a measurement gap).
  3. **Enhanced-Billing per-repo re-pull, agent-orchestrator (first-flipped canary, 2026-07-27)**: `Actions Linux`
     $13.87/day (Jul20-26, pre-flip) → $3.78/day (Aug1-8, post-flip), **-73%**, `Actions storage` unchanged at
     $0, no
     new billed SKU line added (self-hosted glue jobs bill $0 as designed). Residual $3.78/day is the
     still-hosted `quality-gates-v2` pytest/lint job, explicitly out of this phase's scope (security ADR: no self-hosted
     runner may carry a `pull_request` trigger) — not a gap in the flip.
  4. **Enhanced-Billing FULL FLEET re-pull vs Jul23-26 baseline**: $37.35/day → $12.72/day (Aug1-8), **-65.9%** (non-PM
     $23.09/day→$5.85/day, -74.7%) — this is the number the plan's original "~$1,000/mo→~$300-400/mo" target was about,
     and it has now moved into the target band. All 4 measurements recorded as one dated entry in the source doc
     (`github_actions_operator_gated_followups_2026_07_17.md`, 2026-08-09 Progress Log entry) + all 4 source checkboxes
     flipped there. This batch's only open todo is now done — `finalize` gate should re-check.
