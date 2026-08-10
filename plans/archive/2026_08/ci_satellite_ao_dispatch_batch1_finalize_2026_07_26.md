---
doc_type: plan
title: CI satellite AO batch 1 — finalize (wire the new QG checkers, reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch1_2026_07_26.md — machine-held via depends_on + gate_on_depends: true
  until all 29 of that plan's todos are done. Carries the ONE piece of work the batch deliberately could not contain:
  the single PM `scripts/quality-gates.sh` registration commit for the three new checkers batch-1 todos 2, 6 and 7
  deliver as standalone files (three concurrent todos cannot share that file). Then reconciles each distinct source
  doc's checkboxes/prose independently, re-checks the 6 conflict-gated Deferred items for any whose competing claim has
  since cleared, and archives batch 1 via the standard 6-step ritual.
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-26"
last_updated: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch1_2026_07_26]
gate_on_depends: true
source: >-
  `/ag-closeout-audit ci` run 2026-07-26, per `plans/active/task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan, mirroring the sports/defi/cefi batch precedent.
assigned_role: cicd
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/task_template.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# CI satellite AO batch 1 — finalize

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** All 4 todos shipped. Sibling
> `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md` (the 43-item first ci-tranche AO-dispatch
> batch) completed and archived alongside in the same commit set. All 8 conflict-/time-gated Deferred items (D1-D6,
> D29-D30) were re-checked (todo 3): D1/D4/D5/D29 fully discharged, D2/D6/D30 remain open with a live tracked home in
> their own source docs, D3's file conflict cleared with 4 of 5 held claims ready for a future `ci`-tranche batch to
> extract. The 27 operator-gated/human-only entries (D7-D28, D31-D33) were each re-verified to still have a live home
> (their own source doc, active or resolved-and-archived) — none evaporates with this archival. Successor: none drafted
> here; the still-open Deferred items are ready for a future `ci_satellite_ao_dispatch_batchN` extraction.

> **🔒 GATED, not draft.** (Corrected 2026-08-02 — this banner still read "STATUS: `draft`" long after the frontmatter
> was flipped to `status: active`; the frontmatter was right and the banner was stale.) `gate_on_depends: true` alone
> correctly holds every todo below, so no separate draft flip is needed for this doc.

> **Machine-gated on `ci_satellite_ao_dispatch_batch1_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue anything below until all 29 of that plan's todos are `done`. `sequential: true` because todo
> 1 must land before todo 2's reconciliation cites it, todo 3 needs both, and todo 4 (archival) must run last.
>
> **One scoped exception (operator ruling 2026-07-30): todo 2 is applied INCREMENTALLY** — a source doc may be
> reconciled as soon as its own batch-1 item is verifiably done, without waiting for the rest of batch 1. Todos 1, 3 and
> 4 remain fully gated. Details and the running list of discharged items are on todo 2 itself.

## Todos

- [x] ✅ [INFRA] P1. **Register the three new QG checkers into PM `scripts/quality-gates.sh` in ONE commit.** —
      unified-trading-pm@3ee5039ff (checker wiring, `scripts/quality-gates.sh`) + unified-trading-pm@51808a4a6
      (forward-ported `_RUN_INIMAGE_QG` guard into `configs/cloudbuild-api-template.yaml` — unblocked a pre-existing
      fresh cloudbuild-drift regression the new gate would otherwise have caught day-one).
      `bash scripts/quality-gates.sh --no-fix` ran GREEN on PM at HEAD 3ee5039ff (1851 tests passed, all three new
      post-gates ✅ at-or-below baseline, 0 accumulated post-gate failures). Each checker's synthetic-new-violation unit
      test passed (`test_exits_nonzero_on_new_orphan_beyond_baseline`,
      `test_synthetic_template_lags_repo_case_fails_at_seeded_baseline`,
      `test_synthetic_new_site_fails_at_seeded_baseline`). Three baselines already committed by batch-1 todos 2/6/7;
      unchanged by this todo. Batch-1 todos 2, 6 and 7 each deliver a standalone checker plus a proven red/green run but
      deliberately do NOT wire in — three concurrent todos cannot share one file (CLAUDE.md § Plans: concurrent
      same-priority todos must touch different files). Add all three invocations here: `check_dispatch_listeners.py`
      (every dispatched `event_type` has a listener in the resolved target repo), `check_cloudbuild_template_drift.py`
      (rendered template vs each consumer's committed `cloudbuild.yaml`), `check_no_swallowed_credential_fetch.py` (no
      `2>/dev/null || true` around a credential fetch). Each must be **baseline-ratcheted** (fails only on NEW
      violations, per the `doc_reference_baseline.yaml` / `defi_address_citation_baseline.yaml` convention) so the gate
      does not turn red on day-one pre-existing debt. **Done when**: `bash scripts/quality-gates.sh --no-fix` on PM is
      GREEN with all three wired, each checker is proven to fail the gate on a synthetic new violation, and the three
      baselines are committed.
