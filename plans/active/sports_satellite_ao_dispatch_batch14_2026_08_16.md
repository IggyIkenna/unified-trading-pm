---
doc_type: plan
title: Sports satellite AO batch 14 — ag-closeout-audit residual extraction (2026-08-16)
summary: >-
  Fourteenth AO-dispatch batch for sports, drafted by the daily `/ag-closeout-audit sports` run (dispatch agt-6704de,
  slot 24). Phase 0-1 classified 77 sports-tagged AG-primary docs (18 excluded as genuinely multi-AG broad
  coordinators, 2 dual-tag docs resolved by direct read without a Workflow agent, 57 deep-audited via a Workflow): 4
  archivable_now, 19 archivable_after_planned_work, 3 exclude_cross_cutting, and 31 orphaned (26 orphaned_never_touched
  + 5 orphaned_partial_coverage). Of those 31, 7 are formally self-dispatched (assigned_vm: planning, status
  active/open) but their own Progress Logs show real staleness/blockage — reported separately, not orphan-counted, and
  NOT batch candidates (their own dispatch already claims the ground). Of the remaining 24 genuine orphans, the
  Phase-3 conflict-check found 10 source docs' remaining items are both bounded (worker-determinable outcome) and
  conflict-clear today — extracted here. Everything else is operator-gated, time-gated, dependency-gated, needs its
  own scoped design/investigation pass, or is a carried finding from the 2026-08-09 archived audit — see
  `/plans/archive/issues/ag_closeout_audit_sports_parked_2026_08_16.md` for the full deferred ledger with taxonomy
  tags. One item (todo 2) merges two source docs that turned out to name the SAME underlying catalogue-rebuild action
  — drafted as a single todo citing both, not two competing ones.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    ml-service,
    deployment-service,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-14, satellite-docs, ag-closeout-audit]
related:
  [
    /plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md,
    /plans/active/issues/sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    /plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md,
    /plans/active/issues/sports_track_o_attempted_at_keys_extinct_2026_08_14.md,
    /plans/active/sports_taxonomy_p2_consumer_inventory_2026_08_12.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/issues/sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md,
    /plans/active/issues/sports_honest_coverage_gap_closure_2026_08_14.md,
    /plans/active/issues/dp_vm_001_mdps_sports_2026_staleness_guard_and_timeouts_2026_08_16.md,
    /plans/archive/issues/ag_closeout_audit_sports_parked_2026_08_16.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.92
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit sports (2026-08-16, dispatch agt-6704de, slot 24) Phase 3, per
  /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §3's shared conflict-check protocol and
  task_template.md's dispatch-scope eligibility test. Full Phase 1 per-doc classification (57 docs, one agent each via
  Workflow wf_38bce202-00f) journal preserved at the workflow's transcript dir; headline counts + the deferred ledger
  are in the parked-findings issue doc linked above.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# Sports satellite AO batch 14 — ag-closeout-audit residual extraction (2026-08-16)

## Methodology

Ran `/ag-closeout-audit sports` Phase 0 (discover the AG's covering-plan set: 21 covering docs — the consolidated
closeout, batches 5/9/10/12 + finalizes, the native-AO-extract + track-S2-foldin pairs, the taxonomy P2-P4 chain, and
the same-day venue-vocab/league_id-delete pair) then Phase 1 (per-doc classification via a `Workflow` — one agent per
AG-primary candidate doc, 57 docs after excluding 18 genuinely multi-AG broad-coordinator docs and resolving 2
borderline dual-tag docs by direct read from the raw 77-doc `asset_group: [sports]` population). Full verdict counts
and the orphan list are in the run's Phase 2 report (chat/evidence) and the parked-findings issue doc. This batch
covers ONLY the conflict-clear, bounded subset of the 24 genuinely-orphaned (non-self-dispatched) docs' remaining
work — see the parked-findings issue doc for the other 14 items and the 7 self-dispatched-but-stalled docs, and why
each is held back.

## Conflict-check findings that changed what's in this batch

**Todo 2 merges two source docs naming the SAME action.** `sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md`
(a fresh doc documenting why a prior interactive attempt at `build_instrument_catalogue.py --asset-group sports
--since 2019-01-01` was scale-killed) and `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`'s
item 2 (citing the identical catalogue re-roll as Track V of the consolidated closeout) are the same underlying
VM-launch action described from two angles. Drafting two todos here would race the same launcher — folded into one
todo citing both sources.

