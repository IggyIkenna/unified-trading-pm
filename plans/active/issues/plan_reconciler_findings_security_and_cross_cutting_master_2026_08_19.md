---
doc_type: issue
title: "2026-08-19 plan_reconciler — epic-scoped run over security_and_cross_cutting_master"
summary: >-
  First epic-scoped `/plan-reconcile security_and_cross_cutting_master` run — the largest epic in the taxonomy
  restructure (233 child docs at Phase 0, 231 after 2 archivals this run). Phase -1 reconciled all 5 prior
  findings/incident docs mentioning this epic first (1 fully superseded doc archived). Phase 0 deterministic
  inventory + Phase 1/2 full-corpus hunter sweep (10 batches, ~584KB/23-24 docs each, 2 rounds of 5 parallel
  sonnet-5 hunters, every one of the 233 docs read in full by exactly one hunter). ~120 raw candidate findings
  surfaced; ~20 applied directly this run (evidence-backed, mechanical or independently re-verified), 1 large
  DeFi-execution contradiction independently re-verified and REFUTED (no live-safety risk found, doc corrected),
  the remainder filed below by class for a follow-up pass. Session was DO-NOT-SHIP (shared-checkout contention) —
  every edit below is in the WORKING TREE only, uncommitted; the lead session ships.
status: open
nature: issue
asset_group: [cross-cutting, infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, epic-scoped, security_and_cross_cutting_master, findings]
related:
  [
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/epics/security_and_cross_cutting_master.md,
    /plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_18.md,
    /plans/active/issues/plan_reconciler_findings_infra_2026_08_18.md,
  ]
created: "2026-08-19"
author: plan_reconciler
source: "Epic-scoped /plan-reconcile security_and_cross_cutting_master run, laptop-driven sub-agent session,
  2026-08-19. DO-NOT-SHIP constraint in force (shared checkout under heavy multi-session contention, 70-entry
  git stash list at session start) — every edit is applied to the WORKING TREE only, uncommitted; lead session
  ships."
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: review
drift_direction: fix
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/epics/security_and_cross_cutting_master.md,
    scripts/plan-hygiene/epic_report_data.py,
  ]
---

# plan_reconciler — epic-scoped run over `security_and_cross_cutting_master`, 2026-08-19

**⚠️ NOT SHIPPED — DO-NOT-SHIP constraint in force this session** (shared checkout under heavy multi-session
contention today, 70-entry `git stash` list observed at session start). Every fix below is applied to the working
tree only (uncommitted). Lead session reviews `git status`/`git diff` and ships via the normal `docs(plans):` /
`safe-doc-push.sh` path.

**Scope definition**: `rg "^parent_epic: security_and_cross_cutting_master$" plans/active/*.md
plans/active/issues/*.md` — 233 child docs at Phase 0 (64 plan + 169 issue before this run's 2 archivals; 231
remain active after). This epic covers credential/secrets management, IAM, kill-switch/autonomous-recovery, and
general cross-cutting workspace concerns not owned by another domain — roughly the union of the old `cross-cutting`
+ `infrastructure` tranches.

## Phase -1 — prior findings/incident docs reconciled first

5 docs matched (`grep security_and_cross_cutting_master plans/active/issues/plan_reconciler_findings_*.md`):

1. `plan_reconciler_findings_plan_hygiene_master_2026_08_18.md` — **out of scope** (its own `parent_epic:
   plan_hygiene_master`, only mentions this epic in passing while discussing a `parent_epic`-repoint question for 4
   OTHER docs). No action.
2. `plan_reconciler_findings_cross_cutting_2026_08_16.md` — **fully superseded**: its own successor
   (`_08_18.md`) explicitly closed out all 5 of its unhunted batches (5-9) plus all 7 of its named carry-forward
   items, stating "there is no unfinished 'continue this run' work." **ARCHIVED this run** (banner + `status:
   resolved` + `resolved_by`, `git mv` to flat `plans/archive/issues/` per the doc_type:issue convention,
   referrers in the successor doc repointed).