- [x] ✅ [REVIEW] P1. **Reconcile all 29 todos' source docs.** Each batch-1 todo ends with `Source:` naming one or more
      docs (five todos cite two sources each — the `check_strict_quickmerge` pair, the `full-workspace-sit` pair, the
      cloudbuild-template pair, the fleet version/tag census pair, and the codex `ci-cd-flow.md` todo which cites FOUR).
      For each: flip the corresponding checkbox or annotate the corresponding prose section in EVERY cited doc, citing
      the batch-1 commit that shipped it — **verify the cited commit exists and is an ancestor of
      `origin/live-defi-rollout` before citing it** (`git merge-base --is-ancestor`). Then, per doc, re-check whether it
      now has zero open work **in checkbox AND prose form** — 12 of this tranche's orphans express all their remaining
      work as numbered prose with no checkboxes, so a checkbox count is not an answer. Only set `status: resolved` on a
      doc that genuinely reaches zero. **Done when**: every cited doc is flipped/annotated with verified evidence, and
      each doc that genuinely reaches zero open work is `status: resolved`. **DONE 2026-08-09** — all 29 of 29 items
      reconciled (see the discharge list below); evidence unified-trading-pm@8750f0106 (25 items advanced this
      session) + this commit (item 30 resolved-with-no-edit-needed, parent checkbox flipped).
  - **⚖️ OPERATOR RULING 2026-07-30** (recorded in this doc's own Progress Log,
    `ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`, 2026-08-02 entry) **— THIS TODO IS EXEMPT FROM THE
    `gate_on_depends` HOLD; APPLY IT INCREMENTALLY.** Reconciliation of an individual source doc may proceed the moment
    that item's own batch-1 work is verifiably done — it does NOT have to wait for all of batch 1 to finish. The
    rationale is that a batch-1 item that shipped weeks ago but whose source-doc checkbox is still `[ ]` is exactly the
    false-progress this rule exists to prevent, and holding the flip behind an unrelated sibling todo manufactures that
    state. **The `gate_on_depends: true` frontmatter is deliberately UNCHANGED** — it still correctly holds todos 1, 3
    and 4 (the single QG-registration commit, the deferral re-check, and archival), all of which genuinely need the
    whole batch done first. The carve-out is scoped to this todo only. Per-item rule when applying it: verify the cited
    commit is a real ancestor of `origin/live-defi-rollout` BEFORE flipping, and do not mark this parent todo `[x]`
    until every one of the 29 has been reconciled.
  - **All 29 of 29 items discharged — verified/fixed 2026-08-09 (this session, via 10 parallel read-only research agents
    covering every one of the 29 `Source:` citations, plus the original 3 verified 2026-08-02). Recorded here so this
    todo's completion is auditable rather than a bare checkbox flip. Items 4-30 below were newly reconciled this
    session; where a source doc's own citation was missing/placeholder/WRONG, it was fixed in this session's commit
    (noted per item):**
    1. `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` `[DEVOPS] P1` ("Ban the `|| true`
       credential idiom") — flipped `[x] ✅` in the source doc. Evidence re-verified: `unified-trading-pm@c91844b09`,
       confirmed ancestor. **Correction (2026-08-09): the same doc's SECOND `[DEVOPS] P1` (0-runners-listening pool
       alert) is now ALSO discharged — see item 4. The earlier note here claiming it was "still open" was stale by one
       day (na-eligibility-audit flipped it 2026-08-03).**
    2. `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` `[DOC] P2` (`ci-cd-flow.md` LDR→main narrative +
       staging re-entry procedure) — flipped `[x] ✅`. Evidence re-verified: `unified-trading-pm@97970974e`, confirmed
       ancestor. (One of 4 sources for the combined ci-cd-flow.md todo at batch-1 line 397 — see item 16 for the other
       3.)
    3. `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` `[REVIEW] P3` (hardcode the PM dispatch target in
       `agent-runner.yml` / `sit-gate.yml`) — flipped `[x] ✅`. Evidence re-verified: `unified-trading-pm@cb5e944f0`,
       confirmed ancestor.
    4. `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`'s second `[DEVOPS] P1` ("A self-hosted
       pool with 0 runners listening must page on its OWN cause") — already flipped `[x] ✅` in the source doc, citing
       `unified-trading-pm@80f397278`, confirmed ancestor. No edit needed.
    5. `plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` `[DEVOPS] P2`
       (rollout-cloudbuild.py refuses to drop live content) — already correctly flipped citing
       `unified-trading-pm@ddf0b89f4`, confirmed ancestor. No edit needed.
    6. Same doc, `[DEVOPS] P1 + P3` (cloudbuild template-vs-consumer drift checker) — **fixed this session**: the P1
       item's citation was a literal unfilled placeholder (`unified-trading-pm@(this commit — see plan)`) and the P3
       item had no citation at all; both now cite `unified-trading-pm@8f15ff124`, confirmed ancestor. Also flipped the
       doc's frontmatter `status: open` → `resolved` (all todos `[x]`, already carries an
       `ARCHIVED 2026-08-07 — RESOLVED` banner that the frontmatter had never caught up to).
    7. `plans/archive/issues/github_actions_deploy_sa_overbroad_secret_access_2026_07_24.md` `[BACKEND] P3` (sync
       `gcp_service_accounts.yaml` against live IAM) — already `[x]` per the doc's own convention (cites the tracking
       plan rather than duplicating the SHA). Evidence re-verified: `deployment-service@0b7d03c`, confirmed ancestor.
       Follow-up doc confirmed to exist:
       `issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`.
    8. `plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` `[DEVOPS] P2`
       (`sit_retry_cap` escalation) — checkbox correctly STAYS `[ ]`: the item bundles the bounded fix (done, evidence
       `unified-trading-pm@2e5a42479` + `agent-orchestrator@dbdccb6`, both confirmed ancestors, live-proven end-to-end
       via `agt-d37ed9`) with a genuinely still-open design-call sub-clause (ruled 2026-08-07 but not yet scoped into an
       implementation todo). Not a stale mark — verified honest, no edit needed.
    9. Same doc, `[DEVOPS] P2` (`full-workspace-sit` `SIT_VALIDATED` messaging correction) — already correctly flipped
       `[x] ✅` citing `system-integration-tests@33cf6f0`, confirmed ancestor. No edit needed. (Paired with item 10.)
    10. `plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` `[DEVOPS] P2`
        sub-finding (cancelled-run clobbers real success) — already correctly flipped citing
        `unified-trading-pm@ab22e725b6141e4ccd7b11018134e7e8bbb90961` + `@18a55dd49c12dbf71241696b1fbfd5e8aa2ee37d` +
        `system-integration-tests@33cf6f0`, all confirmed ancestors. No edit needed.
    11. Same doc, `[DEVOPS] P3` (sit-gate-stuck-detector) — already correctly flipped citing
        `unified-trading-pm@409c35437`, confirmed ancestor. No edit needed.
    12. `plans/archive/issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` `[DEVOPS] P2`
        (`check_strict_quickmerge.py` fails open on a bad range) — **fixed this session**: was a generic "see batch1 for
        execution" deferral with no commit named; now cites `unified-trading-pm@fd52877f6`, confirmed ancestor. (Paired
        with item 13.)
    13. `plans/archive/issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md` "Fix direction 3" — already
        independently correct (resolved 2026-07-30 via direct code re-verification, not a batch-1 citation); cross-
        referenced to `fd52877f6` for consistency. No edit needed beyond the cross-reference already present.
    14. `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` `[DEVOPS] P3` (husky UI repos'
        strict-quickmerge guard) — already correctly flipped with full citations: `deployment-ui@a3268d0` +
        `unified-trading-system-ui@563f6238` + `unified-trading-pm@69b858288`, all confirmed ancestors. No edit needed —
        this is the citation style item 12/16 were upgraded to match.
    15. `plans/archive/issues/mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md` `[INFRA] P3` third item
        (deployment-api's two unguarded secondary cloudbuild configs) — already `[x]` (archived doc). Evidence
        re-verified: `deployment-api@a3f5822`, confirmed ancestor. No edit needed (flagged a 1-day archive-before-
        execution documentation-trail gap, not a functional gap — the fix is real and shipped).
    16. `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` `[DEVOPS] P3` (ci-cd-flow.md
        WARN-default line, one of the 4 sources for the combined todo at batch-1 line 397) — **fixed this session**:
        same generic-deferral gap as item 12, now cites `unified-trading-pm@97970974e`, confirmed ancestor. Combined
        with items 2, 19 and 20 below, all 4 of that todo's sources are now reconciled.
    17. `d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` (archived) steps 3+7
        (`sync-manifest-versions.py` deleted, `agent-orchestrator::app_version()` fixed) — **fixed this session**:
        citation was a literal placeholder (`unified-trading-pm@<see plan checkbox for sha>`); now cites
        `unified-trading-pm@45b25799b` + `agent-orchestrator@12e0f2e`, both confirmed ancestors.
    18. Same doc, census addendum (`check_workspace_pyproject_pin_drift.py` DELETED, superseded by
        `assert_version_coherence.py`) — **fixed this session**: doc was stuck at "followup todo filed" with no
        resolution recorded; appended a resolution note citing `unified-trading-pm@bd0e44dd3`, confirmed ancestor.
    19. Same doc, census addendum (`check_sdk_version_alignment.py`'s D13-blind function REMOVED) — **fixed this
        session**: same gap as item 18; appended a resolution note citing `unified-api-contracts@44ba64b3`, confirmed
        ancestor, cross-linking `check_sdk_version_alignment_stale_interfaces_and_missing_pins_2026_08_03.md`.
    20. Same doc, "Fleet version/tag-state census (2026-08-02)" (step 2, paired with
        `post_cutover_silent_assumption_sweep_2026_07_23.md`'s "Reconcile the ~4 weeks of missing tags") — already
        correct in both docs (full dated (a)/(b)/(c) table present, cross-linked;
        `main_backmerge_to_ldr_silent_failure_2026_08_02.md` confirmed filed). No edit needed.
    21. `ui_build_warm_cache_2026_06_17.md` `[SCRIPT] P3` (base-ui.sh one automatic retry) — already correctly flipped
        citing `unified-trading-pm@80148edde`, confirmed ancestor. No edit needed.
    22. `cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md` (negative test) — **fixed this
        session**: evidence prose never named the shipping commit; inserted `unified-api-contracts@7450e744`, confirmed
        ancestor.
    23. `post_cutover_silent_assumption_sweep_2026_07_23.md` `[INFRA] P1` (Docker version tag no longer re-pointed) —
        already correct, dated AR-probe evidence recorded in-doc (verification-only, no commit). No edit needed.
    24. Same doc, `[INFRA] P2` (instruments-service `0.0.0.dev0` publish path) — **fixed this session, a genuine
        correctness bug**: the cited `instruments-service@7d005520` is **NOT** an ancestor of `origin/live-defi-rollout`
        (it only survives on the orphaned branch
        `origin/wip-preserve/slot-5-instruments-service-diverged-20260805T111826Z` from the 2026-08-05 slot-5 divergence
        incident). The identical content landed on LDR under a rewritten SHA; replaced the citation with
        `instruments-service@79b7d5b4`, confirmed ancestor.
    25. `post_cutover_silent_assumption_sweep_2026_07_23.md` `[INFRA] P1` (dispatch delivery observable,
        `check_dispatch_listeners.py`) — already correct (cites the tracking plan per the doc's own convention, evidence
        `unified-trading-pm@613f79960` confirmed ancestor via batch-1's own back-reference). No edit needed.
    26. `github_actions_operator_gated_followups_2026_07_17.md` `[VERIFY] P0` (`measure-billed-notify-cost.sh`) —
        **fixed this session, a genuine open→closed transition**: flipped `[ ]` → `[x] ✅` with the full 2026-08-09
        measurement (`DEDUP_BILLED_23D=2019`, self-hosted-glue premise moot/retired). Also struck through the stale
        duplicate row 6 in the doc's "Cannot be done yet" table.
    27. Same doc, Deferred row 14 (`ldr-docs-gate.yml` schedule retarget confirmed firing) — already correct. No edit
        needed.
    28. Same doc, `[REVIEW] P0` / D2 (CI/CD event-ledger consumer found) — checkbox already `[x]` correctly citing
        `unified-trading-pm@4cbf2006d`. **Fixed this session**: two OTHER spots in the same doc (the D-table's D2 row,
        and the "Findings parked for later" table's `persist_cicd_event_ledger_read_modify_write_race` row) still read
        "unanswered"/"NEW (D2)", contradicting the already-correct checkbox — both updated to the 2026-08-02 resolution.
        Also covers Deferred-after-07-23 row 5 (one of the 4 ci-cd-flow.md sources, already correct citing `97970974e`)
        and `github_actions_staging_machinery_shutdown_2026_07_24.md`'s `[DOC] P2` (the last of the 4 ci-cd-flow.md
        sources, already correct citing `97970974e`, doc already archived at zero open work) — both verified this
        session, no edit needed.
    29. `plans/archive/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md` — already correctly
        archived/resolved, content matches batch-1's claim (live-verified `SKIPPED` not `FAILURE`). No edit needed.
    30. batch-1's `check_dispatch_listeners.py` GHA `${{ }}`-expression fix (batch-1 line ~272-284) — **re-checked and
        already fully satisfied, no edit needed anywhere.** Its two cited `Source:`s are (a) "this plan's own todo 2" —
        self-referential, batch-1 IS the record, nothing external to flip; (b)
        `post_cutover_silent_assumption_sweep_2026_07_23.md` `[REVIEW] P3` "discovered while closing it" — this is the
        SAME `[REVIEW] P3` checkbox as item 3 above (hardcode the PM dispatch target in
        `agent-runner.yml`/`sit-gate.yml`, `unified-trading-pm@cb5e944f0`), not a distinct sub-item: the GHA-expr bug
        was found as a side-discovery while working that item, and that checkbox was already correctly flipped `[x] ✅`
        in the 2026-08-02 baseline pass. No separate doc-side action exists to take.
  - **All 29 of 29 items now reconciled (2026-08-09).**
- [x] ✅ [REVIEW] P1. **Re-check the 6 conflict-gated Deferred items (D1-D6) and the 2 time-gated ones (D29-D30).** Each
      names the specific competing claim it collided with, so this is a few greps and reads, not fresh investigation. D1
      is discharged by todo 1 above. For D2-D6: has the competing side shipped, been superseded, or been ruled on? In
      particular D3's five held `scripts/quickmerge.sh` claims are now unblocked as a FILE (batch-1 todo 1 has landed) —
      re-extract them one per subsequent batch in the order D3 lists, and check whether the parked operator questions on
      D3(2)/D3(3) have been answered. For D29: the two-week billing re-pull's earliest date was ~2026-07-31 — if that
      has passed, it is now extractable. **Do NOT draft the follow-up todos here** — this plan's scope is
      reconciliation, not fresh drafting; note each as ready-for-batch-2 instead. Do NOT re-ask an operator question
      that was already escalated; just record that the re-check happened and it is still unanswered. **Done when**: each
      of D1-D6 and D29-D30 has either (a) a note that it is ready for batch-2 extraction because its blocker cleared, or
      (b) a re-verified confirmation the conflict/date is still open. **DONE 2026-08-09** — all 8 re-checked (D1 already
      discharged; D2/D6/D30 confirmed still open; D3 partially unblocked; D4/D5/D29 now fully discharged).
  - **Per-item findings (2026-08-09, this session):**
    - **D1** — already discharged per todo 1 above (the 3 checkers wired into PM `scripts/quality-gates.sh` in one
      commit). No new action.
    - **D2** — `post_cutover_silent_assumption_sweep_2026_07_23.md` F4's `digest-drift-sweep` non-convergence sub-item.
      The FILE conflict with todo 3 (`scripts/quality-gates.sh`) has cleared (batch-1 fully landed), but the item itself
      is still an open-ended root-cause investigation, not a bounded fix — confirmed via
      `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` (`status: open`, na-eligibility-audit 2026-08-06
      "KEEP-NA, valid — open-ended investigation… no bounded fix identified") and the 2026-08-08 na- eligibility-audit
      round7 note that the F4 item "bundles a plausibly-bounded sub-part… with a genuinely open-ended sub-part… not
      split out or reclassified here." The escalated operator question "(3) who owns `digest-drift-sweep.yml` edits" has
      no recorded answer anywhere in the corpus. **Still open — not ready-for-batch-2** (the mechanism analysis itself
      remains un-owned).
    - **D3** — the file conflict (batch-1 todo 1 owning `scripts/quickmerge.sh`) has CLEARED (batch-1 fully landed
      2026-08-09). 4 of the 5 held claims are ready for batch-2 re-extraction in the doc's own listed order; sub-item
      (2) (STAGE 1.6 dormancy-aware dep gate) is already DONE (na-eligibility-audit 2026-08-01,
      `unified-trading-pm@b3abf1bd5`) and should be dropped from the re-extraction list, matching the doc's own existing
      note. Sub-item (3)'s parked question (the MTDS `DEPLOYMENT_ENV` race's reproducer) is still unanswered —
      re-verified via `mtds_deployment_env_race_survives_single_worker_2026_07_23.md` (`status: open`,
      na-eligibility-audit 2026-08-06 "non-deterministic race, substance-unbounded, prior verdicts stand"). Sub-item (5)
      (quickmerge sentinel-race fix 1/fix 3) remains operator-gated, unimplemented — see D30. The escalated operator
      question "(2) `scripts/quickmerge.sh` extraction order (6 competing claims)" has no single recorded ruling, but 3
      of the 6 original claims (D1, D4, D5) have organically resolved via separate batches without needing one — noting
      this, not re-asking it.
    - **D4** — delete `scripts/dev/hooks/pre-push-strict-quickmerge.sh` + repoint referrers. **Now fully DISCHARGED**:
      landed 2026-08-09 via `ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md` todo 1
      (`unified-trading-pm@b02ba28c7`, verified ancestor), source doc
      `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` flipped `status: resolved` and archived.
      No batch-2 action needed.
    - **D5** — `check_strict_quickmerge.py` dirty-deps carve-out trailer. **Already fully DISCHARGED** (pre-dates this
      session): operator ruled Option 2 (2026-07-29), shipped `unified-trading-pm@bbe9a9871` (2026-07-30), source doc
      `check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md` is `status: resolved` and archived. No
      batch-2 action needed.
    - **D6** — disable/fix the 4 F4 vacuous crons + diagnose `digest-drift-sweep`. The file conflict with todo 10
      (`sit-debounce-trigger.yml`) has cleared (batch-1 landed), and the "disable 4 named no-op crons" sub-part is a
      bounded, deterministic task ready for batch-2 extraction — but re-verified via
      `post_cutover_silent_assumption_sweep_2026_07_23.md` that no per-cron disable-vs-fix ruling has ever been made
      (todo still `[ ]`), and the bundled `digest-drift-sweep` diagnosis sub-part stays unbounded (same root cause as
      D2). **Ready for batch-2 extraction as a bounded item, split from the unbounded digest-drift-sweep half** — not
      drafted here per this todo's scope.
    - **D29** — two-week billing-ledger re-pull vs the Phase-0 baseline (earliest ~2026-07-31, now past). **Now fully
      DISCHARGED** — actually completed 2026-08-09 (today, a parallel slot-28 session), per
      `github_actions_operator_gated_followups_2026_07_17.md`'s Phase-5 entry: fleet
      $35.51/day (Jul1-15 baseline) →
      $12.72/day (Aug1-8), -64.2%, landing the ~$300-400/mo target. No batch-2
      action needed.
    - **D30** — re-observe the 27-consecutive-loss quickmerge retry storm under similarly heavy multi-slot contention
      before closing `quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md`. Re-verified: doc
      still `status: open`, fix 1 (content-hash QG fast-path) and fix 3 (serialized PM-doc-push queue) remain
      unimplemented and operator-gated ("do NOT dispatch blind: quickmerge is high-blast-radius shared ship infra"); no
      re-observation event under heavy contention has been logged anywhere in the corpus since the 2026-07-22
      partial-progress note first raised it. **Still open, unchanged.**
- [x] ✅ [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch1_2026_07_26.md`** via the standard 6-step ritual (CLAUDE.md
      § plan archival): migrate any still-unresolved Deferred item to a tracked todo elsewhere (todo 3 above should have
      resolved or re-confirmed D1-D6/D29-D30 — verify none silently vanishes, and confirm the 27 operator-gated /
      human-only entries D7-D28 and D31-D33 each still have a live home) → add the archive banner → run the
      codex-alignment check (batch-1 todo 17 changed `/codex/08-workflows/ci-cd-flow.md`, so confirm that landing is
      reflected and no NEW durable contract is undocumented) → update CLAUDE.md/codex if any batch-1 todo established a
      new contract (candidates: the three new QG checkers from todo 1, and the glue-pool liveness alarm) → grep the
      corpus for every referrer of `ci_satellite_ao_dispatch_batch1_2026_07_26` and repoint each to the archived path →
      clear `locked_by` (already empty; confirm). **Done when**: the plan is in `plans/archive/2026_08/`, every corpus
      referrer resolves, `check_reference_paths.py` has not regressed, and this finalize doc is archived alongside it in
      the same commit. **DONE 2026-08-09.** Step-by-step: (1) verified all D1-D6/D29-D30 + D7-D28/D31-D33 each have a
      live, genuinely-open-or-resolved home in their own source doc (spot-checked every doc named in the Deferred table
      still exists under `plans/active/` or `plans/archive/`; verified D2/D3's 4 remaining sub-items/D6's bounded
      sub-part each still carry a real `- [ ]` todo in their own doc, not just a mention here — none evaporates).
      (2)/(3)/(4) codex-alignment: `/codex/08-workflows/ci-cd-flow.md`'s staging-re-entry + "BLOCKS by default" language
      (batch-1 todo 17) was already landed and current — no edit needed there; the two genuinely-new-and-undocumented
      contracts (the 3 QG checkers now wired into PM `quality-gates.sh`, and the `glue-pool-starvation-monitor.yml`
      alarm) were NOT yet documented anywhere in codex — added a new § "CI-hardening post-gates" to
      `/codex/06-coding-standards/quality-gates.md` and a new reporter row to `/codex/04-architecture/ci-alerting.md`'s
      carrier table (`unified-trading-pm@<this commit set>`). (5) grepped the full workspace corpus (all repos under
      this slot) for both docs' paths: repointed every LEADING-SLASH
      `/plans/active/ci_satellite_ao_dispatch_batch1(_finalize)?_2026_07_26.md` reference in 10 active corpus docs (+ 2
      `.github/workflows/*.yml` comment mentions) to the new `/plans/archive/2026_08/...` path; left pre-existing bare
      (non-leading-slash) filename mentions untouched — those are pre-existing `check_reference_paths.py` format-ratchet
      debt (`plans/archive/` is gate-excluded per the 2026-08-02 ruling; a bare mention isn't a broken link, and fixing
      format debt corpus-wide is a separate, larger effort, not part of a single archival's scope);
      `plans/active/INDEX.md` and `DOC_INDEX.generated.md` are auto-regenerated (never hand-edited) so need no manual
      fix; left the machine-generated `scripts/quality_gates/evidence_backed_completion_baseline.yaml` grandfathered
      entries alone (regenerated by its own checker, not a corpus doc reference). (6) `locked_by` confirmed empty on
      both docs.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes; ratchet-baseline convention
- `/codex/08-workflows/ci-cd-flow.md` — the pipeline contract batch-1 todo 17 edits
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-09 (this session, slot 18) — todo 4 done, plan archived.** Archived both this doc and
  `ci_satellite_ao_dispatch_batch1_2026_07_26.md` per the standard 6-step ritual. Full step-by-step evidence recorded on
  the todo itself. `status: active` → `complete` on both docs; archive banners added; codex updated (`quality-gates.md`
  § "CI-hardening post-gates", `ci-alerting.md` reporters table); 10 active corpus docs + 2 workflow-comment mentions
  repointed to the new `/plans/archive/2026_08/...` path. All 4 finalize todos now `[x]`.
- **2026-08-09 (this session, slot 18) — todo 3 done.** Re-checked all 6 conflict-gated Deferred items (D1-D6) and the 2
  time-gated ones (D29-D30) — **DONE, checkbox flipped `[x]`**. D1 already discharged (todo 1). D4 (delete
  `pre-push-strict-quickmerge.sh`) and D5 (`check_strict_quickmerge.py` dirty-deps carve-out) are now fully DISCHARGED —
  both landed and their source docs archived (D4 today via a parallel batch4-finalize session,
  `unified-trading-pm@b02ba28c7`; D5 pre-dates this session, `unified-trading-pm@bbe9a9871`). D29 (two-week
  billing-ledger re-pull) is now fully DISCHARGED — actually completed today by a parallel slot-28 session: fleet
  $35.51/day → $12.72/day, -64.2%. D3's file conflict has cleared (batch-1 fully landed) — 4 of its 5 held
  `scripts/quickmerge.sh` claims are ready for batch-2 re-extraction (1 of the 5 was already done pre-session). D2 and
  D6 both re-verified still open: the underlying `digest-drift-sweep` non-convergence root-cause investigation remains
  unbounded/un-owned in both (no operator ruling on file for "who owns digest-drift-sweep.yml edits"); D6's bounded
  sub-part (disable 4 named no-op crons) is separable and ready for batch-2 extraction on its own. D30 re-verified still
  open — no re-observation under heavy multi-slot contention has occurred; fixes 1/3 remain operator-gated and
  unimplemented. Per this todo's own scope, no follow-up todos were drafted — findings recorded inline on the todo for
  batch-2/archival (todo 4) to consume. Full per-item findings on the todo itself.
- **2026-08-09 (this session)** — Todo 2 advanced from 3/29 to 29/29 discharged items — **DONE, checkbox flipped
  `[x]`**. Dispatched 10 parallel read-only research agents, one per source-doc group, each verifying its assigned
  batch-1 claims against the actual source doc and checking cited-commit ancestry via `git merge-base --is-ancestor`.
  Applied the fixes their reports surfaced: filled 3 unfilled-placeholder commit citations
  (`cloudbuild_template_behind_repos_rollout_would_regress_fleet`'s P1 item,
  `d13_orphaned_version_readers_and_manifest_drift`'s steps-3+7 item,
  `provenance_gate_override_and_unenforced_quickmerge_hook`'s two generic-deferral items); added 2 missing citations to
  already-`[x]` items (`cloudbuild_template...`'s P3 item, `cassette_drift_check_calls_deleted_script_and_swallows_it`);
  appended 2 resolution notes for census-addendum rows that were stuck at "followup filed" despite the followup having
  since shipped (`d13...`'s pyproject-pin-drift and sdk_version_alignment deletions); **corrected one genuinely WRONG
  citation** — `post_cutover_silent_assumption_sweep`'s instruments-service item cited `instruments-service@7d005520`,
  which is NOT an ancestor of `origin/live-defi-rollout` (only survives on an orphaned 2026-08-05 divergence branch) —
  replaced with the rewritten equivalent `79b7d5b4`, which is; flipped one genuine open→closed checkbox
  (`github_actions_operator_gated_followups`'s `[VERIFY] P0` measure-billed-notify-cost item, plus its stale duplicate
  table row); fixed 2 stale contradicting spots in the same doc where the D2 event-ledger-consumer resolution wasn't
  reflected outside its own already-correct checkbox; flipped
  `cloudbuild_template_behind_repos_rollout_would_regress_fleet`'s frontmatter `status: open` → `resolved` (already
  archived with a RESOLVED banner, all todos `[x]`, the frontmatter had simply never caught up). 20 of the first 28
  items were already correctly reconciled pre-session — verified, not re-touched. The 29th item
  (`check_dispatch_listeners.py`'s GHA `${{ }}`-expression fix) needed no agent/edit at all on a closer re-read: both
  its cited `Source:`s resolve to work already accounted for (a self-reference to batch-1's own record, and the SAME
  already-`[x]` `[REVIEW] P3` checkbox as item 3 — the bug was a side-discovery while closing that item, not a distinct
  doc entry). All 29 of 29 now genuinely reconciled; parent todo flipped `[x]`.
- **2026-07-26** — Drafted alongside `ci_satellite_ao_dispatch_batch1_2026_07_26.md` by `/ag-closeout-audit ci`
  (autonomous mode). Both are `status: draft`; neither is dispatched. Todo 1 exists because the batch's conflict-check
  found PM `scripts/quality-gates.sh` claimed by three separate new checkers — the documented remedy for
  partial-parallelism (parallel work in plan A, the shared gated step in plan B via `depends_on` +
  `gate_on_depends: true`).
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **2026-08-02 (operator ruling executed)** — Recorded the ruling that todo 2's reconciliation is exempt from the
  `gate_on_depends` hold and applies incrementally, per source doc, as each batch-1 item verifies done.
  `gate_on_depends` frontmatter left `true` on purpose — todos 1/3/4 still need the whole batch. Verified and recorded
  the first 3 of 29 discharged items (`silent_failures_…_2026_07_17.md` `[DEVOPS] P1`;
  `post_cutover_silent_assumption_sweep_2026_07_23.md` `[DOC] P2` and `[REVIEW] P3`); all three were already flipped in
  their source docs by the 2026-08-01 `/na-eligibility-audit ci` sweep, and all three cited commits (`c91844b09`,
  `97970974e`, `cb5e944f0`) were re-verified this session as real ancestors of `origin/live-defi-rollout` before being
  recorded. No source-doc checkbox needed changing as a result. Also corrected the stale "STATUS: `draft`" banner, which
  contradicted this doc's own `status: active` frontmatter. Separately re-checked the ruling's third item — flagging
  `ci_satellite_ao_dispatch_batch2_2026_07_29.md`'s todo 4(b) as stale-as-drafted: **already done and no edit made**.
  That plan completed and was archived to `/plans/archive/2026_07/`, and its todo 4 sub-item (b) already carries the
  verbatim finding ("the 2 SPECIFIC 2026-07-17 offenders named in this todo … are STALE", with the live re-verification
  that `deployment-ui` has no open promote PR).
- **context-scout 2026-08-03**: re-confirmed context_scope (5 entries) unchanged — still matches this doc's own "Codex
  SSOTs" section; no source-code paths added (`_finalize` gate doc, skip-source carve-out).
- **2026-08-09 — todo 1 done.** Wired all three batch-1 checkers into `scripts/quality-gates.sh` as blocking,
  baseline-ratcheted post-gates (`unified-trading-pm@3ee5039ff`). Wiring `check_cloudbuild_template_drift.py` first
  surfaced a genuine over-baseline regression: `client-reporting-api`'s cloudbuild.yaml had locally grown a
  `_RUN_INIMAGE_QG` in-image-QG-toggle guard (landed via `99171ca`, unrelated concurrent work) that was never
  forward-ported into the shared `configs/cloudbuild-api-template.yaml` — the exact pattern already proven in
  `cloudbuild-service-template.yaml`'s own quality-gates step. Since the checker's own baseline-write clamps DOWN only
  (never raises), the only path to GREEN was fixing the drift, not re-baselining around it — forward-ported it
  (`unified-trading-pm@51808a4a6`), re-verified the fleet-wide drift scan returned to 0 regressions across all 20
  consumers, then shipped both as separate commits via one quickmerge call. Full
  `bash scripts/quality-gates.sh --no-fix` GREEN at HEAD `3ee5039ff` (1851 tests passed, all three new post-gates
  at-or-below baseline).
