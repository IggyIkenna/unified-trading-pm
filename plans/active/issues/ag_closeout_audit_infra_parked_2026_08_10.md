---
doc_type: issue
title:
  "2026-08-10 /ag-closeout-audit infra + ci run — 0 real orphans; 8 corpus-wide linkage-only gaps mechanically fixed
  across both tranches"
summary: >-
  infra's 2026-08-10 pass found 9 `check_ag_closeout_linkage.py`-confirmed orphans at run start; all 9 turned out to be
  linkage-only gaps (5 batch/finalize plans + `codex_vs_repo_docs_ssot_audit` finalize + `reference_path_convention`
  finalize missing a `related:` link to `infra_consolidated_closeout_2026_07_25.md`, plus 1 self-dispatched issue doc
  `broad_except_as_binding_form_blind_spot_2026_08_09.md` with real open AO-dispatched work just missing the same link)
  — 0 genuine orphans remain for infra after the mechanical fix. ci's pass found 3 orphans at run start (its
  consolidated-closeout doc is archived, `plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md` — a known
  pre-existing condition, not a new gap); all 3 were the same linkage-only shape (a finalize plan + its paired issue doc
  + a self-dispatched openapi-regen findings doc) — 0 genuine orphans remain for ci either.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ci, ag-closeout-audit, parked-findings, linkage-fix, clean-run]
related:
  [
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/active/infra_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md,
    /plans/active/reference_path_convention_2026_07_23_finalize_2026_08_08.md,
    /plans/active/issues/broad_except_as_binding_form_blind_spot_2026_08_09.md,
    /plans/active/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26_finalize_2026_08_08.md,
    /plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md,
    /plans/active/issues/venv_workspace_openapi_regen_batch11_findings_2026_08_09.md,
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /plans/active/infra_satellite_ao_dispatch_batch15_2026_08_10.md,
    /plans/active/infra_satellite_ao_dispatch_batch15_finalize_2026_08_10.md,
    /plans/archive/2026_08/issues/host_root_disk_full_transient_2026_07_13.md,
    /plans/active/issues/s5_7_required_docs_gaps_2026_07_29.md,
    /plans/active/issues/host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md,
    /plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md,
    /plans/active/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md,
  ]
created: "2026-08-10"
author:
  "slot-26 (ag_closeout_auditor, all-tranche mode) + slot-20 (ag_closeout_auditor, infra tranche, dispatch agt-7788a0,
  second run same day)"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.05
estimate_calibrated_ai_days: 0.04
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope: [/scripts/plan-hygiene/check_ag_closeout_linkage.py]
source: >-
  `/ag-closeout-audit all` run 2026-08-10 (ag_closeout_auditor scheduled worker, slot 26, one-shot, no $TRANCHE set).
---

# Parked findings — 2026-08-10 `/ag-closeout-audit infra` + `ci` (part of the `all`-mode run)

## Resolved this run (not parked findings — mechanical linkage fixes, 0 real orphans remain)

**infra (9 fixed)**: `infra_satellite_ao_dispatch_batch12_2026_08_09.md`, `…batch12_finalize`, `…batch13_2026_08_09.md`,
`…batch13_finalize`, `codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md`,
`reference_path_convention_2026_07_23_finalize_2026_08_08.md` (all missing a `related:` link to
`infra_consolidated_closeout_2026_07_25.md`, added) + `issues/broad_except_as_binding_form_blind_spot_2026_08_09.md`
(self-dispatched, `assigned_vm: planning`, 2 real open todos — same missing-link gap, fixed).