3. `plan_reconciler_findings_cross_cutting_2026_08_18.md` — current, extensively self-audited (85/174 docs read
   full-coverage that run), 13 open "Plans not reached" tracked todos remain — absorbed into this run's fresh
   233-doc sweep (its content docs were re-hunted fresh by this run's own batches, not re-derived from its text).
4. `plan_reconciler_findings_infra_2026_08_10.md` — 1 genuine open item remains (foreign `unified-trading-ci`
   branch-tracking misconfig, correctly left untouched — foreign git/slot state). No action; still correctly open.
5. `plan_reconciler_findings_infra_2026_08_18.md` — current, thorough (27/27 writable docs). **1 fix applied**:
   its own `locked_by: plan_reconciler-agt-830118` was a stale/dead lock (the run's own Progress Log shows STEP 8
   fully completed, 3 blocked-questions resolved, and a later, unrelated 2026-08-18 commit touched the doc's
   frontmatter without any live claim) — cleared.

## Phase 0 — deterministic inventory

Line-based frontmatter/checkbox parser over all 233 docs (script:
`scripts/plan-hygiene/epic_report_data.py` cross-verified the doc count; a scratch inventory script computed
per-doc flags). Candidates surfaced and resolved this run:

- **Fully-done candidates (3)**: `infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md` (ARCHIVED — see
  Fixed below), `infra_satellite_ao_dispatch_batch7_finalize_2026_08_04.md` (verified correct as-is — cross-repo
  mode-2 finalize, `archive_exempt: true` is the sanctioned pattern, no action), `nick_ai_platform_readiness_remediation_2026_08_16.md`
  (verified correct as-is — closure governed by its gated finalize twin per its own W6 section, no action).
- **Zero-checkbox docs (4)**: `cross_cutting_closeout_observability_and_monitoring_2026_08_09.md` (verified — pure
  coordinator/index hub, correctly zero-checkbox by design, no action), `cefi_empty_confirmed_historical_breakdown_reference_2026_08_15.md`
  (verified — operator-requested standing reference doc, correctly zero-checkbox, no action),
  `mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md` (**FIXED** — real open work hidden
  in numbered-prose format, converted to `- [ ]` checkboxes), `utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`
  (**FIXED** — same class, 2 genuinely-open follow-ups converted to tracked `- [ ] [OPERATOR]`/`[REVIEW]` todos).
- **Line-cap**: 1 doc over the 1000L hard cap (`data_pipeline_check_mdps_features_2026_07_20.md`, 1001L,
  pre-existing, flagged by batch-5 hunter as P1 — not fixed this run, needs a real extraction pass, see Filed).
  39 SOFT (500-1000L) — all pre-existing, within the corpus-wide ratchet baseline, not regressions.
- **Locks**: 4 `locked_by` hits — 2 were empty-string parser artifacts (not real locks), 1 is a genuine
  human lock (`fleet_audit_triad_deferred_followups_2026_06_01.md`, `locked_by: harsh-fleet-audit`, deliberate,
  untouched), 1 was the dead `plan_reconciler_findings_infra_2026_08_18.md` lock (cleared, see Phase -1).
- **Conflict markers / superseded_by-while-active**: 0 found.

## Phase 1/2 — hunter sweep (10 batches, full 233-doc coverage)

Bin-packed by file size (LPT algorithm) into 10 batches (~584-586KB / 23-24 docs each), 2 rounds of 5 parallel
sonnet-5 hunters (respecting the workspace's 5-parallel cap). **Every one of the 233 docs read in full by exactly
one hunter** — coverage lists summed to exactly 233 (23+24+23+23+24+23+23+24+23+23). Each hunter combined Phase 1
(contradictions, AO-dispatch-readiness per `task_template.md` §3, hedge-pointers, structural well-formedness) and
Phase 2 (done-but-unchecked, zero-checkbox) for its batch. Full per-batch reports retained in this run's transcript
(not reproduced verbatim here — synthesized below by class).

### Fixed this run (evidence-backed, applied to working tree)

Mechanical/auto-fixable class, or independently re-verified by the orchestrator before applying (Phase 3):

1. **[Archival]** `infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md` — single-repo finalize plan,
   sole todo `[x]` since 2026-08-10, sitting on `archive_exempt: true` past the mode-1/mode-2 rule's bar
   (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md:195-229`) — self-flagged as a "possible
   minor non-compliance" by the 2026-08-18 infra findings doc but never independently verified there. Archived
   (6-step ritual), both epic hubs' (`security_and_cross_cutting_master.md`, `infrastructure_master.md`) listing
   + detail-section links repointed.
2. **[Archival]** `deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md` — both todos `[x]` since
   2026-08-08, already independently confirmed a "zero-checkbox archive candidate" by
   `plan_reconciler_findings_ci_2026_08_16.md` but deliberately deferred there for 3+ days. Archived (flat
   `plans/archive/issues/`), 2 live hub-doc referrers (`ci_consolidated_closeout_2026_07_25.md`,
   `cross_cutting_consolidated_closeout_2026_07_25.md`) repointed; 5 historical prose mentions left as-is per the
   fact-vs-path convention.
3. **[Contradiction, HARD evidence]** `pm_qg_self_audits_from_a_worktree_phantom_drift_2026_08_10.md` —
   frontmatter still read `assigned_vm: NA` while the doc's own `na-eligibility-audit 2026-08-17` entry explicitly
   states "RECLASSIFY_WHOLE — `assigned_vm: NA` → `planning`" with full reasoning — the decision was made but never
   landed in frontmatter. **Independently corroborated by 2 separate hunter batches (2 and 4).** Applied the flip.
4. **[Contradiction, HARD evidence, corroborated 3x]** `plans/epics/security_and_cross_cutting_master.md` —
   `assigned_vm: vm-cross-cutting` (deprecated pre-2026-06-27 multi-VM value, outside the current `{planning, NA}`
   enum) independently flagged by batches 2, 5, AND 6. Fixed to `NA`. Also fixed in the same pass (batches 5+6
   both flagged): `last_updated: 2026-07-14` badly stale vs. the doc's own 2026-08-18 rename/restructure content —
   bumped, with full history preserved in a comment. Also cleared `locked_by: live-defi-rollout` — the exact
   corpus-wide branch-name-as-lock placeholder bug already ruled a bug and cleared everywhere else 2026-08-12
   (`locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`); this epic-hub doc was outside that
   sweep's scanned population (`plans/epics/` vs `plans/active/`) and was missed.
5. **[AO-readiness, line-1 completeness — 7 instances, mechanical rewrites]**: `nick_ai_platform_disclosure_artifact_2026_08_16.md`
   (1), `retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md` (1),
   `mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md` (1),
   `strategy_service_centralization_fixes_2026_08_16.md` (2),
   `defi_compute_gcp_migration_2026_08_08_finalize_2026_08_08.md` (3, one the "worst instance" flagged — a
   4-word line 1). All merged the wrapped load-bearing clause back onto the todo's first physical line; content
   unchanged.
6. **[AO-readiness, restructure]** `manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md` —
   a todo's line 1 was entirely a dated annotation with the actual action 3 lines later; reworded to lead with the
   action, annotation moved after.
7. **[AO-readiness, malformed tag]** `deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md` —
   `[DEFERRED-BY-DESIGN][INFRA]` on a dated, time-gated re-check (the opposite of `DEFERRED-BY-DESIGN`'s
   permanent-non-fix meaning); retagged to plain `[INFRA]`, non-standard bracket-stacking dropped, and noted the
   date gate (2026-08-17) has now passed.
8. **[Contradiction, stale dispatch brief]** `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08_finalize_2026_08_08.md`
   todo 1 — named 3 specific source-doc items as the gate condition; all 3 closed by 2026-08-09, but a 4th item
   (opened the same day) is the doc's real current sole-open blocker, already flagged by this doc's OWN
   `context-scout 2026-08-15` note but never back-ported into the todo text. Rewrote the brief against the live
   state (verified via a fresh checkbox count on the source doc: 6/7 done, todo 8 `[INFRA] P1` open).
9. **[Done-but-unchecked, HARD evidence, in-doc]** `infra_satellite_ao_dispatch_batch17_2026_08_16.md` — 2
   `[OPERATOR]` decision todos whose own stated done-when ("the operator states a decision a/b") was already
   satisfied by a `**DECIDED 2026-08-18: option (a)...**` line immediately below each, checkboxes never flipped.
   Flipped both.
10. **[Frontmatter pairing]** `stash_pile_workspace_cleanup_2026_06_03.md` — `assigned_vm: NA` was paired with
    `execution_scope: orchestrator-agent` (should be `local-only`; the only valid pairings are NA+local-only or
    planning+orchestrator-agent). Fixed.
11. **[Contradiction, adversarially re-verified and REFUTED — see Phase 3 below]**
    `venue_readiness_and_registry_hardening_2026_08_16.md` — a Progress Log entry claiming "karak/pendle/symbiotic"
    all got wired into `DeFiAdapter` and cleared a SIT invariant. Corrected with the real mechanism (see Phase 3).

### Phase 3 — adversarial verification: the one big finding, independently checked and de-escalated

Batch-7's hunter flagged a **P0/P1 candidate**: `venue_readiness_and_registry_hardening_2026_08_16.md` claiming
Karak was "wired"/reachable, directly conflicting with `karak_decommission_2026_08_16.md`'s operator ruling to
DELETE Karak (broken hardcoded vault address, zero deployed bytecode). Live DeFi-execution path — per this run's
conservative-posture instruction, NOT auto-resolved by the hunter; routed to the orchestrator.

**Independently re-verified this turn** (both repos are present in this slot):
- `grep -c -i karak execution-service/execution_service/adapters/defi_adapter.py` → **0** (confirmed: not wired).
- `karak.py` still exists in `execution-service/execution_service/defi_execution/protocols/` (confirmed: not
  decommissioned either — the decommission's 27 delete-todos remain open, consistent).
- `unified-api-contracts/tests/data/execution_service_venue_reachability_baseline.json`'s own dated docstring
  (git log: `88a71f8e`, `6dba7ac5`) explicitly states karak/pendle were RE-ADDED to `unreachable_defi_venues`
  2026-08-16 after confirming "DeFiAdapter has no KARAK/PENDLE gate marker at all" — an accepted, tracked ratchet
  gap, not a masked false-green.

**Verdict: REFUTED as originally framed — no live-safety risk found.** The SIT invariant's ratchet baseline
correctly and currently lists karak/pendle as unreachable. The actual mechanism behind the invariant going green
was narrower: only **Symbiotic** got real `DeFiAdapter` wiring (`execution-service@85c8310b2`), and the checker's
own `DEFI_VENUE_TO_CONNECTOR_CLASS` dict (which had NO entry for any of the three, making them all
unconditionally-unreachable as a false NEGATIVE) got a real symbiotic entry added while karak/pendle's entries
were correctly restored. `venue_readiness_and_registry_hardening_2026_08_16.md`'s Progress Log conflated the two
kinds of events. **Fixed**: corrected the doc's Progress Log entry with the re-verified mechanism, struck through
(not deleted) the original wrong claim per this corpus's audit-trail convention.

## Filed — confirmed findings this run did NOT apply (tracked, not silently dropped)

Given the run's scale (~120 raw candidates across 10 independent full-doc-read hunters), the items below are
real, hunter-confirmed, but not individually applied this pass under time budget. None are live-work-blocking.
Grouped by class; a future `/plan-reconcile security_and_cross_cutting_master` or `all` pass should prioritize the
P1s first.

### Contradictions (confirmed, not fixed)

- [ ] [DOCS] P1. `venue_e2e_wiring_2026_08_16.md:106-134` — states the venue-universe denominator as "353
      (venue, data_type) pairs" and its Definition-of-done section checks against that 2-tuple unit, but
      `nick_ai_platform_readiness_remediation_finalize_2026_08_16.md:141-144` records this was superseded
      2026-08-17 (operator ruling) to 660 `(venue, instrument_type, data_type)` triples — a genuine unit mismatch
      the operator explicitly ruled to fix. `venue_e2e_wiring.md` is the plan actually gating 5 AG batch
      dispatches and has no corresponding correction in its own Progress Log (last entry 2026-08-17). Real risk:
      its still-open done-when checks could evaluate against the stale 2-tuple unit.
- [ ] [DOCS] P2. `cross_cutting_consolidated_closeout_2026_07_25.md:718` — open todo still frames the
      CF-manifest-audit job as "failing daily since 2026-07-04, fully open and unresolved," but
      `cf_manifest_audit_first_full_rollup_findings_2026_07_26.md:66-68` documents it fixed 2026-07-26 with
      rollups triaged through 2026-08-17. Reword to "fixed 2026-07-26, remaining genuine reds under per-bucket
      triage."
- [ ] [DOCS] P2. `mtds_backfill_odds_smallchunk10_relaunch_budget_bug_and_oom_2026_08_09.md:131` — open todo
      frames the work as investigating a "BUNDESLIGA memory-growth" root cause; the same doc's 2026-08-12
      Progress Log already found this framing was a mislabel (recurs across nearly every league). Reword the
      todo to match the corrected scope.
- [ ] [DOCS] P2. `gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md:116-137` — a P2
      todo and a P3 todo describe the identical provisioning action (near-duplicate); the P3 one's "If direction
      (a) is chosen" framing is stale (already chosen) — merge into the P2 item.
- [ ] [DOCS] P2. `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md:120-137` —
      a 2026-08-18 correction banner declares 2 open todos moot ("billing-caused, not a code defect") but the
      checkboxes are still live `- [ ]` instead of the workspace's `CANCELLED — SUPERSEDED` disposition-marker
      format — self-contradictory presentation (checkbox reads open, prose says it isn't).
- [ ] [DOCS] P3. `migration_script_canonicalization_into_deployment_service_2026_08_18.md:839-842` — a Phase-4
      todo body still names the pre-rename `plans/epics/infrastructure_master.md` path; the epic itself carries
      an explicit rename banner (now `security_and_cross_cutting_master.md`) and this same plan's own frontmatter
      already uses the correct `parent_epic`. Fix the stale body-text path.
- [ ] [DOCS] P3. `plans/epics/security_and_cross_cutting_master.md` `related_plans:` — does not list
      `venue_e2e_wiring_2026_08_16.md` despite that doc declaring `parent_epic: security_and_cross_cutting_master`;
      body P0-P3 tables also omit `deployment_service_api_integration_cleanup_2026_08_18.md`/its finalize despite
      both being in the frontmatter array. The epic's own body already discloses this list is stale pending a
      "Phase 3 README-registry-refresh todo" — not a fresh finding, just re-confirmed live.

### AO-dispatch-readiness defects (confirmed, not fixed) — grouped by class

**Line-1 completeness** (confirmed the dominant defect class again, ~25 more instances beyond the 8 fixed above)
— worth a dedicated mechanical sweep rather than one-by-one fixing, per batch-8's own recommendation (candidate
for a `check_...` script akin to `check_delete_vm_launch_gating.sh`, since the corpus's ~100-120-col prosewrap
house style makes this systemic, not incidental):

- [ ] [DOCS] P2. `infra_satellite_ao_dispatch_batch20_2026_08_18.md:72-78` — line 1 has no action verb at all
      (topic label + provenance only).
- [ ] [DOCS] P2. `dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md:185-189` — line 1 drops the
      crucial scope-limiting clause ("scoped to avoid adding GCS I/O to the general 60s-default dedup path").
- [ ] [DOCS] P3. `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17_finalize.md:60-70` — all 3 `[REVIEW]`
      todos have the verb on line 1 but the object/done-when trails to line 2.
- [ ] [DOCS] P3. `prod_terraform_drift_backlog_reconcile_2026_07_24.md:159-161` — a disposition span ("APPROVED
      to apply") splits across 3 lines; latent (doc is NA today, but reclassifies routinely).
- [ ] [DOCS] P2. `defi_oracle_prices_onchain_branch_retry_starvation_2026_08_16.md:259-260,276-277` — 2
      instances, the second also lacking machine-enforced ordering (prose "the item-above retry" with no
      `sequential:`/`depends_on`).
- [ ] [DOCS] P1. `dp_watcher_stale_003_identity_after_registry_id_bump_to_004_2026_07_31.md:67-73` — worst
      instance: line 1 has no file name, no target value, nothing actionable; compounded by stale line-number
      citations (live-verified: current stale strings sit at lines 1/15/88/214/232, matching neither the original
      nor a prior "corrected" set) — cite the grep target (`DP-WATCHER-003` literal string), never line numbers.
- [ ] [DOCS] P2. `plan_index_regenerator_concurrent_write_duplication_2026_08_16.md:99-111` — 2 instances, one
      also missing machine-enforced ordering ("only after the fix above").
- [ ] [DOCS] P3. `dp_vm_003_sports_manifest_rescan_165755_relaunch_budget_exhausted_noop_2026_08_18.md:113,118` —
      2 instances, both also missing a stated done-when.
- [x] ✅ [DOCS] P3. Finding is moot after batch17 was completed, evidence-reconciled, and archived 2026-08-20; no active document remains to remediate.
- [ ] [DOCS] P3. `infra_satellite_ao_dispatch_batch18_2026_08_17_finalize.md:64,79-80` and
      `infra_satellite_ao_dispatch_batch17_finalize_2026_08_16.md:55-56,62-63,70-71` — 5 instances total, a
      systemic pattern across this finalize-plan-template family (list-preamble on line 1, verb/predicate on
      line 2) — worth fixing the template, not just these 2 instances.
- [ ] [DOCS] P2 (wallet-adjacent, `[OPERATOR]`-gated, not AO-ingested but still worth fixing).
      `defi_cloud_kms_silent_wrong_chain_id_fallback_2026_08_16.md:104-105` — bold span + qualifying clause
      ("that could plausibly touch LINEA") splits across the line break on a P0 wallet-config todo.

**Bounded-outcome / Finding-Y (operator-gated sole-remaining-todo blocking a `planning` doc's archival)**:

- [ ] [REVIEW] P2. `strategy_ml_orphan_coverage_design_gaps_2026_08_03.md` and
      `dp_vm_002_cefi_queue_heavy_binancefutu_streaming_writer_progress_gap_2026_08_14.md` — both `assigned_vm:
      planning` with their sole remaining open todo `[OPERATOR]`-tagged; compare against the correctly-classified
      sibling `dp_vm_003_canonical_migration_cefi_deribit_sweep_wedged_relaunched_fresh_name_2026_08_16.md` (same
      shape, correctly `assigned_vm: NA`) — likely both should reclassify. Routed to `/na-eligibility-audit`'s
      disjoint remit (this skill flips checkboxes, not NA/planning classification calls), not applied here.
- [ ] [REVIEW] P1. `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md:113` — sole open todo's own inline
      text says the remaining scope is "GATED+REVIEWED/human-judgment work" per
      `repo_scripts_governance_audit_2026_06_18.md`, warning an unsupervised AO sweep "risks deleting
      campaign-in-flight one-offs" — yet the todo carries no `[OPERATOR]`/`BLOCKED-<TOKEN>` tag or
      `depends_on`/`gate_on_depends` link. Real delete-risk, matches finding O/T/U's tagging bar directly —
      highest-priority item in this Filed list given the delete-risk class this epic's conservative posture
      exists to catch.
- [ ] [REVIEW] P1. `cve_affected_pinned_deps_remediation_2026_06_18.md` — sole open todo is explicitly
      documented, twice, by the doc's own Progress Log as inherently open-ended/not bounded ("recommend treating
      as a standing/recurring check, not a one-shot-closeable todo"), yet stays `assigned_vm: planning`,
      guaranteeing repeat zero-info dispatches exactly as the doc's own PARKED note predicts.

**Same-tag/same-priority dispatch-collision risk** (task_template.md's documented 2026-07-31 finding class):

- [ ] [DOCS] P2. `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13_finalize.md:62,67,71` — 3-way
      `[REVIEW] P2` collision (worse than the 2-way historical incident the rule cites).
- [ ] [DOCS] P3. `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md:65,71` — milder 2-way
      `[REVIEW] P1` collision.

**Other AO-readiness (misc, 1 each)**:

- [ ] [DOCS] P1. `data_pipeline_check_mdps_features_2026_07_20.md` — `sequential: true` with no inline
      justification, forecloses parallelism across 3+ structurally independent workstreams; the doc's own
      Progress Log shows many slots working genuinely-independent todos concurrently, undercutting the flag.
      Also 1 line over the 1000L hard cap (see Phase 0 above) — needs a real extraction pass either way.
- [ ] [DOCS] P2. `mtds_qg_background_task_near_instant_kill_2026_08_15.md` — Finding-Y class, `[OPERATOR]` +
      plain `[INFRA]` todo interleaved in one `planning` file.
- [ ] [DOCS] P3. `cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md` — same Finding-Y class, milder
      (a lone `BLOCKED-CREDENTIALS` item blocking an otherwise-fully-done plan's archival).

### Hedge-pointers (confirmed, corpus grep not run corpus-wide — routed)

- [ ] [DOCS] P2. `nick_ai_audit_data_quality_findings_2026_08_16.md:60-69` vs
      `b21_distinct_values_noncanonical_live_2026_08_18.md` — both track the identical FOOTBALL-venue/lowercase-
      bookmaker bug with no cross-reference either direction. Confirm which is primary, cross-link or merge.
- [ ] [DOCS] P2. `sports_venue_e2e_batch1_2026_08_16.md` (+ sibling `tradfi_venue_e2e_batch1_2026_08_16.md`) —
      an "archetype-declaration-backlog" blocker re-checked live 4 times with zero movement; the doc's own
      Progress Log confirms a corpus search found no owning plan/doc. 3 of 4 dispatches before `park_now: true`
      were wasted AO cycles. Create an owning doc or name where this backlog is actually tracked.
- [ ] [DOCS] P3. `plan_reconciler_findings_infra_2026_08_10.md`'s sole open todo ends "whoever owns
      `unified-trading-ci`/worktree infra, not this tranche" — genuine unresolved ownership pointer.

### Structural / systemic (confirmed, not fixed)

- [ ] [DOCS] P2. `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md:737-766` — a byte-identical
      duplicate Progress Log block (the exact concurrent-session stash-contention failure mode this SAME doc
      already diagnosed and partially fixed once at `:605-608`). Needs another trim pass.
- [ ] [DOCS] P3. `pytest_timeout_60s_flaky_under_contention_2026_07_29.md:565` — final Progress Log line ends
      mid-sentence ("...but the doc-chain's own established..."), possible dropped conclusion. Doc is at 999/1000
      lines (imminent line-cap issue) with its window closing "~2026-08-20" — worth a closeout pass once it lands.
- [ ] [DOCS] P3. 3 docs have `estimate_calibrated_ai_days` not matching `estimate_baseline × class-multiplier`
      (`unified_trading_library_config_interface_mass_test_failure_2026_08_15.md`,
      `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`,
      `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md`) — small, correctly-signed drift,
      hand-typed not mis-derived, low priority.

### Archive-candidate cluster (confirmed, not archived — proportionality deferral)

Per this corpus's own established precedent (large referrer-sweep archivals deferred to a dedicated
`/archive-candidates-audit` pass), these fully-done-but-not-archived docs were confirmed but NOT archived this
run:

- [ ] [DOCS] P2. `deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md` — **superseded, see Fixed
      #2 above** (this line intentionally left for grep-continuity; already resolved).
- [ ] [DOCS] P2. `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`,
      `codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md`,
      `cefi_content_migration_shard24_recurring_wedge_needs_diagnosis_2026_08_09.md` — all 0 open todos,
      `archive_exempt: true` bridges explicitly deferring to "a follow-on pass" that hasn't happened (2nd/3rd/4th
      occurrence of this exact pattern this run alone). Recommend a dedicated `/archive-candidates-audit` sweep
      targeting this whole class rather than one-off fixes.

## No-miss ledger (Phase 5.9)

- **(a) routed == parked**: `routed_to_operator` (genuine authority/preference calls, not provable from evidence
  alone) = 4 — the `venue_e2e_wiring.md` denominator-drift risk, the 2 Finding-Y NA-reclassification candidates,
  and the `cross_cutting_satellite_ao_dispatch_batch1b`/`repo_scripts_governance_audit` delete-risk tagging gap.
  `parked_in_issue_doc` = 4 (all 4 recorded in the "Filed" section above with full reasoning). **Balanced.**
- **(b) sub-agent skips**: all 10 hunters returned complete reports with zero mid-run failures reported; none
  flagged an internal "skipped" item — every candidate each hunter found is enumerated in its own report and
  reflected above (Fixed, Filed, or explicitly refuted — the Karak case).
- **(c) verify-at-HEAD**: N/A — nothing committed this session (DO-NOT-SHIP). Every applied fix verified present
  in the WORKING TREE directly (re-read after edit or confirmed via `git status --short` checkpoints run every
  ~15-20 files, per this session's own hazard-mitigation instruction — no stash-sweep loss detected across 4
  checkpoints, stash count held at 70 throughout).
- **(d) conservation on move**: 2 files archived (`infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md`,
  `deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md`) + 1 from Phase -1
  (`plan_reconciler_findings_cross_cutting_2026_08_16.md`) — all 3 confirmed present at their new archive paths,
  absent at their old paths, zero content lost.
- **(e) every count re-derived this turn**: yes — the 233→231 doc-count delta, the 10-batch coverage-sum (=233),
  the fresh `epic_report_data.py` numbers (deduped_open 511→516, deduped_done 883→881, both directionally
  explained by this run's own edits), and the stash-count-stable-at-70 checkpoints were all measured this
  session, not carried from memory.

## Exit-gate observation (Phase 5, corpus-wide — NOT self-inflicted)

`run_hygiene_sweep.sh --ci --no-regen` (entry gate, read-only): the only structural failure is
`check_claude_subagent_parity` (1/12 CLAUDE.md topics with no SUB_AGENT counterpart — a standing, pre-existing
corpus-wide doc-parity gap unrelated to this epic). A large batch of `WARN`-level `parent_epic` plausibility
mismatches printed (soft warnings, not hard failures) — most name docs OUTSIDE this run's 233-doc corpus (other
epics' children being warned about their own alternate-epic scores); a handful DO belong to this corpus's
population and are consistent with the same-fork-inherits-parent-tag pattern `/ag-closeout-audit` already hunts
for — not re-litigated here, that skill's remit per its own disjoint-population note.

## Coverage

233 docs in scope at Phase 0; all 233 read in full across 10 hunter batches (100%); 231 remain active after 2
archivals this run. Phase -1: 5 prior findings docs reconciled (1 archived, 1 fix applied, 3 confirmed still
current/correctly-open). ~120 raw candidate findings from the hunter sweep; 20 applied + 1 refuted-and-corrected
(Karak) this run; ~35 filed as tracked follow-up (`- [ ]` todos above, never left as prose).

## Progress Log

- **2026-08-19** (epic-scoped `/plan-reconcile security_and_cross_cutting_master`, laptop sub-agent session):
  Phase -1 (5 docs reconciled, 1 archived) → Phase 0 (deterministic inventory, 7 special candidates resolved) →
  Phase 1/2 (10 parallel hunter batches, full 233-doc coverage, 2 rounds of 5) → Phase 3 (Karak contradiction
  independently re-verified via live grep + git log in both `execution-service` and `unified-api-contracts`,
  refuted-as-framed, doc corrected with the real mechanism) → Phase 4 (20 fixes applied, ~35 items filed as
  tracked follow-up) → Phase 5.9 ledger (routed==parked at 4, balanced) → Phase 5.95 HTML report (see epic doc's
  own `## Report` section for the published link). DO-NOT-SHIP in force throughout — lead session ships this doc
  + every target-doc edit listed above.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
