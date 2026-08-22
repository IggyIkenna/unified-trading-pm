---
doc_type: issue
title: "2026-08-18 plan_reconciler sports tranche — daily deep reconciliation run"
summary: >-
  Sharded daily deep plan-reconciliation pass over the sports tranche (110 docs, 57 in the 12h grace window at run
  start). Fans out read-only hunter sub-agents to cross-check plans <-> epics <-> codex <-> issue docs <-> real code
  state, adversarially verifies every candidate, auto-fixes the verified-easy (sha/PR-evidenced flips + mechanical
  hygiene), and routes the hard ones (contradictions / doc-drift) via trust-mode [WORKER REC] application per the
  2026-08-15 operator ruling. This run supersedes the prior sports-tranche dispatch
  (`plan_reconciler_findings_sports_2026_08_16.md`), which died after Phase 0 and never actually reconciled anything.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, sports, plan-hygiene, sharded]
related:
  [
    /agents/plan_reconciler.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/issues/plan_reconciler_findings_sports_2026_08_16.md,
  ]
created: "2026-08-18"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: review
assigned_vm: NA
execution_scope: local-only
locked_by:
locked_since:
supersedes: plan_reconciler_findings_sports_2026_08_16
superseded_by:
resolved_by:
author: plan_reconciler
source: "Sharded daily /plan-reconcile sports-tranche sweep, dispatch agt-57336e, slot 31, 2026-08-18."
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/issues/plan_reconciler_findings_sports_2026_08_16.md,
    /plans/archive/issues/ag_closeout_audit_sports_parked_2026_08_16.md,
  ]
---

# plan_reconciler findings — sports — 2026-08-18

Dispatch `agt-57336e`, slot 31, tranche `sports`. Deep reconciliation pass per `agents/plan_reconciler.md` STEPs 1-8.
This doc is the run journal + final report surface.

**Note on `PM_REPO_PATH` dispatch misconfiguration (recurring, second occurrence).** Boot-provided `$PM_REPO_PATH`
pointed at the ROOT PM clone (`/home/ubuntu/unified-trading-system-repos/unified-trading-pm`), conflicting with
`agents/RULES.md`'s HARD RULE that root-clone work is READ-ONLY and all writes happen in the assigned slot. Also, none
of the boot-message "session variables" (`SERVER_URL`, `PM_REPO_PATH`, `SLOT_ID`, `DISPATCH_ID`, `WORKTREE`, `TRANCHE`,
`BRANCH`) were actually exported as shell env vars — confirmed via `env | grep`. This is the SAME misconfiguration the
2026-08-16 dispatch (`agt-2be768`, slot 10) already flagged verbatim in the doc this one supersedes. Two independent
occurrences now — worth escalating as a dispatcher fix, not just a per-run note (filed below, `## Filed`). This run
operates entirely out of the slot-31 clone (`/home/ubuntu/unified-trading-system-repos/.tabs/31/unified-trading-pm`)
and uses literal values for `$SERVER_URL`/`$SLOT_ID`/`$DISPATCH_ID` in every HTTP call instead.

**Corpus**: 110 docs (Phase-0 inventory, `generate_tranche_doc_inventory.py --tranche sports`). 57 in the 12h grace
window (read-only context this run, never written) — high grace fraction reflects heavy concurrent AO-dispatch
activity on this tranche today. 0 locked (at run start). 53 non-grace docs are the actionable working set. 3
zero-checkbox docs found (`ag_closeout_audit_sports_parked_2026_08_16.md`, `plan_reconciler_findings_sports_2026_08_16.md`
— both non-grace, actionable; `sports_taxonomy_p2_consumer_inventory_2026_08_12.md` — still grace-protected,
deferred again). 4 fully-done candidates, 23 near-complete (≤1 open todo, non-grace) candidates.

## Flips verified