**ci (3 fixed)**: `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26_finalize_2026_08_08.md` +
`issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` (missing a `related:` link to the ARCHIVED
`ci_consolidated_closeout_2026_07_25.md` — still a valid link target per `check_ag_closeout_linkage.py`'s own design)

- `issues/venv_workspace_openapi_regen_batch11_findings_2026_08_09.md` (self-dispatched, `assigned_vm: planning`, 2 real
  open P3 todos — same gap).

All fixes verified via re-run of `check_ag_closeout_linkage.py`: infra and ci both show 0 orphans in the post-fix
corpus-wide sweep (14 total remaining, all in other tranches — see `ag_closeout_audit_ao_parked_2026_08_10.md`,
`…cross_cutting_parked_2026_08_10.md`, `…defi_parked_2026_08_10.md`, `…tradfi_parked_2026_08_10.md`).

## Second dispatch delta — infra only (2026-08-10, ~4.7h later, slot 20, `agt-7788a0`)

A second same-day `ag_closeout_auditor` dispatch for `infra` specifically (sharded per-tranche, distinct from slot 26's
`all`-mode run above). Per SKILL.md's iterative-drain step 1 and the fuller-audit intent of a dedicated single-tranche
dispatch, ran the PROPER Phase 0-3 procedure (`generate_ag_closeout_audit_candidates.py --tranche infra` + a full
Phase-1 Workflow) rather than re-relying on the lighter `check_ag_closeout_linkage.py`-only pre-filter slot 26 used —
that check catches "never mentioned anywhere," not "mentioned but not actually covered," which is a real gap for a
single-tranche run with the budget to do the fuller pass.

**Candidate set**: 58 members, 15 covering docs (11 batch/finalize pairs + the hub +
`infra_capture_and_devops_ leftovers`+finalize — the latter pair found only via the dependency-graph discovery path, not
the filename-pattern one), 17 never-cited. Ran a 17-agent Phase-1 Workflow (0 errors) classifying every one.

**Verdicts**: 2 `archivable_now`, 1 `archivable_after_planned_work`, 9 `orphaned_never_touched`, 5
`exclude_cross_cutting` (mistags/multi-tranche digests).

**Resolved this dispatch (not parked findings)**:

1. **4 stale "awaiting operator review" banners fixed** (batches 11/12/13/14) — all 4 were bulk-approved
   `unified-trading-pm@78e91572f3` ("flip 14 satellite-extraction batches draft->active for AO dispatch," 2026-08-09
   23:48 UTC) but their own body text was never updated to match, so each still read "awaiting review" against an
   already-`active` frontmatter — the same stale-banner bug class previously seen on batch3 (2026-08-01 entry, this
   hub's Progress Log). Corrected all 4 with the approval commit cited.
2. **`host_root_disk_full_transient_2026_07_13.md` archived** — both todos were `[x]` (done 2026-08-09,
   `unified-trading-pm@9dcd37631` + `@2c028dee9d`), `archive_exempt: true` was the sanctioned bridge, and the doc's own
   2026-08-09 Progress Log entry explicitly deferred "the actual archive-and-referrer-sweep... to the next
   `/ag-closeout-audit infra`... pass" — this dispatch. Ran the full 6-step ritual: `git mv` to
   `plans/archive/2026_08/issues/`, ARCHIVED banner + `resolved_by` + dropped `archive_exempt`, fixed the 1
   active-corpus referrer carrying a real leading-slash path (`host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md`, 2
   occurrences — the other 3 referrers found were bare-filename prose mentions in already-archived docs or informal
   citations, out of `check_reference_paths.py`'s scope per its own `plans/archive/`-exclusion design, ruled
   2026-08-02). No codex-alignment update needed (the doc's own fix work already updated
   `/codex/05-infrastructure/per-tab-worktrees.md` § "Shared uv cache" on 2026-08-09).
3. **`s5_7_required_docs_gaps_2026_07_29.md`'s stale "fill the gaps" todo corrected** — resolved a conflict a 2026-08-08
   na-eligibility-audit round had already found and correctly held (`assigned_vm: NA` pending reconciliation): the todo
   assumed market-data-processing-service's `DEPLOYMENT_GUIDE.md`/`TESTING.md` needed net-new content, but
   `codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s dated, specific 2026-07-27 refreshed registry classifies both as
   **DELETE** (redirect-stub targets already verified to exist), matching the already-executed instruments-service
   precedent exactly. Resolved by logic (the codex audit's evidence is more authoritative/recent/direct), not escalated
   — corrected the todo text in place.
4. **Drafted `infra_satellite_ao_dispatch_batch15_2026_08_10.md` + finalize twin** (`status: draft`, 2 todos): (a) the
   `/tmp` tmpfs root-cause fix (`host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md`'s 2 todos, combined — live
   re-verified 2026-08-10, still saturating with a fully different set of large scratch files than the original report,
   confirming an ongoing pattern, not a one-time fluke); (b) the corrected S5.7 redirect-stub reconciliation from
   finding 3. Both conflict-checked clean against the full covering set + corpus-wide greps for the specific targets.
   Validated via `check_frontmatter_schema.py`, `check_todo_format.sh`, `check_line_caps.sh`,
   `check_finalize_plan_coverage.py` — all pass. `check_ag_closeout_linkage.py` re-run: 0 orphans corpus-wide (unchanged
   from slot 26's post-fix baseline).

**Carried-forward, re-verified unchanged (parked, not newly escalated)**:

5. `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` todo 10 — genuinely-optional design/priority call
   (build a branch-protection alert on `unified-trading-ci`?), KEEP-NA confirmed independently 3× already
   (2026-08-07/08/09). Unchanged.
6. `ag_closeout_audit_infra_parked_2026_08_08.md` findings 12/13 (DOCS P3 tooling additions —
   `self_dispatched_orphan_count` metric, `CITE_RE` hardening + a governance-audit scoping call) — 8th consecutive
   reconfirmation, still not urgent/ripe.
7. `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` — 4 open items, correctly non-batchable
   (live-repro-needed, `[OPERATOR]`-sign-off-pending mitigation choice, downstream-of-that-decision doc update, and a
   deliberately-not-yet-automated stash audit per the 2026-08-10 na-eligibility-audit's own stated safety rationale).
8. `deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md` — `[OPERATOR]`-gated (needs a ruling on
   which of 2 duplicate Terraform Cloud Run job module definitions is canonical before the follow-on `tofu state rm`
   step is safe to dispatch).
9. `lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md` todo 2 — design/judgment call, confirmed
   twice already (na-eligibility-audit 2026-08-07/09).
10. `na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md` — design-preference call (a
    shared membership-test module extraction), no stated tiebreaker.
11. `shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md` — **genuine cross-tranche conflict, correctly
    held since 2026-08-08 (na-eligibility-audit round7), reconfirmed unchanged today.** Closely overlaps `ci`'s
    `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` (`asset_group: [ci]`, still `status: open`, 2 open
    todos) — both propose per-invocation/per-slot gcloud-identity fixes against the SAME shared `~/.config/gcloud`
    mutable state, from two different root causes (multi-slot `gcloud config set account` races vs. GH Actions WIF job
    auth overwrites). Per the conflict-check protocol's caution on closely-adjacent claims, this stays `assigned_vm: NA`
    — not re-escalated as a fresh `BLOCKED-OPERATOR-DECISION` since the existing hold is already the correct disposition
    and nothing material changed.
12. **Mistag corroboration — `ci_pipeline_speed_and_cost_redesign_2026_08_05.md` +
    `self_hosted_runner_public_repo_ revert_2026_08_05.md`** (both `[ci, infrastructure]`, real owner `ci`). This is the
    5th/6th independent confirmation across 3 days (infra's own 2026-08-08 run; `ci`'s own 2026-08-07/08/09/10 runs, the
    last being TODAY) that both docs' content is CI-pipeline-internal (self-hosted runner capacity/billing/checkout
    mechanics), not infra's actual Track 1-3 scope. Not retagged this run either — corroborating `ci`'s own stated
    2026-08-10 recommendation for "a dedicated corpus-wide `ci`↔`infrastructure` retag pass" rather than a unilateral
    single-tranche fix, consistent with the multi-day restraint both sides have already shown. **Formalized 2026-08-10
    (prose-findings formalization sweep): now a real `- [ ]` todo in `ag_closeout_audit_ci_parked_2026_08_10.md`'s own
    `## Todos` section (covers all 4 known dual-tagged docs, this pair plus
    `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` +
    `shared_ci_workflow_repo_extraction_2026_08_06.md`) — not duplicated here to avoid two independently-drifting
    checkboxes for the same corpus fix.**
13. `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md` — DeFi-owned (title-prefixed,
    content is a DeFi manifest-purge saga; the `infrastructure` co-tag was earned by now-fully-closed VM-launcher
    reliability fixes surfaced along the way). One small remaining item (fix a stale row in a sibling DeFi doc) — not
    infra's to write, handed forward as an evolved pointer (the item 21/7 chain from 2026-08-08/09 is now resolved down
    to just this one row-update).
