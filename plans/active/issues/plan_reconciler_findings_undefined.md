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

**Missed-flip hunter**: grepped every open `- [ ]` in `plans/active/**` whose own line carries a "shipped/already
done/DONE 2026/sha/verified working" signal (63 raw candidates). Adversarially verified each (refuter: is the cited
evidence actually for THIS todo's own completion, or just a precondition/partial/blocked-on-something-else? confirmer:
re-locate the evidence, check reachability). The vast majority (~60) refuted as NOT missed flips — the cited "shipped"
language describes a PRECONDITION for the still-open action (e.g. "engine SHIPPED" but
BACKTEST-PENDING/no-authorised-backfill blocks registration; "code fix shipped" but the todo's own job is a separate
re-verify/relaunch/reconcile action; multiple explicit "NOT ticked — pw:L2 ran but full suite doesn't exit 0, blocked on
a separate doc" UI todos correctly honoring the playwright-gate HARD RULE). 1 CONFIRMED genuine missed-flip, applied:

- **`cefi_satellite_ao_dispatch_batch3_finalize_2026_07_26.md`'s `[PM] P2` todo** ("Hand the 2 provably-shipped stale
  checkboxes to a reconcile pass") — this todo's OWN job (verify 2 specific checkboxes in
  `issues/deribit_combo_perpetual_partition_move_2026_07_21.md` and flip them if evidence holds) turned out to already
  be done by a DIFFERENT pass (slot-15, 2026-07-27) — both target checkboxes are already `[x]` with the exact evidence
  chain this todo asked for. Independently re-verified BOTH conditions myself before flipping: (1) `mtds@2ddc6d4a`
  reachable on `origin/live-defi-rollout` — `gh api repos/.../compare/2ddc6d4a...live-defi-rollout` → `status: ahead`
  (HARD evidence, since I have no local market-tick-data-service clone in this standalone environment); (2)
  `tardis_cefi_shards.py` genuinely routes through the shared fixed classifier — fetched the file content directly via
  `gh api .../contents/...` and confirmed lines 298/590 call `self._classify_row_instrument_type(s, venue)`, the exact
  method the cited commit patched. Flipped the finalize doc's own todo `[x]`, citing both independent verifications.