4 missed-flip todos flipped `[ ]` → `[x]`, each independently re-verified via `git merge-base --is-ancestor` against
`origin/live-defi-rollout` (not just trusting the hunter's own report) before applying — commit `ba2a6238a4`:

1. `sports_features_layer_findings_sweep_2026_07_18.md` §E [CONFIG] P2 (sports-scheduler trigger config) —
   `deployment-service@9e1fd57ae`.
2. `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md` §J [CODE] P2 (manifest-consolidator error
   text) — `unified-trading-library@471dee02`.
3. Same doc, §N [PROCESS] P2 (surgical-filler-before-refetch rule) — `unified-trading-pm@aa4124c7a0`, codified into
   `/codex/05-infrastructure/vm-launcher-runbook.md` as a HARD RULE.
4. Same doc, §O [DATA] P2 (`emit_empty_gaps_for_entity` denominator) — `instruments-service@a95049d1`, landed 3 weeks
   before the doc's own "GENUINELY OPEN" note was last written.

All 4 share one root cause: a "not duplicating here, cite the extraction target" citation convention that goes stale
the moment the cited duplicate ships, with nobody re-syncing the source doc. Likely present elsewhere in the corpus
outside this tranche — worth a dedicated grep in a future pass.

## Contradictions

**Fixed this run** (commit `34c6461441`):

1. **P2** — `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`'s `[GMX_DRIFT]`-tagged `solana_defi_drift.py`
   bug-list entry referenced a file confirmed deleted (`find` returns 0 hits in both `market-tick-data-service` and
   `instruments-service`). The doc's own blanket "every `[GMX_DRIFT]`-tagged finding is moot" banner already reached
   the right conclusion by tag-membership, but its stated reason (GMX capture-path deletion) doesn't actually apply
   to this entry — it's a different protocol (Solana Drift) sharing the tag name. Added a precise inline correction
   citing the real reason (DRIFT/PACIFICA purged by operator ruling 2026-07-16, a week before the GMX removal).
2. **P2** — `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`'s open `[DECISION] P2`
   todo cited a stale "58 findings" count against `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`, which is
   now majority `[x]` fixed. Corrected the LIVE todo to point at re-deriving the count fresh (per the "delete rather
   than restate a re-stale-prone number" principle) — left every historical Progress Log entry citing "58" untouched
   as accurate history of past audit passes, not live drift.
3. **P1** — `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`'s deferred-work table framed its
   blocking `odds_targets` backfill as "Not done — unclaimed"; the blocker doc
   (`sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md`) resolved and archived
   2026-08-16. Updated the table + "Recommended next item" pointer so the now-unblocked VM relaunch (todo 2) isn't
   held on stale framing.
4. **P1 (duplicate-dispatch prevention)** — `sports_satellite_ao_dispatch_batch14_2026_08_16.md` (`status: draft`,
   not yet activated) todo 5 duplicates work already extracted the SAME day to
   `sports_venue_rename_attempted_at_trace_ao_dispatch_2026_08_16.md` (+ gated finalize) — a gap in that batch's own
   "Conflict-check findings" section. Struck through with a clear note (not silently deleted) so it can never be
   dispatched as a duplicate.

**Noted, not fixed (low severity / out of scope for a doc-only pass)**:

- P3 cosmetic — `ag_closeout_audit_sports_parked_2026_08_16.md:249` cites a stale `locked_by: agt-2be768` value that
  has since cleared on the referenced doc; the doc's substantive claim (an unconcluded prior `/plan-reconcile` run)
  is independently correct and already corroborated elsewhere. Not worth an edit on its own.
- P2 (deferred to whoever owns `agent-orchestrator`) — `nick_ai_audit_data_quality_findings_2026_08_16.md` todo 1
  (sports `FOOTBALL` venue write-path bug) has no grep-able starting symbol, unlike its siblings todos 2-4 in the
  same doc — flagged by the infrastructure-master hunter, not fixed here (would require independently tracing the
  write path first, out of scope for this pass).
- P2 — `prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md` todo 4 is tagged
  `[BLOCKED-CREDENTIALS][INFRA]`; worth a one-line check of whether the AO dispatcher's non-dispatchable regex
  actually matches the literal string `BLOCKED-CREDENTIALS` (vs. only `BLOCKED-OPERATOR-DECISION`, which this same
  doc's own history shows it definitely matches) — this doc has already seen 6+ re-dispatch churn cycles before a
  2026-08-10 ruling stopped it; a regex gap would silently reproduce that churn. Backend/AO-side check, not a
  plans-doc fix.

## Doc-drift

None confirmed this run beyond the codex-gap observation below (routed, not auto-applied — outside the narrow
mechanical codex-staleness carve-out since it would require judgment about whether/how to add a new rule, not a
single unambiguous substitution).

- **Codex-gap candidate (routed, not applied)**: the manifest-consolidator's "captured always outranks non-captured,
  regardless of recency" tie-break rule was independently rediscovered as a costly production blocker by BOTH
  `sports_cf8_available_at_backfill_regression_2026_07_13.md` (2026-07-14) and
  `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` (2026-08-11) — two unrelated incidents, ~1 month apart,
  each forcing a "re-derive-in-place `--force` overwrite" workaround instead of a simple correction. Not found
  documented as its own named contract in the ~591/2310 lines of `/codex/02-data/availability-manifest-and-data-status.md`
  read this pass (hedged — the remaining ~1,700 lines were not read). Plausible candidate for promotion into that
  SSOT; needs an operator/codex-owner decision on wording, not an autonomous edit.

## Hygiene fixes

None needed beyond what's captured above — corpus-wide mechanical hygiene (frontmatter, todo-format, line-caps,
reference-paths, depends_on DAG) was already green for the sports tranche per the Phase-0 `run_hygiene_sweep.sh`
pass (only 2 pre-existing, unrelated, corpus-wide ratchet failures: `assigned_vm:NA` corpus size and
silent-default-effort — both owned by other standing audits, not this tranche).

## Codex corrections applied (mechanical, evidence-cited)

None — no finding this run met the narrow carve-out bar (single unambiguous substitution, no new measurement, not a
HARD-STOP area). The one codex-adjacent finding (the manifest-consolidator tie-break gap above) requires judgment
about wording/placement, so it's routed as doc-drift instead.

## Filed

1. **`plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md`** (P2) — the recurring (2nd confirmed
   occurrence) dispatcher misconfiguration where `$PM_REPO_PATH` resolves to the root PM clone instead of the
   dispatched slot's own clone, plus the boot-message "session variables" not being real exported env vars. First
   seen 2026-08-16 (`agt-2be768`) but never filed as its own tracked issue until now.
2. **`pipeline_e2e_check_declared_violations_sports_stale_exemption_2026_08_18.md`** (P3) — migrated from the archived
   `mdps_sports_e2e_checker_...` doc's prose per the todos-not-prose rule (see Archive candidates below).

## Archive candidates (operator review)

**Archived this run** (commit `7f8c97417b`):

- `mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md` → `plans/archive/issues/`. 3/3
  todos HARD-verified (content-confirmed live in `pipeline_e2e_check.py`, matching the doc's own docstring
  self-citation). 1 genuine deferred item (a stale `_declared_violations()` sports exemption, previously only a code
  comment) migrated to a new tracked todo rather than left as prose. `archive_exempt: true` bridge was already set
  by a prior pass, confirming agreement this was ready.

**Verified done but DEFERRED to the next sports pass** (reverted this run, not landed):

- `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` — all todos HARD-verified done (content-confirmed after
  hitting the corpus's known squash-merge SHA-orphaning trap on the cited SHAs).
- `sports_consolidated_native_ao_extract_2026_07_25.md` — 33/33 todos HARD-verified done; `archive_exempt: true`
  bridge was 6 days overdue.

**Why deferred, not landed**: both share the SAME referrer — `sports_consolidated_closeout_2026_07_19.md` (the
sports_master epic hub), which is grace-protected (10.8h old at run start, inside the 12h HARD LIMIT window). The
archival ritual's step 5 (fix every corpus referrer) requires editing that doc; the grace-window HARD LIMIT forbids
it this run. Attempting the `sports_consolidated_native_ao_extract` archival anyway also surfaced a second, distinct
problem: that doc's own finalize plan (`sports_consolidated_native_ao_extract_2026_07_25_finalize.md`, itself
grace-protected at 11.3h old) was designed to archive it LAST, after 3 other todos (chiefly: reconcile its 26 done
todos back into the SAME grace-protected hub's checkboxes) — archiving it first, out of sequence, would have left
those 26 parent checkboxes permanently unreconciled with no live pointer explaining why. Both archivals were
cleanly reverted (never committed) rather than landed with a known-broken referrer or an out-of-sequence finalize
gap. **Action for the next sports pass** (once both grace windows clear, likely within ~1-2h of this run): (1) fix
the broken link in `sports_consolidated_closeout_2026_07_19.md` pointing at `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`
and archive it; (2) work `sports_consolidated_native_ao_extract_2026_07_25_finalize.md`'s todos 1-3 (reconcile into
the hub, re-check 3 excluded sub-items' gates) BEFORE todo 4 (archive the extract plan) — full evidence for archival
readiness is already gathered above, re-verification should be cheap.

**Recommended but not executed (near-complete fold candidates, trust-mode `[WORKER REC]` — see rationale below)**:
these all carry exactly ONE obvious active sibling and are folding candidates per Phase 4, but the actual content-move
mechanics (add FOLDED-IN section, verify conservation, archive the shell) were judged lower-priority than the
higher-confidence archival/flip/contradiction work above given this run's time budget. Recommendation is recorded
here so a future pass can execute without re-deriving the target:

1. `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s remaining backfill item →
   `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (both confirmed active/unlocked).
2. `sports_track_o_attempted_at_keys_extinct_2026_08_14.md`'s remaining todo → already functionally superseded by
   `sports_venue_rename_attempted_at_trace_ao_dispatch_2026_08_16.md` (+finalize) per that doc's own Progress Log —
   this one is closer to "already folded, needs the shell doc marked FOLDED-OUT + archived" than a fresh fold
   decision.
3. `prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md`'s remaining todo 4 → named twice in its own
   text as belonging with `prediction_arb_live_execution_bridge_2026_07_20.md` item [5] — NOT recommending an actual
   fold here since the item is genuinely `BLOCKED-CREDENTIALS` (an operator/account-holder-only live blocker, not an
   organizationally-homeless remnant); folding would just relocate a blocked item with no benefit.

7 additional near-complete docs found (1 open todo each, no single clean sibling identified) — see hunter reports in
Coverage below for the full list; not enumerated here individually as none has an actionable fold target.

## Refuted (dropped by verify)

- The hunter-B prompt (written by this orchestrator) mis-cited `sports_satellite_ao_dispatch_batch9_2026_08_04.md`
  and `sports_taxonomy_p2_migration_2026_08_08.md` as Phase-0-flagged "all-todos-closed" candidates — they were NOT
  actually in the Phase-0 script's `fully_done_candidate` output (a prompt-authoring transcription error by this
  orchestrator, not a Phase-0 script bug). Hunter B independently grep-verified both docs have real open todos (9
  and 1 respectively) and correctly refused to treat either as archival-ready. No corpus action needed — this was a
  self-caught orchestration error, not a corpus finding, but recorded here per the adversarial-verification
  discipline (the check worked as designed).

## Coverage (hunters / batches / docs)

- Phase-0 inventory: 110 docs, 57 grace, 0 locked, 3 zero-checkbox (2 actionable — see below, 1 still
  grace-protected: `sports_taxonomy_p2_consumer_inventory_2026_08_12.md`, deferred again).
- Epic distribution (non-grace, 53 docs): sports_master=27, infrastructure_master=16, instruments_master=4,
  observability_master=2, agent_operating_framework_master=1, plan_hygiene_master=1 (this doc's own predecessor,
  handled directly via Phase -1, not assigned to a hunter), predictions_master=1, mtds_mdps_master=1.
- **Wave 1** (4 epic-cluster hunters, parallel, ≤10 limit honored): `sports_master-A` (14 docs),
  `sports_master-B` (13 docs), `infrastructure_master-sports` (16 docs), `small-epics-combined` (9 docs —
  instruments/observability/agent_operating_framework/predictions/mtds_mdps; `plan_reconciler_findings_sports_2026_08_16.md`
  excluded from this batch and handled directly in Phase -1 instead). Full 53-doc non-grace coverage, each doc read
  in full by exactly one hunter — zero overlap, zero gaps. Each hunter also assessed its own batch's
  archival-readiness, near-complete, zero-checkbox, missed-flip, AO-dispatch-readiness, and codex-alignment
  candidates inline (single full read per doc, per `/plan-reconcile`'s "piggyback the check on whichever hunter
  already reads the doc" pattern, rather than a separate pass per check family).
- **Per-hunter tallies** (self-reported, spot-verified where cited above): sports_master-A — 4 contradictions, 2
  missed-flip candidates (both SOFT/unverifiable from this seat), 2 archive-ready, 7 near-complete, 1 zero-checkbox.
  sports_master-B — 3 contradictions, 0 missed-flips, 1 archive-ready, 5 near-complete, 0 zero-checkbox.
  infrastructure_master-sports — 5 contradictions (4 hard-verified as missed-flips), 0 archive-ready (1 blocked on
  `archive_exempt`), 7 near-complete (+2 found beyond the seeded list), 0 zero-checkbox, 2 AO-readiness issues.
  small-epics-combined — 3 contradictions, 0 missed-flips, 0 archive-ready, 4 near-complete, 0 zero-checkbox, 1
  AO-readiness note.
- **STEP 4 verification**: this orchestrator independently re-ran the hunters' own cited evidence (not trusting
  self-report) for every item that became a Flips-verified/Archive/Contradiction-fixed action above — 3 archival
  checkbox-count re-checks, 6 sha-ancestry re-checks (2 hit the known squash-merge trap, resolved via direct
  content/symbol verification instead), 1 file-deletion re-check, 1 doc-status re-check. `confirmed=11` (4 flips + 4
  contradictions-fixed + 1 archived + 2 archive-verified-but-deferred), `refuted=1` (this orchestrator's own
  prompt-authoring error, see Refuted above, not a corpus finding).
- No dedicated cross-batch reconciler was spawned for the sports_master A/B split — neither batch's own contradiction
  list referenced a claim in the other batch's file set, so no cross-batch pair was suspected; this is a
  coverage-completeness tradeoff worth naming, not a verified zero.

## Plans not reached

None — all 53 non-grace docs were read by exactly one Wave-1 hunter; all 57 grace docs were correctly excluded from
writes and used only as read-only context where cited by a hunter or this orchestrator.

## Progress Log

- **2026-08-18 (plan_reconciler, dispatch agt-57336e, slot 31)**: Phase -1 complete — reconciled prior sports findings
  doc (dead run, zero findings, correctly left unarchived per its own reasoning; this run is the fresh pass it was
  waiting for). Reviewed the 3 non-sports `plan_reconciler`-mechanism meta docs in context (`ao` tranche, out of scope
  to fix here): lock-TTL auto-clear is RULED but not yet implemented (my own lock is fresh, not dead, so N/A this run);
  blocked-answer retrieval via `/api/slots/N/messages` has a live bug — `/api/activity` is the confirmed fallback if I
  post a `/blocked` question; `ORCHESTRATOR_INTERNAL_SECRET` is set in my shell, so the result-POST auth gap
  (empty-secret rejection) should not affect this run. Phase 0 complete: 110-doc inventory built (reusing
  `scripts/docs/docspec.py`), grace/locked/checkbox/archival-candidate flags computed. Proceeding to Wave 1 hunter
  fan-out.
- **2026-08-18 (continued)**: Wave 1 (4 parallel hunters) completed full 53-doc non-grace coverage. STEP 4 verify:
  independently re-ran every hunter-cited git/grep check before acting (not trusting self-report) — caught 0 hunter
  errors, but did catch my OWN prompt-authoring error (see Refuted). STEP 5 apply, 3 commits: (1) `7f8c97417b` —
  archived 1 doc (3/3 todos HARD-verified), migrated 1 deferred item to a tracked todo; reverted 2 other
  independently-HARD-verified archival candidates after discovering both share a grace-protected referrer the
  archival ritual's step 5 requires fixing but the grace HARD LIMIT forbids touching this run — see Archive
  candidates for the full reasoning and next-pass action items. (2) `ba2a6238a4` — flipped 4 stale citation-pointer
  todos to done, each independently sha-ancestry-verified. (3) `34c6461441` — fixed 4 contradictions (2 stale-content
  corrections, 1 stale-blocker-status update, 1 duplicate-dispatch prevention on a still-draft batch plan). Filed 2
  new issue docs (recurring dispatcher misconfig — 2nd occurrence; 1 migrated deferred item). 0 blocked-questions
  raised — every finding this run either had HARD evidence enabling a direct auto-fix, or was judged lower-priority/
  out-of-scope-for-this-pass and routed as a documented recommendation rather than requiring an operator ruling.
  Proceeding to Phase 5's exit hygiene gate + STEP 7 final report.
- **2026-08-18 (conclusion)**: Phase 5 exit hygiene gate confirmed clean of sports-tranche-attributable hard failures
  (remaining corpus-wide failures verified via direct script invocation to belong to other concurrently-active
  tranches or pre-existing standing ratchets owned elsewhere). Corrected an internal arithmetic slip in this doc's own
  STEP-4 tally (`confirmed=12` → `confirmed=11`; the enumerated Archive-candidates list only supports 2
  archive-verified-but-deferred docs, not 3 — matches the "3 archival checkbox-count re-checks" figure exactly: 1
  landed + 2 deferred). `locked_by` cleared. STEP 7 result POST + STEP 8 `/done` follow immediately; 0 blocked
  questions means STEP 8's loop-and-wait collapses to immediate completion per the one-shot lifecycle contract.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
