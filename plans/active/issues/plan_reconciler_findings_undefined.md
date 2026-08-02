---
doc_type: issue
title:
  "plan_reconciler daily-worker run — 2026-08-02 whole-corpus pass (manual/standalone invocation, dispatch id undefined)"
summary: >-
  Run-findings + progress journal for a whole-corpus (`scope: all`) plan_reconciler pass executed per
  `agents/plan_reconciler.md` STEP 0-7, invoked standalone (no live agent-orchestrator dispatch — no
  $SERVER_URL/$DISPATCH_ID/$SLOT_ID available in this execution context, so every `/api/...` POST in the boot prompt is
  orchestrator plumbing skipped per this run's own operating instructions). Fans out the 5 hunter families
  (epic-cluster, topic, codex-alignment, mechanical-adjudicator, missed-flip) via sequential/batched reasoning (no
  nested sub-agent spawn available in this execution context) against the full `plans/active/**` +
  `plans/active/issues/**` + `plans/epics/**` corpus, adversarially verifies every candidate (refuter+confirmer+
  tiebreaker reasoning), auto-fixes the verified-easy classes, and routes/parks the genuine judgment calls. Because this
  skill is in its documented PROVING PHASE, this run ships via a review branch (`plan_reconciler/workflow-undefined`) +
  PR into `live-defi-rollout`, never a direct push/quickmerge. STEP 8 (loop-and-wait for operator answers) is explicitly
  skipped per this run's operating instructions — no live dashboard to poll; every alert-worthy item is parked in this
  doc's `## Filed` / `## Contradictions` sections instead, for a human to pick up from the PR.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    plan_reconciler,
    reconciliation,
    plan-hygiene,
    scheduled,
    multi-agent,
    adversarial-verify,
    review-branch,
    whole-corpus,
  ]