14. `defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md` — operator-ruled dual-tag
    `[defi, infrastructure]` (2026-08-09, recommendation B), 2 open items both genuinely DeFi/manifest-consolidator
    domain (a design call + a VM relaunch), correctly not infra's to action.

**Not a mistag (informational only)**: `operator_action_items_consolidated_2026_08_08.md` (deliberate 7-tag
multi-tranche digest, matches the Orthogonality check's own stated exemption) and
`plan_reconciler_findings_infra_2026_08_10.md` (actively being worked by a concurrent LOCKED `plan_reconciler` dispatch,
`agt-716973`, confirmed via commit-timing cross-check against 5 sibling same-family docs — correctly left untouched, not
this run's to race).

**Ledger**: 14 parked/carried findings (5-14 above, counting the 2-doc mistag corroboration as one item) + 4 resolved
items (1-4) + 2 informational (not counted) = **18 entries written to this section this dispatch, 18 substantive
findings generated — balanced.** 0 items newly escalated as `BLOCKED-OPERATOR-DECISION` (finding 11's conflict was
already correctly held; nothing new required fresh escalation).

## Todos

None — every genuine finding this dispatch either resolved directly (4 items) or is already correctly tracked/held in
its own source doc (10 carried-forward items, re-verified unchanged). The one item that WAS genuinely still-prose-only
(item 12, the `ci`↔`infrastructure` mistag corroboration) was formalized 2026-08-10 into a `- [ ]` todo in the sibling
`ag_closeout_audit_ci_parked_2026_08_10.md` doc instead (see the note on item 12 above) — not duplicated here.

## Progress Log

- **2026-08-10 (prose-findings formalization sweep)**: converted 0 prose findings into a NEW todo in this doc (this
  doc's own findings were all either already-resolved-with-evidence or already tracked in their own source docs, per its
  own accurate "## Todos: None" framing); 1 genuinely-open item (item 12's mistag corroboration) was cross-referenced to
  the formal todo added in the sibling `ag_closeout_audit_ci_parked_2026_08_10.md` doc rather than duplicated here.
- **na-eligibility-audit 2026-08-10 (formalized-docs follow-up, group 1 of 2)**: KEEP-NA, valid — not an ARCHIVE
  candidate. Today's most current infra+ci audit ledger, actively tracking 14 carried-forward findings (a live,
  genuine cross-tranche conflict among them) across 3 same-day dispatches (slot 26 all-mode, slot 20 infra-specific
  follow-up). "## Todos: None" is by design (every genuine finding either resolved directly this run or already
  tracked at its own source doc). Not locked. Doc stays `assigned_vm: NA`.
- **2026-08-10 (scheduled `ag_closeout_auditor`, slot 20, `agt-7788a0`, ~4.7h later)**: Second same-day dispatch,
  infra-only (sharded). Ran the full Phase 0-3 procedure (candidate generator + 17-agent Phase-1 Workflow) rather than
  the lighter linkage-only pre-filter slot 26 used. Fixed 4 stale operator-approval banners, archived 1 fully-done doc
  (6-step ritual), corrected 1 stale conflict-resolution-pending todo, and drafted
  `infra_satellite_ao_dispatch_ batch15_2026_08_10.md` + finalize (2 AO-eligible items). 10 other findings reconfirmed
  unchanged/correctly held, including 1 genuine live cross-tranche conflict
  (`shared_host_gcloud_active_account_cross_slot_clobber` vs `ci`'s WIF-poisoning doc) and a now-5×/6×-confirmed
  `ci`↔`infrastructure` dual-tag mistag pair. See "Second dispatch delta" section above for full detail.
- **2026-08-10** — `/ag-closeout-audit all` run (autonomous mode, task-less one-off, slot 26). Phase 0: corpus-wide
  `check_ag_closeout_linkage.py` sweep found 9 infra + 3 ci orphans, all linkage-only (verified via direct read: every
  flagged doc either already had real coverage as a self-dispatched `assigned_vm: planning` plan, or was gating
  scaffolding for one). Fixed all 12 by appending the tranche's closeout-family path to each doc's `related:` list.
  Re-ran the check: infra and ci both 0. No Phase-1 Workflow dispatch needed for either tranche (nothing survived the
  linkage-only pre-filter). Ledger: 0 operator-decision-requiring findings + 12 mechanical fixes (not counted as parked
  findings) — **balanced**.
