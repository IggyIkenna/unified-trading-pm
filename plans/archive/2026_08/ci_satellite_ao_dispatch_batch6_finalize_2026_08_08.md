---
doc_type: plan
title: CI satellite AO batch 6 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch6_2026_08_08.md — machine-held via depends_on + gate_on_depends: true
  until all 12 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the Deferred items (D6-1 through D6-29) for whether their blocker has cleared, flips the 2 confirmed
  stale-checkbox items in github_actions_operator_gated_followups_2026_07_17.md and
  post_cutover_silent_assumption_sweep_2026_07_23.md that batch6's own Phase 1 audit found already-done-but-unflipped,
  and archives batch 6 via the standard 6-step ritual.
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.9
estimate_calibrated_ai_days: 0.7
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch6_2026_08_08]
gate_on_depends: true
source: >-
  Authored alongside `ci_satellite_ao_dispatch_batch6_2026_08_08.md` per `plans/active/task_template.md` §4's
  finalize-plan-coverage rule. Authored `status: active` (not `draft`) per the established 2026-07-30 no-double-gate
  finding (batch4/batch5's finalize plans record the same): `gate_on_depends: true` already machine-holds every task
  here until the batch's own todos are `done`, including while the batch is still `draft` (via the derived
  `gate-upstream-open:<stem>` condition).
assigned_role: cicd
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 6 — finalize

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** All 3 todos done. Todo 1 reconciled all 12 batch-6 source docs plus the 2
> D6-8/D6-9 stale-checkbox docs; todo 2 re-checked all 29 Deferred items (11 cleared, 18 confirmed still open, none
> silently dropped); todo 3 archived `ci_satellite_ao_dispatch_batch6_2026_08_08.md` via the standard 6-step ritual,
> alongside this finalize doc, in the same commit set. Successor: none.

> **🔒 GATED, not draft (historical).** `depends_on: [ci_satellite_ao_dispatch_batch6_2026_08_08]` +
> `gate_on_depends: true` held every todo below until all 12 of batch6's own todos were `done` — this applied whether
> batch6 was still `status: draft` or had been flipped `active`. No separate flip was needed for THIS doc.
> `sequential: true` because todo 2's reconciliation needed todo 1's verification current, and todo 3 (archival) had to
> run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 12 batch-6 todos' source docs.** Each batch-6 todo ends with `Source:` naming a
      doc. For each: flip the corresponding checkbox or annotate the corresponding prose section, citing the batch-6
      commit that shipped it — **verify the cited commit exists and is an ancestor of `origin/live-defi-rollout` before
      citing it** (`git merge-base --is-ancestor`). **Also flip the 2 confirmed-already-done-but-unflipped stale
      checkboxes batch6's own Phase 1 audit surfaced** (see D6-8, D6-9 in batch6's Deferred table): the
      ldr-docs-gate-firing verification + the codex staging-re-entry item in
      `github_actions_operator_gated_followups_2026_07_17.md` (both closed by `unified-trading-pm@97970974e` and a
      batch1 [VERIFY] P2 todo, 2026-07-26 — verify the ancestor relationship before flipping, do not trust the citation
      blind), and the F3 `cascade-qg-ordering.yml`/`sit-gate.yml` success-reporting item in
      `post_cutover_silent_assumption_sweep_2026_07_23.md` (closed by batch5's `[INFRA] P2` todo, 2026-08-07 — same
      ancestor-verify-first rule). Then, per doc, re-check whether it now has zero open work **in checkbox AND prose
      form**; only set `status: resolved` on a doc that genuinely reaches zero. **Done when**: every cited doc (batch-6
      sources plus the 2 stale-checkbox docs above) is flipped/annotated with verified evidence, and each doc that
      genuinely reaches zero open work is `status: resolved`. **DONE 2026-08-09, slot 31** — see this doc's own Progress
      Log for the full per-doc breakdown.