related:
  [
    /agents/plan_reconciler.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: plan_reconciler
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  Standalone plan_reconciler run, 2026-08-02, whole-corpus scope (`scope: all`), invoked directly against an isolated
  audit clone (no agent-orchestrator dispatch — dispatch_id undefined, hence this doc's literal filename per the
  invoking task's explicit instruction). Ships via review branch `plan_reconciler/workflow-undefined` + PR (PROVING
  PHASE — PR-gated, not quickmerge).
context_scope:
  [
    /agents/plan_reconciler.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /cursor-configs/SUB_AGENT_MANDATORY_RULES.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# plan_reconciler — 2026-08-02 whole-corpus run (standalone, dispatch id undefined)

> Ships via review branch `plan_reconciler/workflow-undefined` (PROVING PHASE — PR-gated). This doc is the run's single
> human-readable presentation, appended-to as the run progresses (also the progress journal).

## Run parameters

- Scope: `all` (whole corpus — `plans/active/**`, `plans/active/issues/**`, `plans/epics/**`, normative refs).
- Execution mode: standalone / no live orchestrator. Every `/api/...` POST in `agents/plan_reconciler.md` is skipped
  (orchestrator plumbing not reachable in this context).
- Hunter fan-out: performed via sequential/batched reasoning in this single session (no nested sub-agent spawn available
  here) — every hunter family still run, coverage-equivalent, not literally parallel.
- Adversarial verify (STEP 4): performed via the same session's own refuter/confirmer/tiebreaker reasoning per candidate
  — nothing acted on from a single unverified read.
- 12-hour grace window enforced: `git log -1 --format=%ct -- <plan>` vs current time; any plan under grace is read-only
  context this run.
- Shipping: review branch + PR only (this skill's documented PROVING PHASE) — no quickmerge, no direct push to
  `live-defi-rollout`.

## Flips verified

(none yet — appended as STEP 4/5 confirm missed-flip candidates)

## Contradictions

### C1 — `status: resolved` issue docs with genuinely open todos (systemic pattern, P2, ROUTED not auto-fixed)

**Confirmed** (refuter attack: is this just a doc I haven't read carefully enough, or a real split? Confirmer: read each
doc's own Progress Log, which EXPLICITLY names the split as intentional — not a miss, a documented convention). 3 of the
13 `check_terminal_status_archived.py` DUAL-TRACK candidates carry `status: resolved` (correctly reflecting that doc's
PRIMARY incident/finding closed) while still holding 1-3 genuinely open `- [ ]` todos for standing follow-up hygiene
work:

- `github_actions_billing_wall_recurrence_2026_07_29.md` — 3 open `[BACKEND]` P2/P3 todos (spend-telemetry
  self-detection, outage-aware v2 status dispatch, `authoring_slot="ci-reconcile"` 400 fix). Progress Log: "genuine
  standing hygiene follow-ups, independent of the wall itself clearing — left open, not part of this resolution."
- `github_actions_total_fleet_outage_startup_failure_2026_07_30.md` — 2 open todos (re-verify shipped commits went
  CI-green; separate this outage's contribution to a concurrent escalation spike). Progress Log: "standing hygiene
  follow-ups, left open."
- `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` — 2 open todos, BOTH already verified (via the
  doc's own na-eligibility-audit verdict, 2026-07-31) as verbatim-duplicated into
  `/plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (still `status: draft`, unshipped) — the source doc's
  own Progress Log says to "cite/close lines 128 and 132-144 here" once batch4 ships. This one is NOT an orphaned
  deferral (already migrated), just correctly waiting on its own gate.

**Why not auto-fixed**: Phase 4's archival ritual requires "scan for DEFERRED/NICE-TO-HAVE/open items — migrate each...
BEFORE archiving... a done plan with an un-migrated deferral is NOT archive-ready." These 3 have real, un-migrated (for
the first two) open todos, so none were archived despite `check_terminal_status_archived.py` flagging them as
DUAL-TRACK. **This is also a genuine ambiguity in the checker itself worth flagging**: the script only reads `status:`
frontmatter, not todo completeness — a status-only terminal check cannot distinguish "the whole doc is done, just never
archived" from "the PRIMARY finding is done but standing follow-ups were deliberately kept open under the same doc."
Recommend (not applied — this is a judgment call, not a provable fact): either (a) accept this as a legitimate corpus
convention and teach the checker to skip a `status: resolved` doc that still has open todos (treat it as a still-active
doc for archival purposes, only flag it once 0 open remain), or (b) tighten the convention so a `status: resolved` doc's
open follow-ups get split into a fresh child issue doc immediately, keeping the resolved doc's own todo-set 100% closed.
Routed here rather than resolved unilaterally — this is a policy preference, not a checkable fact.

### C2 — `codex_vs_repo_docs_ssot_audit_2026_06_01.md` false-positive dangling-ref quotes (P3, no action needed)

**Refuted as a live finding** (confirmed false positive, not a corpus defect): `check_codex_refs.sh` flags this doc for
citing `codex/02-data/per-category-bucket-layouts.md` and `codex/09-strategy/cross-cutting/operational-modes-matrix.md`,
neither of which exist. Read in context (lines 683-687, 906-907): the doc is itself an audit-result record, and both
mentions are VERBATIM QUOTES of what OTHER files (`docs/audits/dart-v2-audit-context.md`,
`docs/portable-backtest-criteria.md`, a README — all outside `plans/**`) cite incorrectly, immediately followed by
`[actual: <correct path>]` annotations. This is the "resolved issue doc describing history" false-positive class
SKILL.md explicitly excludes. No fix applied (the quoted files themselves are out of this run's `plans/**` scope even if
their own refs are still stale — not verified here).

## Doc-drift

(none yet — appended as STEP 3/4 confirm plan<->codex drift; flagged only, never auto-fixed)

## Hygiene fixes

**check_reference_paths.py FORMAT ratchet** (Phase-0 mechanical-adjudicator candidate): whole-corpus was 205 violations
vs baseline 161 (44 over). Ran a plans/active/\*\* + plans/epics/\*\*-scoped invocation of the canonical
`fix_reference_paths.py` transforms (never touched codex/\*\* or plans/archive/\*\* — both out of this skill's edit
scope per plan_reconciler.md's HARD LIMIT "NO touching files outside plans/\*\* except reading" and SKILL.md's "codex
and archive are out of audit scope"). 22 files fixed (bare `codex/...` -> `/codex/...`, 3 unambiguous bare `related:`
filenames resolved to full paths). Corpus-wide format count now 170 (still 9 over baseline — the remainder is
codex-internal ambiguous refs + plans/archive/\*\* content, both out of scope for this run; tracked already by
`/plans/active/issues/reference_path_convention_2026_07_23.md`, status open, 6 todos).

**2 confirmed dangling codex refs (directory-swap bug), HARD-verified via `ls`**: both
`cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md` and its `_finalize` companion cited
`ao-dispatch-batch-naming-and-conflict-check.md` under `/codex/12-agent-workflow/` (wrong — file lives at
`/codex/11-project-management/`) and `plan-completion-and-archival-discipline.md` under the reverse swap. The finalize
plan's own 2026-08-01 context-scout pass had already diagnosed this exact swap in its Progress Log (`context_scope` was
already correct) but explicitly left the doc-body "## Codex SSOTs" section unedited, flagging it "for a future doc-body
fix." Fixed both docs' body sections this run.

**Whole-corpus `check_codex_refs.sh`**: 5 broken refs found. 2 were the directory-swap bug above (fixed). 2
(`per-category-bucket-layouts.md`, `operational-modes-matrix.md` in `codex_vs_repo_docs_ssot_audit_2026_06_01.md`) are
confirmed FALSE POSITIVES — that doc is itself an audit-result doc quoting OTHER files' (`docs/audits/`, a README) stale
refs as findings, not making a live claim of its own; the quoted files are outside `plans/**` scope regardless. 1
(`sports-canonical-league-cup-registry.md` in
`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`) is a `New:` — a not-yet-created codex doc
this still-active (6 open todos) plan proposes to write as its own deliverable, not a stale/broken reference.

**check_terminal_status_archived.py ratchet**: 13 violations vs baseline 1 — see `## Archive candidates` below, 7
archived, 6 deliberately left (3 grace-protected, 3 with genuine open follow-up work).

**check_archive_candidates.sh ratchet**: 31 candidates vs baseline 4 (0-open-todo docs still `status: active`/`open` in
plans/active — a DIFFERENT, earlier-stage signal than the terminal-status check: these never had their `status` advanced
at all, not just never physically moved). Overlaps significantly with the terminal-status set. Working through the
non-overlapping remainder — see Archive candidates section, updated as verified.

## Filed

- `github_actions_billing_wall_recurrence_2026_07_29.md`,
  `github_actions_total_fleet_outage_startup_failure_2026_07_30.md`,
  `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` — see `## Contradictions` below (same
  underlying pattern, filed together).

## Archive candidates (operator review)

**Archived this run (7, all verified via HARD sha/artifact evidence, all non-grace, all unlocked)** — full detail +
evidence citations in the checkpoint-2 commit message:

1. `delta_one_dependency_checker_ignores_passthrough_feature_group_2026_07_31.md` — features-service@f57d11ae
2. `delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md` — features-service@9e70fbac
3. `deployment_ui_coverage_floor_red_preexisting_2026_07_31.md` — unified-trading-pm@01ff2a3f5 + @5e13d9421
4. `features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md` —
   unified-trading-library@06190d77/@5ab129d4/@880b2fb2
5. `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` — superseded by
   `mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`, live-verified manifest read
6. `tradfi_manifest_consolidator_staleness_budget_missing_2026_07_31.md` — unified-trading-library@2fa09f1d
7. `utl_get_captured_instruments_unfiltered_manifest_read_2026_07_31.md` — unified-trading-library@6c0ca59b

**Referrer-fix gap (grace-blocked)**: `expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md` references item
7 above (both frontmatter `related:` and inline prose) but is itself inside the 12h grace window (freshly touched,
age=0h at check time) — could not edit. Now a genuinely dangling `/plans/active/issues/...` reference (target moved to
`/plans/archive/issues/...`). **Follow-up needed**: once grace clears, repoint both occurrences in that file to
`/plans/archive/issues/utl_get_captured_instruments_unfiltered_manifest_read_2026_07_31.md`.

**NOT archived — 3 grace-protected (read-only context this run, unmodified)**:

- `aave_plasma_is_denominator_drift_no_producer_2026_08_01.md` (age 0h)
- `instruments_backfill_launcher_missing_sports_provider_passthrough_2026_08_01.md` (age 0h)
- `plan_commit_sha_evidence_regression_7e0aab35f_2026_07_31.md` (age 0h)

**NOT archived — 3 with genuinely open follow-up work despite `status: resolved`** — see `## Contradictions`.

**`check_archive_candidates.sh` batch (0-open-todo docs, `status` never advanced at all)**: 24 candidates vs baseline 4
(3 grace-protected, overlapping with the terminal-status set above). Archived 2 more after individual verification (both
`status: open` -> `resolved`, both HARD-evidenced, referrers fixed):

8. `ag_closeout_audit_ao_parked_2026_07_31.md` — sole actionable finding independently re-verified via direct read of
   its target doc's corrected section; 2 other findings were already-documented non-AO-eligible classifications needing
   no action. Reconciliation ledger balanced (3==3).
9. `ag_closeout_audit_scope_widening_triage_2026_07_26.md` — all 3 todos HARD-evidenced (unified-trading-pm@3a5b294ef),
   cross-corroborated against the sibling doc below.

**Reviewed, correctly NOT archived (false positives from the checker's crude 0-open-checkbox logic — genuine prose-form
remaining work, or a structural finalize-plan-coverage gate)**:

- `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` — na-eligibility-audit already confirmed
  (2026-07-31) this doc's own Progress Log documents genuine prose-form deferred work (an operator-gated GCS-catalog
  `--apply` rewrite) that the checkbox count doesn't see.
- `cefi_deribit_binance_futures_bundle_verification_2026_06_20_finalize_2026_07_27.md` — explicitly documents (own
  Progress Log) that it must stay active to keep serving as the `depends_on`+`gate_on_depends` structural gate for a
  sibling plan with real residual work (a Track-2 backfill VM preempted, not recovered).
- `deployment_registry_firestore_migration_2026_07_14.md` — hub/overview doc for an in-progress 6-phase migration chain;
  its own companion finalize plan (already archived) explicitly reserved the archival decision for Phase 5, gated on
  Phase 3's still-active HALT. Independently re-verified: `deployment_registry_firestore_p3_cutover_2026_07_14.md` is
  `status: active`, `deployment_registry_firestore_p5_verify_2026_07_14.md` is `status: draft`.
- `prediction_consolidated_closeout_2026_07_18.md` — a standing consolidated-closeout hub/index doc by design (not a
  finished task), multiply re-verified by na-eligibility-audit (2026-07-30, 2026-07-31).
- `ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` — all 5 numbered todos done, but carries a genuine,
  still-open `## BLOCKED-OPERATOR-DECISION` section (3 named options A/B/C + a [WORKER REC]) about whether/how to retag
  ~20 habitually-mistagged `cross-cutting` docs into `ci`/`ao`. **Parked into this run's `parked_items`** — see below.

## Refuted (dropped by verify)

(none yet)

## Coverage (hunters / batches / docs)

(populated at STEP 7)

## Plans not reached

(populated if genuinely not reached before context/time budget runs out)