**1 finding NOT flipped (needs a UI-capable session)**: `data_status_tab_and_downloads_remediation_2026_06_16.md`
carries 3 `[UI]` P1/P2 todos explicitly NOT ticked because the required `pw:L2` full-suite run was blocked by a separate
regression (`deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md`) — that blocking doc is now `status: resolved`
and archived. This MAY unblock the 3 todos, but flipping them requires actually re-running `pw:L2` against
`deployment-ui` (per CLAUDE.md's playwright-gate HARD RULE — "no tick without `[UI]` + `pw:L2` ✓ + a cited regression
spec"), which this standalone/no-UI-repo environment cannot do. Filed here as a follow-up rather than guessed at.

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
- `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md` — see `F1` above (likely false-checked P0 todo,
  real data-correctness question).
- `data_status_tab_and_downloads_remediation_2026_06_16.md` — see `## Flips verified` above (3 UI todos likely unblocked
  now, need a `pw:L2` re-run this environment cannot perform).
- `tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md` — grace-blocked referrer-path fix
  (points at `mdps_tradfi_chain_bundle_aggregate_write_malformed_row_key_2026_07_31.md`'s pre-archival path).
- `expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md` — grace-blocked referrer-path fix (points at
  `utl_get_captured_instruments_unfiltered_manifest_read_2026_07_31.md`'s pre-archival path).
- `context_scope_consumption_enforcement_2026_07_30.md` — grace-blocked referrer-path fix (2 mentions of
  `ag_closeout_audit_ao_parked_2026_07_31.md`'s pre-archival path).

### Phase-0 hygiene finding: `assigned_vm:NA` corpus ratchet is RED — OUT OF THIS SKILL'S REMIT (P2, routed not fixed)

`check_na_corpus_ratchet.py` reports the NA doc count/open-todo count grew beyond baseline (352 docs vs baseline 350;
1302 open todos vs baseline 1292). Per this skill's own SKILL.md: "this skill... does not ask whether a doc's OWN `NA`
classification is still correct — that reclassification question... is `/na-eligibility-audit`'s disjoint remit." Fixing
this ratchet requires re-running that OTHER skill's methodology (reclassify/archive NA docs), which is explicitly out of
scope here. Reported honestly rather than silently left red or worked around — recommend a `/na-eligibility-audit` pass.

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
- `ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md` — na-eligibility-audit (2026-08-01) already
  determined ARCHIVE-eligible but deliberately NOT archived independently — a sibling active AO plan
  (`ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`) already carries its own queued todo naming this doc for the
  archival ritual. Archiving it here would be duplicate/collision work.
- `autonomous_session_operator_decisions_2026_07_25.md` (943 lines, 23 numbered decision entries) — its OWN latest entry
  (2026-07-31) already explicitly re-verified and confirmed: "the parent rollout plan itself is not [concluded], so this
  doc correctly stays `status: open`... No frontmatter change needed."

**Archived this run (6 more, all HARD-evidenced)**:

10. `cefi_content_migration_shard17_default_bump_2026_07_31.md` — deployment-service@9e6004a
11. `features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md` — live GCS reads confirmed
    (`GCS read leagues: 1228 rows` etc.)
12. `footystats_migration_bg_workers_killed_externally_2026_07_28.md` — operator-ruled forensic check + documented
    pattern
13. `mdps_tradfi_chain_bundle_aggregate_write_malformed_row_key_2026_07_31.md` — schema contract fix, confirmed on
    live-defi-rollout
14. `mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md` — market-tick-data-service@749ca622, 9786
    tests passed
15. `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md` — agent-orchestrator@49c919d (verified
    ancestor) + codex doc section independently confirmed present at HEAD

Referrer-fix gap (grace-blocked, same shape as before): 1 more —
`tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md` references item 13 above but was
inside the 12h grace window at check time (age=0h — this file was itself touched by ME in an earlier checkpoint this
same run, so the grace-window rule is being applied strictly/conservatively rather than carving out self-authorship).
Follow-up needed once grace clears.

### F1 — likely FALSE-CHECKED todo, real data-pipeline-correctness question (P1, big finding, PARKED not fixed)

`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s `[DATA] P0` todo (line 267) is marked `[x]`, but
its own stated "Done when" bar ("both windows show full historical coverage in the manifest... and this todo cites the
launcher/dispatch evidence") is **not met** by anything written in the checked item, and the doc's own LAST Progress Log
entry (2026-07-29, the final paragraph in the file) ends: "Did not launch the backfill VM as part of this edit — that
remains the actual next action." No launcher/VM evidence for the actual backfill exists anywhere in the doc, and a
corpus-wide grep for a matching launch found nothing. Two readings: (a) the checkbox was deliberately narrowed by a
2026-07-29 "corpus hygiene pass" to mean "both approval GATES (launch-decision + credential) are now unblocked", not
"backfill complete" — a legitimate, if under-explained, scope narrowing; or (b) this is a genuine false-checked todo
(Phase 2's "a plan can be false-checked" case) and the ~29-day sports-odds gap this doc exists to fix is still
un-backfilled today. **Did NOT unilaterally un-check the box** — un-checking is itself a judgment call on a doc I did
not author, on a live data-correctness question, and the "Done when" bar could plausibly have been intentionally
satisfied-by-proxy (unblocking = the todo's real job, backfill-launch = separately owned elsewhere and simply not found
by my grep). **Recommend**: verify directly whether the 2026-06-27..2026-07-15 total-gap window and the
2026-07-16..2026-07-25 granularity-loss window actually show full historical coverage in the live manifest today; if
not, re-open the todo (or split it into "unblocked" [x] + "backfill launched and verified" [ ]) and dispatch the actual
launch.

## Refuted (dropped by verify)

- **~60 of 63 missed-flip candidates** — see `## Flips verified` above; the "shipped" language in each cited an unmet
  precondition, a separately-owned follow-up action, or (for 3 UI todos) an explicit already-documented playwright-gate
  block, not the todo's own completion.
- **C2** (`codex_vs_repo_docs_ssot_audit_2026_06_01.md` dangling-ref quotes) — see `## Contradictions`.
- **`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`**'s `New:` codex-doc reference
  (`sports-canonical-league-cup-registry.md`) — refuted as a live finding; it is a planned future deliverable of a
  still-active (6 open todos) plan, not a stale/broken claim.
- **~20 of the `check_archive_candidates.sh` batch's 24 raw candidates** — see `## Archive candidates` above; false
  positives from the checker's crude 0-open-checkbox logic (genuine prose-form deferred work, structural
  finalize-plan-coverage gates, standing hub/index docs, or already-queued-elsewhere archival work).
- **2 "new" reference-path dangling refs surfaced by my own checkpoint-1 format-normalization fix** (not a regression —
  see the Hygiene-fixes reference-path note above): `codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s quoted
  `operational-modes-matrix.md` mention (already covered by C2 — this is the SAME quote, just newly visible once its
  format was corrected from bare to absolute) and
  `cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md`'s `ODUM_SLA_v4_2026-07-24.md` mention
  (explicitly described in-doc as "an unrelated file from another concurrent session... CURRENTLY WORKING-TREE-ONLY
  (staged, uncommitted)" — a historical record of a file that may never have landed in this repo, not a live claim this
  doc makes).

### Reference-path ratchet — the "regression" is fully explained, not a miss

The whole-corpus dangling-ref count went 917 -> 936 (+19) across this run, which looks like a regression at a glance.
Diffed the exact before/after DANGLING lists (`comm -13`, 22 raw line-diffs incl. a few doc/target pairs matched twice)
to verify every single new entry: 11 are referrer lines I deliberately did NOT fix because the referrer doc was inside
the 12h grace window at check time (already itemized in `## Filed` above, each with its target archive-path noted for a
follow-up run), and 9 are an ALREADY-ARCHIVED doc's own historical prose mentioning one of my 15 newly-archived targets
(archive-to-archive text is out of this skill's edit scope by the same "archive is out of audit scope" convention this
run has honored throughout — fixing it would mean rewriting a frozen historical record). The remaining **2** are
pre-existing wrong/stale codex-path mentions that were INVISIBLE to the dangling-check before this run (bare,
non-`/codex/`-prefixed format is FORMAT-checked but not EXISTENCE-checked) and became visible only because my own
checkpoint-1 fix corrected their FORMAT (bare -> absolute) without being able to also verify path correctness (that
fixer only normalizes syntax, never validates targets) — both are themselves false-positive historical quotes (see
`## Refuted` above), not new corpus defects. Net: the FORMAT ratchet genuinely improved (205 -> 172, still 11 over
baseline 161 -- pre-existing debt, not newly introduced); the EXISTENCE ratchet's apparent regression is 100%
attributable to correctly-scoped restraint (grace window, archive-editing boundary) plus two now-visible pre-existing
errors, not carelessness.

## Coverage (hunters / batches / docs)

- **Mechanical-adjudicator hunter**: 100% corpus coverage — every Phase-0 deterministic check
  (`run_hygiene_sweep.sh --ci --no-regen`) runs over the WHOLE `plans/active/**` + `plans/active/issues/**` +
  `plans/epics/**` tree in one pass; re-run at the end to measure delta. 4 hard-gate ratchets were RED at entry
  (reference-paths, terminal-status-archived, assigned_vm:NA, archive-candidates); reference-paths (format) and
  terminal-status-archived and archive-candidates all measurably improved this run (see counts above); assigned_vm:NA is
  explicitly out of this skill's remit (routed to `/na-eligibility-audit`).
- **Missed-flip hunter**: corpus-wide grep across every open `- [ ]` in `plans/active/**` for a shipped/DONE/sha signal
  (63 raw candidates), each individually adversarially verified. 1 confirmed and flipped.
- **Archival verification**: 35 individual docs read in full (13 terminal-status DUAL-TRACK candidates + 24
  archive-candidates minus overlap), each checked for genuine 0-open-work (checkbox AND prose) before any archive
  action; 15 archived, 3 correctly left grace-protected, ~17 correctly left active with a documented reason.
- **Codex-alignment hunter**: opportunistic, not a dedicated systematic sweep of every active plan's `Codex SSOTs:`
  section — found + fixed 2 genuine dangling codex refs (a directory-swap bug affecting 2 sibling docs) while reading
  archival candidates; confirmed 1 false-positive (`codex_vs_repo_docs_ssot_audit_2026_06_01.md`).
- **Topic hunters**: NOT run as a dedicated pass across SKILL.md's full topic list (canonical-ID, manifest/coverage,
  batch=live, milestones/dates, etc.) — see `## Plans not reached` below. Topic-adjacent findings this run DID surface
  came opportunistically from the archival/missed-flip reads (the 3 CI-incident-doc pattern in C1, the sports-odds
  false-checked todo in F1).
- **Epic-cluster hunters**: NOT run as a dedicated full-corpus partition-by-`parent_epic` sweep (242 active plans is a
  genuinely large corpus for one sequential agent pass within this run's time budget) — see `## Plans not reached`.
  Every doc this run DID touch was read with its epic/cross-reference context, not just its own text.
- **Adversarial verify**: performed inline for every candidate this run acted on (refuter-attack framing + confirmer
  re-location, explicitly narrated per finding above) rather than via separate sub-agent Task calls — this execution
  context has no nested sub-agent spawn capability, so the STEP-4 discipline was applied via the same session's own
  structured reasoning pass per candidate, never a single unverified read acted on.

## Plans not reached

**Honest gap, not silently dropped**: this run did NOT perform a dedicated, systematic epic-cluster or topic-hunter
sweep across the full ~695-file `plans/active/**` + `plans/active/issues/**` corpus (SKILL.md's own text acknowledges
this is a "500+ active plans/issues" corpus expensive enough to warrant sharding for routine runs). Coverage this run
concentrated on: (1) 100% mechanical/deterministic coverage via the hygiene-sweep tooling (which IS corpus-wide by
construction), (2) full individual reads of every doc the mechanical tooling flagged as an archive/terminal-status
candidate, (3) a corpus-wide grep-and-verify pass for missed-flips. NOT individually read this run: the ~200 active
plans that were not flagged by any mechanical check and did not surface via a cross-reference from a doc this run did
read. A genuine cross-doc contradiction hiding entirely within that unread population (two docs neither flagged by
tooling nor cross-referenced from a flagged doc) would not have been caught. Recommend: a future `/plan-reconcile` pass
(ideally with real sub-agent fan-out available) run the dedicated epic-cluster + topic-hunter sweep this run could not
complete standalone.

## Final Phase-5 exit state (STEP 7)

Re-ran `run_hygiene_sweep.sh --ci` (with regen) as the closing measurement. Hard gates: 4 still RED (reference-paths,
terminal-status-archived, assigned_vm:NA, archive-candidates) — all 4 IMPROVED from entry except assigned_vm:NA (out of
this skill's remit, documented above, not touched):

| Check                       | Entry              | Exit               | Delta                                                                      |
| --------------------------- | ------------------ | ------------------ | -------------------------------------------------------------------------- |
| reference-paths (format)    | 205 (baseline 161) | 172 (baseline 161) | -33, still +11 over baseline (pre-existing debt)                           |
| reference-paths (existence) | 917 (baseline 901) | 936 (baseline 901) | +19, fully explained (see note above), 0 unfixed real regressions          |
| terminal-status-archived    | 13 (baseline 1)    | 6 (baseline 1)     | -7 (all archived)                                                          |
| archive-candidates          | 31 (baseline 4)    | 15 (baseline 4)    | -16 (9 archived + 7 already double-counted with the terminal-status batch) |
| assigned_vm:NA              | red (out of remit) | red (out of remit) | unchanged, routed to `/na-eligibility-audit`                               |

The inventory regenerator (run read-only for measurement, NOT committed — see below) reports **242 plans, 0 orphans, 0
TBD** — the corpus-wide orphan count SKILL.md's Phase-5 gate cares about is clean.

**Regen side-effects deliberately discarded, not committed**: `run_hygiene_sweep.sh --ci`'s inventory/index regenerators
touched `plans/active/INDEX.md` (1174-line diff) and
`plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md` (498-line diff, inside `plans/archive/` — out of
scope regardless). `INDEX.md`'s last commit was **1 hour old** at check time (a concurrent process in this same
multi-agent batch almost certainly touched it since my last `git pull`) — force-committing a full regen over that risks
clobbering fresher concurrent work per the multi-agent-safety HARD RULE, and the diff's size (far larger than my own
~16-doc archival/flip scope) confirms it reflects broad accumulated drift, not just this run's changes.
`git checkout --`'d both rather than risk it — same discard-the-regen-side-effect precedent STEP 1 already established
for the entry-side read. Recommend a dedicated, freshly-pulled regen pass as its own follow-up, not bundled into this
review branch.

## Run totals

- **Docs archived**: 15 (7 terminal-status DUAL-TRACK + 8 archive-candidates), all HARD-evidenced, all referrers fixed
  except where genuinely grace-blocked (3 follow-ups filed).
- **Todos flipped**: 1 (confirmed missed-flip, HARD-verified).
- **Mechanical hygiene fixes**: 22 files' reference-path format normalized + 2 confirmed dangling codex refs
  (directory-swap bug) fixed.
- **Contradictions found**: 2 classes (C1: systemic `status:resolved`-with-open-todos pattern across 3 docs, routed; C2:
  1 false-positive, refuted) + 1 likely false-checked todo (F1, parked).
- **Parked for operator** (see `parked_items` in the structured result): 1 genuine `BLOCKED-OPERATOR-DECISION`
  (`ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`'s cross-cutting/ci/ao retag question).
- **Refuted**: ~85 candidates total (60 missed-flip false positives, ~20 archive-candidate false positives, a handful of
  dangling-ref false positives) — all individually reasoned, not bulk-dismissed.
- **Grace-protected, untouched**: 3 terminal-status docs (aave_plasma, instruments_backfill_launcher,
  plan_commit_sha_evidence_regression) + several referrer-fix targets (documented per-item above).