- [x] ✅ [REVIEW] P1. **Re-check the Deferred items D6-1 through D6-29 for whether their blocker has cleared.**
      D6-1/D6-2 (the two parked `scripts/workflow-templates/` claims) — has todo 9 landed, freeing the mechanism? If so
      both are ready-for-batch-7 extraction; note it, do NOT draft it here. D6-3 — has batch4's todo 1 landed
      (`scripts/quickmerge.sh` freed)? D6-4 through D6-14 (operator-gated) — has any received a ruling since 2026-08-08?
      D6-15 through D6-19 (time-gated/live-incident) — has the incident's own Progress Log shown resolution, or has the
      stated elapsed-time gate passed? D6-20 through D6-22 (needs-re-scoping) — has anyone supplied the missing scope
      decision? D6-23 through D6-29 (too-large/human-only) — unchanged confirmation only. **Done when**: each of D6-1
      through D6-29 has either (a) a note that it is ready for batch-7 extraction because its blocker cleared, or (b) a
      re-verified confirmation the blocker is still open. Do NOT draft follow-up todos here — this plan's scope is
      reconciliation, not fresh drafting. **DONE 2026-08-09, slot 2** — see this doc's own Progress Log for the full
      per-item breakdown (11 of 29 blockers cleared, 18 confirmed still open).