**`sports_honest_coverage_gap_closure_2026_08_14.md`'s item 3 (odds_api 278-day backfill gap) was NOT extracted**
despite reading as bounded on its own text — a direct check of `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`
and `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (both self-dispatched, `assigned_vm: planning`)
shows these already own the SAME `mtds-backfill-odds-*` VM-fleet campaign, tracked as a live (if currently stalled)
dispatch — drafting a launch todo here would race or duplicate that lineage. Reported as a self-dispatched-but-stalled
finding in the parked-findings doc instead, not batched.

**`sports_league_id_namespace_migration_2026_07_20.md`'s Track H items and STEP 9's human-gated delete were NOT
extracted** — Track H is machine-gated (`depends_on` + `gate_on_depends: true`) on `sports_track_h_denominator_prereqs_2026_07_28.md`,
itself blocked on an unresolved 2026-07-29 operator design fork (Path A vs Path B); STEP 9's delete already has its
live-writer pre-check dispatched via today's `sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16.md`, and
the delete itself stays human-gated regardless. Only that doc's item (c) — a standalone, dependency-free code bug — is
conflict-clear and extracted (todo 7).

**`sports_predictions_live_mode_activation_readiness_2026_07_21.md`'s promote-workflow CLI-chain kickoff (Todo 5,
gate-unblocked 2026-08-11 but unstarted) was NOT extracted** — starting a >=7-day paper-trading sequence for a
strategy archetype is a meaningfully consequential action (a real promote-pipeline entry point, even though paper, not
live-capital), and this pass could not confirm current staffing/monitoring readiness for a week-long unattended run
outside this batch's scope. Flagged in the parked-findings doc as ripe-but-recommend-explicit-operator-kickoff rather
than silently started here.

**`sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md`'s Phase 1-3 items were NOT extracted** — the
doc's own phases are explicitly sequenced (Phase 2 depends on Phase 1's regression-verify actually landing; Phase 3 on
Phase 2's IS-mirror decision) and this pass could not independently re-verify Phase 1's narratively-declared-complete
status without a live deploy-state check outside this batch's scope. Flagged in the parked-findings doc as
possibly-ripe-once-Phase-1-is-independently-reverified, not guessed at here.

## Todos

- [ ] [DATA] P2. **Adjudicate + close footystats matches/predictions fetch-gaps todo #4.** Check the current
      `pending_fetch` count for the affected footystats universe (the doc's own text expects 0, i.e. a likely no-op);
      if 0, decide + record whether the archived `sports_p2_history_reference_and_odds_2015_to_present` item #5 needs
      a flip, then flip this doc's own todo #4 checkbox with the evidence. If `pending_fetch` is nonzero, dispatch the
      footystats backfill VM for the residual instead. Safe/idempotent: a read-only count check first, backfill only if
      genuinely needed. `quality-gates.sh --no-fix` green before any commit if code changes; ship via quickmerge.
      Source: `sports_matches_predictions_fetch_gaps_2026_07_08.md` (repo: instruments-service). Done when: the count
      is measured, the decision is recorded, and todo #4's checkbox is flipped with the evidence cited.
- [ ] [INFRA] P2. **Re-run the sports instrument-catalogue rebuild to completion on a dedicated, rightsized VM.**
      `build_instrument_catalogue.py --asset-group sports --since 2019-01-01` was previously scale-killed running
      interactively (840,035-blob corpus-scale walk). Launch it on its own VM per
      `/codex/05-infrastructure/vm-launcher-runbook.md` (register/reuse a launcher category, do not run this
      corpus-scale walk on the shared planning host), verify row-count/`CATALOGUE_ROLLUP` output on completion,
      capture dmesg/RSS diagnostics if it is killed again. `quality-gates.sh --no-fix` green before any code change;
      ship via quickmerge if the launcher needs a new category. Sources:
      `sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md` +
      `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md` (§ Track V item, same action) (repo:
      instruments-service). Done when: the rebuild completes with a verified row count cited in both source docs, or a
      captured diagnosis if it fails again.
- [ ] [DATA] P1. **Execute the operator-authorized CF-8 `available_at` targeted backfill on prod.** Run the
      already-built + unit-tested `market-tick-data-service/scripts/sports_captured_available_at_targeted_backfill_2026_07_14.py`
      (per-service_name-scoped targeted re-emit) against production on both sports surfaces — instruments-service
      (~652K captured rows) and market-tick-data-service/MDPS (~287K captured rows) — with pre-snapshots and a
      documented safe-rollback path. Operator-authorized 2026-08-07; not yet run as of 2026-08-16. Safe/idempotent:
      snapshot-before-write, targeted re-emit only (no delete). `quality-gates.sh --no-fix` green before commit if any
      code change is needed; ship via quickmerge. Source: `sports_cf8_available_at_backfill_regression_2026_07_13.md`
      (repo: market-tick-data-service). Done when: both surfaces' post-run verification is cited by evidence in the
      source doc and its checkbox is flipped.
- [ ] [DIAG] P2. **Fix `pipeline_e2e_check`-adjacent `odds_features` export gap for 3 named dates (2025-10-23/2025-11-11/2025-11-13) + close the Option-C cleanup.** Investigate + fix why the `odds_features` feature-export parquet is entirely
      missing (404, not honest-absence) for those 3 dates despite `odds_horizon_bucket` now correctly re-derived (one
      date is partially investigated — an env=dev anomaly + a manifest-aware-prune false-resolved bug — fix not yet
      attempted). Separately, locate/re-engage the owner of "the bucket-cutover lane" to formally close out the
      ~90,947 preserved-not-migrated legacy `odds_horizon_bucket` objects, or confirm the `reprocess_sports_odds.py`
      code comment referencing it is stale and remove it. `quality-gates.sh --no-fix` green before commit; ship via
      quickmerge. Source: `sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`
      (repo: features-service, market-data-processing-service). Done when: the 3-date export gap is root-caused +
      fixed (or confirmed honest-absence) with evidence, and the Option-C ownership/staleness question is resolved
      with evidence, both cited in the source doc.
- **[DIAG] P2. CANCELLED — DUPLICATE, found by plan_reconciler 2026-08-18 (retagged 2026-08-22, was a live
  checkbox despite the note below — regen's `_UNCHECKED_RE` is indentation-agnostic and would have dispatched it).**
  ~~Repair Track O `attempted_at` keys against current venue names...~~ This exact task (same source doc, same
  scope) was already extracted the SAME day (2026-08-16) to
  `/plans/active/sports_venue_rename_attempted_at_trace_ao_dispatch_2026_08_16.md` (+ gated finalize), per
  `sports_track_o_attempted_at_keys_extinct_2026_08_14.md`'s own Progress Log ("2026-08-16 — na-eligibility-audit
  follow-up... extracted to `sports_venue_rename_attempted_at_trace_ao_dispatch_2026_08_16.md` for AO dispatch").
  This batch's own "Conflict-check findings" section did not catch this one. The live copy is the other doc.
- [ ] [CODE] P2. **Fix ml-service `_infer_domain` missing FOOTYSTATS venue classification.**
      `cross_asset_training_pipeline.py::_infer_domain`'s venue-classification set is missing FOOTYSTATS, which
      causes FOOTYSTATS-derived `instrument_id`s to misclassify as CEFI. Add FOOTYSTATS to the correct
      classification bucket; add a regression test pinning the correct classification. `quality-gates.sh --no-fix`
      green before commit; ship via quickmerge. Source: `sports_taxonomy_p2_consumer_inventory_2026_08_12.md` §6 /
      cross-cutting finding #5 (repo: ml-service). Done when: `_infer_domain` correctly classifies a FOOTYSTATS
      `instrument_id` as sports (not CEFI), with a regression test, cited in the source doc.
- [ ] [CODE] P3. **Fix the instruments-service per-fixture `league_id` resolution bug.** `sports_reference_fixtures.py:224-229`'s
      `build_league_id()` has a never-addressed resolution defect (see the source doc's own diagnosis). Fix it,
      add/extend a regression test. This item is independent of Track H and STEP 9 in the same source doc — those stay
      gated/human-only, not touched by this todo. `quality-gates.sh --no-fix` green before commit; ship via
      quickmerge. Source: `sports_league_id_namespace_migration_2026_07_20.md` (item, the per-fixture resolution bug
      only) (repo: instruments-service). Done when: `build_league_id()` resolves correctly for the previously-broken
      case, with a regression test, cited in the source doc — the doc's Track H / STEP 9 items stay open and
      untouched.
- [ ] [DIAG] P3. **Live manifest census: is betfair_adapter.py's uppercase "ODDS" write a real or phantom population?** Run a live manifest census to determine whether `betfair_adapter.py:373`'s uppercase `"ODDS"`
      write path is producing a real, accruing row population or is phantom/dead. Write the finding back into the
      source doc. Read-only — do not decide the operator's rewrite-vs-accept-normalization question (leave that
      item open, operator-gated). Source: `sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md` (item 1
      only) (repo: market-tick-data-service). Done when: the census result (real vs. phantom, with row counts) is
      cited in the source doc.
- [ ] [DATA] P2. **Close 3 bounded honest-coverage gap-closure items.** (a) Re-attempt the SFI 7-date retry for the
      112 `attempted_failed` rows (mechanical — dates + CLI already specified in the source doc). (b) Land the
      stranded UAC pinning-test git-stash for `_KNOWN_NON_VENUE_SOURCES` (apply, verify, commit). (c) Relaunch the
      SPOT-preempted weather VM, then run the manifest-rescan-vm script afterward. Do NOT touch item 3 (odds_api
      278-day gap — owned by the self-dispatched `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`/
      `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` VM lineage, see Conflict-check above) or item 5
      (operator decision on the 72,955-cell gap). `quality-gates.sh --no-fix` green before any commit; ship via
      quickmerge. Source: `sports_honest_coverage_gap_closure_2026_08_14.md` (items 1, 2, 4 only) (repo:
      market-tick-data-service, deployment-service). Done when: all 3 items are cited with evidence in the source doc
      and their checkboxes flipped; items 3 and 5 stay open and untouched.
- [ ] [CODE] P3. **Add bounded retry-with-backoff to the SPORTS staleness guard + investigate shared timeout root cause.** (a) Add bounded retry-with-backoff to the MDPS SPORTS staleness guard (`process_handler.py`/
      `dependency_checker.py`), plus a regression test. (b) Investigate whether the 15 subprocess-per-date timeouts
      documented in the source doc share the same manifest-consolidator-contention root cause already diagnosed
      elsewhere in the corpus, or are distinct. Do NOT touch item 1 (waiting on sibling `mdps-sports-{2022..2025}`
      VMs — time/operator-gated). `quality-gates.sh --no-fix` green before commit; ship via quickmerge. Source:
      `dp_vm_001_mdps_sports_2026_staleness_guard_and_timeouts_2026_08_16.md` (items 2, 3 only) (repo:
      market-data-processing-service, unified-trading-library). Done when: the retry-with-backoff + test ship, and the
      timeout root-cause investigation's conclusion is cited in the source doc; item 1 stays open and untouched.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 — the shared conflict-check
  protocol applied to every todo above (and to the items explicitly NOT extracted, see "Conflict-check findings"
  above)
- `/codex/05-infrastructure/vm-launcher-runbook.md` — governs todo 2's VM launch (rightsizing, no corpus-scale walk on
  the shared host)
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — relevant to todo 3's targeted re-emit (not a delete,
  but the same snapshot-first discipline)

## Progress Log

- **2026-08-16 (ag-closeout-audit sports, dispatch agt-6704de, slot 24)**: authored from the 24-doc genuine-orphan
  list (26 orphaned_never_touched + 5 orphaned_partial_coverage, minus 7 self-dispatched-but-stalled docs excluded
  from the orphan count per the tooling's own definition). 10 items extracted across 11 source docs (one todo merges
  2 docs naming the same action); 4 items were held back after a deeper conflict-check read (1 live-VM-lineage
  conflict, 1 machine-gated dependency, 1 consequential-action caution, 1 unverifiable-narrative-claim caution) — see
  "Conflict-check findings" above. The remaining orphaned-doc items and the 7 self-dispatched-but-stalled docs are
  parked in `/plans/archive/issues/ag_closeout_audit_sports_parked_2026_08_16.md` by taxonomy category. **Status left
  `draft`** per this skill's autonomous-mode safety rail — flipping to `active` needs explicit operator approval
  before this batch dispatches.

- **2026-08-22 (operator-directed blocked-backlog re-check)**: operator asked to re-verify the AO dashboard's
  "N blocked" figure against reality and unblock what's genuinely resolvable. Live re-check via
  `/api/backlog/{id}/blockers` (the exact function the dispatcher itself uses) found this draft plan gating 11
  downstream `_finalize` tasks via `gate_on_depends` — the single highest-impact structural blocker in the current
  440-task blocked population. Fresh conflict re-check: all
  6 named related source docs still genuinely open (no staleness), the extraction is still valid; also found todo 5
  (Track O duplicate) was left as a live `- [ ]` checkbox despite its own "do NOT dispatch" note — regen's
  indentation-agnostic unchecked-line parser would have dispatched it once this plan activated. Fixed that line to
  the proper bold CANCELLED form (task_template.md §3) and flipped `status: draft` → `active` under the operator's
  explicit direction this session — this is the "explicit operator approval" this doc's own safety rail asked for.