- [x] ✅ [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch6_2026_08_08.md`** via the standard 6-step ritual (CLAUDE.md
      § plan archival). **DONE 2026-08-09, slot 15**: (1) confirmed no unresolved Deferred item was silently dropped —
      every D6-1 through D6-29 row names a still-live, still-tracked source doc of its own (none was uniquely resident
      in batch6), so archival strands no open work; todo 2 above already did the per-item re-verification. (2) Archive
      banners added to both this doc and batch6 itself. (3) Codex-alignment check: batch6 todos 4 and 6 each established
      a genuinely new contract not previously documented anywhere in codex — `scripts/cicd/alert_recovery.py`'s shared
      state-diffed recovery-bookend helper (todo 4, wired into 6 standing- condition monitors) and `ci_reconcile.py`'s
      `should_suppress_redispatch()` escalation-dispatch cooldown guard (todo 6) — both added to
      `/codex/08-workflows/ci-cd-flow.md`'s "Central CI watcher" section (`unified-trading-pm@<this commit>`);
      `/codex/04-architecture/ci-alerting.md` needed no change (it governs Slack-page dedup, a distinct mechanism from
      either). (4) No CLAUDE.md bullet warranted — both are implementation details under the existing "CI alerts"
      one-liner's SSOT pointer, not new workspace-wide rules. (5) Every leading-slash
      `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md` and
      `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md` reference in the active corpus (7
      files, 14 occurrences — `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26_finalize_2026_08_08.md`,
      `issues/ci_monitor_recovery_bookend_residual_gaps_2026_08_09.md`,
      `issues/tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md`,
      `issues/ag_closeout_audit_ci_parked_2026_08_09.md`, `issues/ag_closeout_audit_ci_parked_2026_08_08.md`, plus each
      doc's own self/sibling references) repointed to `/plans/archive/2026_08/...`; bare (non-leading-slash) prose
      mentions of the doc name left as-is (historical citations, out of `check_reference_paths.py`'s scope by design —
      only `/plans/...`/`/codex/...`-prefixed refs are existence-checked). `plans/active/INDEX.md`'s stale entry is
      auto-regenerated, not hand-edited. (6) `locked_by` confirmed empty on both docs. **Done when**: the plan is in
      `plans/archive/2026_08/`, every corpus referrer resolves, `check_reference_paths.py` has not regressed, and this
      finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes
- `/codex/08-workflows/ci-cd-flow.md` — the pipeline contracts several batch-6 todos touch
- `/codex/04-architecture/ci-alerting.md` — the dedup/recovery-bookend contract todos 3, 4, 6 establish or extend
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-08** — Drafted alongside `ci_satellite_ao_dispatch_batch6_2026_08_08.md`. Authored `status: active` per the
  established no-double-gate precedent (batch4/batch5's finalize plans record the same reasoning); batch6 itself remains
  `status: draft` pending the operator's flip.
- **2026-08-09 (todo 1, slot 31)** — Reconciled all 12 batch-6 source docs plus the 2 D6-8/D6-9 stale-checkbox docs, one
  by one, verifying every cited commit is an ancestor of `origin/live-defi-rollout` (`git merge-base --is-ancestor`)
  before citing it:
  1. `issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` (todo 1) — already correctly reconciled
     (checkbox flipped + Progress Log entry present); no action needed.
  2. `issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (todo 2) — already correctly reconciled,
     `features-service@7c86a6b1` verified ancestor; no action needed.
  3. `issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (todo 3) — flipped 2 stale `[ ]` checkboxes
     (`[REVIEW] P2` allowlist-removal item citing `unified-trading-pm@917fc626a`; `[SCRIPT] P1` automation-gap item
     citing `unified-trading-pm@b073c47f9`), both verified ancestors. Doc still carries genuine open prose work
     (redeploy-to-live-VM + operator-gated throughput decision) — `status` correctly stays `open`.
  4. `issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md` (todo 4) — corrected a STALE
     citation: `c717af0fd` does not resolve to a commit in this repo (`git cat-file -e` fails — a pre-rebase SHA);
     replaced with the actual work commit `unified-trading-pm@4bd8a11d0b` (verified ancestor), matching the correction
     batch6's own plan already made for its todo 4. Doc genuinely reaches zero open checkbox+prose work but a prior
     session already documented why it deliberately stays `status: open` + `archive_exempt: true` (a line-cap/link-gate
     archival deadlock) — respected that existing reasoning rather than overriding it.
  5. `issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` (todo 5) — replaced the vague
     "unified-trading-pm@(this commit)" placeholder citation with the actual flip commit `unified-trading-pm@39e71f811`
     (found via `git log --follow`, verified ancestor). Doc still has 1 open `[INFRA] P3` item (D6-2's parked scope);
     status unchanged.
  6. `issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` (todo 6) — already correctly reconciled,
     `agent-orchestrator@a351d0d` verified ancestor; no action needed.
  7. `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` (todo 7) — flipped the unchecked `[ ]`
     lag-alert-cause-per-line item, citing `unified-trading-pm@66ba7feda` (verified ancestor). Doc's other 3 open items
     stay correctly parked per batch1 D14/D15/D33 precedent; status unchanged.
  8. - 9. `plans/archive/2026_08/issues/unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md` (todos 8, 9) —
          already `status: resolved` and archived; no action needed.
  9. `ui_build_warm_cache_2026_06_17.md` (todo 10) — flipped the pnpm hardlink-store checkbox, verified
     `deployment-ui@33c6a02`, `unified-trading-system-ui@e70aeeb8`, `unified-trading-pm@e9e344a66` are all ancestors.
     This was the doc's LAST open item (sub-parts 1-2 already shipped) — zero open checkbox/prose work remains, so
     `status: active` → `complete` (`resolved` isn't a valid `doc_type: plan` status; `complete` is the plan schema's
     terminal value). Not archived (`locked_by: live-defi-rollout` is non-empty, blocking archival without an
     `[unlock-plan]` decision — out of this todo's scope).
  10. - 12. `quality_gates_quickmerge_timing_baseline_2026_07_31.md` (todos 11, 12) — todo 11's item had been converted
            to a non-checkbox digest pointer ("do the work via batch6, not here"); converted it back to a real `[x]`
            checkbox with the actual evidence + citation (`unified-trading-pm@ec01e4167`, verified ancestor) now that
            batch6 shipped it. Todo 12's item was already an `[x]` checkbox with full evidence but no commit citation;
            added one (`unified-trading-pm@7f41c4488`, verified ancestor). Doc still has 3 other open items; status
            unchanged.
  - **D6-8**: `github_actions_operator_gated_followups_2026_07_17.md` — flipped 2 stale table rows: row 14
    (`ldr-docs-gate` firing verification, citing batch1's 2026-07-26 `[VERIFY] P2` live-check evidence — no code commit,
    a pure observation) and row 5 (codex staging re-entry procedure, citing `unified-trading-pm@97970974e`, verified
    ancestor, from batch1's combined `[DOC] P2` todo). Doc has many other genuinely open rows; status unchanged.
  - **D6-9**: `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` — the F3 item is a composite (3 slices); the
    `service-deployed→deployment-service` slice was already done, and I added evidence that the
    `cascade-qg-ordering.yml`/`sit-gate.yml` slice is ALSO done (`unified-trading-pm@ead69c37d` from batch5 todo 6,
    verified ancestor). Left the outer checkbox `[ ]` — the 24-repo `semver-agent.yml schema-changed` slice remains
    genuinely open (D5-2, conflict-gated, not claimed by batch6 either). Status unchanged (doc has substantial other
    open work).
  - Net: 8 files edited (1 doc archived+resolved already, 3 docs already correctly reconciled with no edits needed). 1
    doc (`ui_build_warm_cache_2026_06_17.md`) reached zero open work and was flipped to `status: resolved`; every other
    doc retains its existing status because real open work remains, matching the todo's "only set status: resolved on a
    doc that genuinely reaches zero" instruction.

- **2026-08-09 (todo 2, slot 2)** — Re-checked all 29 Deferred items (D6-1 through D6-29) against their live source
  docs. **11 blockers cleared** (ready for batch-7 extraction/re-triage — not drafted here per this todo's scope); **18
  confirmed still open** (re-verified, no status change). No item silently vanished.

  **Cleared (ready for batch-7):**
  - **D6-1/D6-2** — batch6 todo 9 landed 2026-08-08, freeing the `scripts/workflow-templates/` rollout mechanism. Both
    conflict-gated items are now unblocked.
  - **D6-3** — batch4's todo 1 landed (`unified-trading-pm@b02ba28c7`) and batch4 itself is now fully done (all 8 todos
    `[x]`, confirmed via checkbox sweep), so `scripts/quickmerge.sh`'s file-mutex is free. Caveat: the source doc's own
    latest note (`quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` step 3) independently flags this
    as "a genuine design/judgment call," not just file-contention-gated — ready for batch-7 consideration but not a
    rubber-stamp extraction.
  - **D6-5** — `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`'s `[DEVOPS] P3` OOM-killer item RESOLVED
    2026-08-08: root access confirmed working (SSM `AWS-RunShellScript` runs as root), kernel/journald logs don't cover
    the 2026-07-30 incident window (host rebooted 2026-08-07), but the rotated classic syslog (`/var/log/kern.log.1`)
    did — grepped the exact incident window, zero OOM-killer matches, kernel OOM ruled out by direct evidence. Item is
    closed (not just deferred); no longer an open operator-gated blocker. (A follow-on "find the real
    `tmux_session_lost` cause" item was opened by that investigation — separate scope, not this todo's to draft.)
  - **D6-11** — `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`'s head `[OPERATOR-DECISION]` item
    RESOLVED 2026-08-08 (operator ruled option (b): non-shared credential file per job). Two new bounded todos now exist
    in that doc ready for batch-7 extraction: a `[SCRIPT] P2` (AO worker-side ADC pinning) and a `[BACKEND] P3`
    (CI-workflow-side audit of the 7 remaining self-hosted repos). batch6's "direction (a)-(d) still unruled" framing is
    now stale.
  - **D6-12** — `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` RECLASSIFIED `assigned_vm: NA → planning`
    2026-08-08 (round7 sweep): the doc's own blocking question ("should this be AO-dispatched or human?") resolved via
    the corpus-wide 2026-08-08 operator default (self-service plan-destination). Both existing todos (BATS warn-only
    phase + re-harden-after-baseline) are unchanged in content and now dispatchable as-is.
  - **D6-15** — the `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` AWS Cost Explorer $-quantification item
    (`[DATA] P2`) is NOT actually incident-hot: the doc's own na-eligibility-audit has called it
    "extraction-ready"/bounded/conflict-clear since 2026-08-01 (a week before batch6 was even authored) and reflagged it
    `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` again on 2026-08-09 — never actually extracted across 7+ subsequent batches.
    batch6's "deliberately left pending the doc's own incident-stabilization" framing does not match the doc's own
    self-assessment; ready for batch-7 extraction.
  - **D6-16** — item 3 (`pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md`, "re-check whether this
    3-doc chain self-resolves") was gated on `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phases 2-3
    landing — that doc is now `status: complete` and archived (`plans/archive/2026_08/`). Item 3's re-check is now
    actionable; ready for batch-7 extraction. (Item 1 stays open — capacity-side root cause still unlanded.)
  - **D6-18** — the blocking external condition (zero self-hosted glue runners registered,
    `fleet_promoter_glue_runner_stall_2026_08_06.md`) has cleared — that doc is now archived. A 2026-08-09 stale-recheck
    sweep on `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` confirms most of the doc's
    previously-blocked verification items are now DONE (real tag minted, live end-to-end verified; stall count dropped
    13→7, not to 0 — real partial progress). One NEW narrower item opened 2026-08-09 (`[DEVOPS] P2`, root-cause the
    residual 7-repo stall) replaces the old 3-item-blocked framing; ready for batch-7 extraction.
  - **D6-21** — the risky item that dominated this doc's re-scoping concern, todo 11 (`staging-lock-check.yml`
    conversion, the doc's own "real landmine" across 16 repos' branch-protection rulesets), has itself LANDED 2026-08-08
    — all 16 rulesets updated, template source converted, verified. Only one optional stretch todo (10, `[INFRA] P3`)
    remains open in the doc. The re-scoping concern this Deferred entry existed for is now moot; ready for batch-7
    extraction (or note the doc as near-fully-complete).

  **Partially cleared / de-escalated (nuance, not a clean flip):**
  - **D6-17** — the specific livelock-recurrence question is CHECKED and CLOSED 2026-08-09 (operator-directed
    interactive session: ~39h of clean `ldr-to-main-promote-fleet` runs, closed as not-recurred). But the doc's own
    remaining `[DEVOPS] P1` "60-min clean-window bar" todo is independently reconfirmed still open by today's
    (2026-08-09) na-eligibility-audit — live-incident observation work, not yet cleared. The acute "too hot to batch"
    framing has de-escalated; one genuine open item remains, so this stays Deferred, not extracted.

  **Confirmed still open (re-verified, unchanged):**
  - **D6-4** — throughput-provisioning vs. concurrency-reduction operator decision: reconfirmed unresolved 2026-08-09 by
    this batch's own todo-1 pass (doc set `archive_exempt: true`, decision itself untouched).
  - **D6-6** — `RETRY_PER_TICK` design tradeoff: reconfirmed genuinely open by today's (2026-08-09) na-eligibility-audit
    ("leave as-is" explicitly still a valid outcome, blocks whole-doc RECLASSIFY on its own).
  - **D6-7** — both `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md` residuals unchanged. Residual 1
    was flagged "worth a RECLASSIFY look" 2026-08-07 but explicitly NOT reclassified this round (rushed-step-4 risk) —
    worth a closer look in batch 7, not yet cleared. Residual 2 unchanged design call.
  - **D6-8** — remaining operator-gated rows (beyond the 2 stale checkboxes already fixed by this plan's todo 1)
    reconfirmed still open via the 2026-08-08 round7 na-eligibility-audit (10 open items re-verified, 7th+ consecutive
    KEEP-NA pass).
  - **D6-9** — F4 (vacuous crons) + `sit_validated_workspace_digest` gap unchanged; the F3 evidence this plan's todo 1
    already added does not close the doc (D5-2's 24-repo semver-agent slice remains genuinely open, conflict-gated).
  - **D6-10** — D1-D4 rulings table: reconfirmed no operator ruling has landed anywhere in the corpus
    (round5-cross-cutting-audit 2026-08-08 explicitly checked and declined to rule blind).
  - **D6-13** — `[A]`/`[B]` sign-off: reconfirmed genuinely open TODAY (2026-08-09 na-eligibility-audit) — the operator
    was walked through the mechanism 2026-08-08 and explicitly declined to sign off; strongest possible confirmation
    this stays a live, current operator-gated decision.
  - **D6-14** — standing 2026-07-14 human-driven ruling: reconfirmed KEEP-NA today (2026-08-09 na-eligibility-audit).
  - **D6-19** — todo 20 billing/load re-measurement: confirmed still the sole open item, still genuinely time-gated
    ("needs a few days of real elapsed usage," per the doc's own latest note).
  - **D6-20** — todo 2 (extend `PYTEST_TIMEOUT=300` to other repos): still lacks a named repo list/acceptance criterion;
    reconfirmed the sole open item by na-eligibility-audit, unchanged.
  - **D6-22** — sole open todo 3 (fleet-wide CI concurrency backstop): last audit 2026-08-07 confirms still open, no
    update since; unchanged.
  - **D6-23 through D6-29** — all 7 unchanged: source docs still `status: open`/`active`, `assigned_vm: NA` (D6-25's
    doc, `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md`, is correctly `status: resolved` and
    archived, matching batch6's own note — not a fresh finding).

  None of D6-1 through D6-29 was dropped or silently reclassified; every id above is accounted for. No follow-up todos
  drafted here per this todo's scope — batch-7 (or whichever future satellite batch) owns extracting the 11 cleared
  items.

- **2026-08-09 (todo 3, slot 15)** — Archived `ci_satellite_ao_dispatch_batch6_2026_08_08.md` via the standard 6-step
  ritual, alongside this finalize doc, in the same commit set. Full breakdown in todo 3's own entry above. Both docs
  move to `plans/archive/2026_08/` as a separate follow-up commit (checkbox flip lands first, per the archival
  discipline's "never combine the flip with the `git mv` in one commit" rule — see
  `issues/checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md` for the incident this avoids).
  **`archive_exempt: true` added transiently** to this doc's own frontmatter so the checkbox-flip commit (this one)
  doesn't trip `check_archive_candidates`'s 0-open-todos gate before the physical move lands — matches that check's own
  documented escape-hatch shape (b), "a doc explicitly routed for archival THROUGH another plan's own dispatched
  reconciliation todo... rather than standalone right now." Removed again in the immediate follow-up `git mv` commit,
  where it becomes moot (the check doesn't scan `plans/archive/`).
